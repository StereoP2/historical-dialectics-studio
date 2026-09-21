from __future__ import annotations

import asyncio

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from dialectics_studio.engine.debate import DebateEngine, DebateEvent
from dialectics_studio.engine.personas import PERSONAS, TOPICS, get_persona


class DebateWorker(QThread):
    event = Signal(object)
    finished_ok = Signal()

    def __init__(
        self,
        topic: str,
        persona_ids: list[str],
        rounds: int,
        api_key: str,
        force_demo: bool = False,
        source_mode: str = "Free",
        supplied_sources: str = "",
    ):
        super().__init__()
        self.topic = topic
        self.persona_ids = persona_ids
        self.rounds = rounds
        self.api_key = api_key
        self.force_demo = force_demo
        self.source_mode = source_mode
        self.supplied_sources = supplied_sources

    def run(self):
        debaters = [get_persona(pid) for pid in self.persona_ids]
        engine = DebateEngine(api_key=self.api_key or None)

        async def _go():
            async def on_event(ev: DebateEvent):
                self.event.emit(ev)

            await engine.run(
                self.topic,
                debaters,
                self.rounds,
                on_event,
                force_demo=self.force_demo,
                source_mode=self.source_mode,
                supplied_sources=self.supplied_sources,
            )

        asyncio.run(_go())
        self.finished_ok.emit()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Historical Dialectics Studio")
        self.resize(1320, 860)
        self._worker: DebateWorker | None = None
        self._build()
        self._apply_dark()

    def _build(self):
        root = QWidget()
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        left = QWidget()
        left_l = QVBoxLayout(left)
        left_l.addWidget(QLabel("<b>Debaters</b> (pick 2–3)"))
        self.persona_list = QListWidget()
        self.persona_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        for p in PERSONAS:
            item = QListWidgetItem(f"{p.name}  [{p.archetype}]")
            item.setData(Qt.ItemDataRole.UserRole, p.id)
            item.setToolTip(p.blurb)
            self.persona_list.addItem(item)
        left_l.addWidget(self.persona_list, stretch=2)

        form = QFormLayout()
        self.topic_edit = QLineEdit()
        self.topic_edit.setPlaceholderText("Type any topic…")
        self.topic_edit.setText(TOPICS[0] if TOPICS else "")
        form.addRow("Your topic", self.topic_edit)

        self.topic_presets = QComboBox()
        self.topic_presets.addItem("— presets —")
        self.topic_presets.addItems(TOPICS)
        self.topic_presets.currentTextChanged.connect(self._preset_topic)
        form.addRow("Or pick preset", self.topic_presets)

        self.rounds_spin = QSpinBox()
        self.rounds_spin.setRange(1, 6)
        self.rounds_spin.setValue(2)
        form.addRow("Rounds", self.rounds_spin)
        left_l.addLayout(form)

        src_box = QGroupBox("Sources")
        src_l = QVBoxLayout(src_box)
        mode_row = QHBoxLayout()
        self.mode_free = QRadioButton("Free sources")
        self.mode_limited = QRadioButton("Limited sources")
        self.mode_free.setChecked(True)
        self.mode_free.setToolTip(
            "Debaters may cite their own works and historically plausible evidence."
        )
        self.mode_limited.setToolTip(
            "Debaters may ONLY use the links/excerpts you paste below."
        )
        self._mode_group = QButtonGroup(self)
        self._mode_group.addButton(self.mode_free)
        self._mode_group.addButton(self.mode_limited)
        mode_row.addWidget(self.mode_free)
        mode_row.addWidget(self.mode_limited)
        src_l.addLayout(mode_row)
        src_l.addWidget(
            QLabel("Paste links and/or excerpts (required for Limited mode):")
        )
        self.sources_edit = QTextEdit()
        self.sources_edit.setPlaceholderText(
            "Examples:\n"
            "https://www.marxists.org/archive/marx/works/1867-c1/\n"
            "---\n"
            "Excerpt: \"The wealth of those societies…\" (Capital, Vol. I)\n"
        )
        self.sources_edit.setMinimumHeight(120)
        src_l.addWidget(self.sources_edit)
        left_l.addWidget(src_box, stretch=2)

        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setPlaceholderText("Optional OPENAI_API_KEY for live debates")
        left_l.addWidget(QLabel("API key"))
        left_l.addWidget(self.api_key_edit)
        self.demo_check = QCheckBox("Force demo transcript")
        left_l.addWidget(self.demo_check)

        self.start_btn = QPushButton("Start debate")
        self.start_btn.clicked.connect(self.start_debate)
        left_l.addWidget(self.start_btn)
        splitter.addWidget(left)

        center = QWidget()
        c_l = QVBoxLayout(center)
        c_l.addWidget(QLabel("<b>The Arena</b>"))
        self.transcript = QTextEdit()
        self.transcript.setReadOnly(True)
        c_l.addWidget(self.transcript)
        splitter.addWidget(center)

        right = QWidget()
        r_l = QVBoxLayout(right)
        r_l.addWidget(QLabel("<b>The Historiographer</b>"))
        self.fact_feed = QTextEdit()
        self.fact_feed.setReadOnly(True)
        r_l.addWidget(self.fact_feed)
        cite_box = QGroupBox("Your supplied materials (mirror)")
        cite_l = QVBoxLayout(cite_box)
        self.cite_view = QTextEdit()
        self.cite_view.setReadOnly(True)
        self.cite_view.setPlaceholderText("Sources you paste will show here when a debate starts.")
        cite_l.addWidget(self.cite_view)
        r_l.addWidget(cite_box)
        splitter.addWidget(right)
        splitter.setSizes([340, 600, 360])

    def _preset_topic(self, text: str):
        if text and not text.startswith("—"):
            self.topic_edit.setText(text)

    def _apply_dark(self):
        self.setStyleSheet(
            """
            QWidget { background: #1a1d23; color: #e8eaed; font-size: 13px; }
            QTextEdit, QListWidget, QLineEdit, QComboBox, QSpinBox {
                background: #12141a; border: 1px solid #2c313c; border-radius: 6px; padding: 6px;
            }
            QPushButton {
                background: #3d7ea6; color: white; border: none; border-radius: 6px;
                padding: 10px; font-weight: 600;
            }
            QPushButton:disabled { background: #333842; color: #888; }
            QGroupBox { border: 1px solid #2c313c; margin-top: 8px; padding-top: 12px; }
            QRadioButton { spacing: 6px; }
            """
        )

    def selected_ids(self) -> list[str]:
        return [i.data(Qt.ItemDataRole.UserRole) for i in self.persona_list.selectedItems()]

    def start_debate(self):
        ids = self.selected_ids()
        if not (2 <= len(ids) <= 3):
            QMessageBox.warning(self, "Pick debaters", "Select 2 or 3 figures.")
            return
        topic = self.topic_edit.text().strip()
        if not topic:
            QMessageBox.warning(self, "Topic needed", "Type a topic or pick a preset.")
            return
        mode = "Limited" if self.mode_limited.isChecked() else "Free"
        sources = self.sources_edit.toPlainText().strip()
        if mode == "Limited" and not sources:
            QMessageBox.warning(
                self,
                "Sources needed",
                "Limited mode requires at least one link or excerpt.",
            )
            return
        if self._worker and self._worker.isRunning():
            return
        self.transcript.clear()
        self.fact_feed.clear()
        self.cite_view.setPlainText(sources or "(Free mode — debaters find their own sources)")
        self.start_btn.setEnabled(False)
        self._append_transcript("System", f"Starting · {mode} sources · {topic}", "#888888")
        self._worker = DebateWorker(
            topic,
            ids,
            self.rounds_spin.value(),
            self.api_key_edit.text().strip(),
            force_demo=self.demo_check.isChecked(),
            source_mode=mode,
            supplied_sources=sources,
        )
        self._worker.event.connect(self.on_event)
        self._worker.finished_ok.connect(self.on_done)
        self._worker.start()

    def on_event(self, ev: DebateEvent):
        colors = {p.id: p.color for p in PERSONAS}
        colors.update({"historiographer": "#c9a227", "system": "#888888"})
        color = colors.get(ev.speaker_id, "#e8eaed")
        if ev.kind == "factcheck":
            self.fact_feed.append(
                f"<p style='color:{color}'><b>{_esc(ev.speaker_name)}</b><br>{_esc(ev.text)}</p>"
            )
        elif ev.kind == "invalidate":
            self.fact_feed.append(
                f"<p style='color:#ff6b6b;border:1px solid #ff6b6b;padding:8px'>"
                f"<b>⛔ INVALIDATED</b><br>{_esc(ev.text)}</p>"
            )
            self._append_transcript("Historiographer", f"⛔ {ev.text}", "#ff6b6b")
        elif ev.kind == "error":
            self._append_transcript(ev.speaker_name, ev.text, "#e06666")
        else:
            self._append_transcript(ev.speaker_name, ev.text, color)

    def _append_transcript(self, name: str, text: str, color: str):
        self.transcript.append(
            f"<p style='margin:10px 0'><span style='color:{color};font-weight:700'>{_esc(name)}</span>"
            f"<br><span style='background:#22262e;padding:8px;border-radius:8px;display:inline-block'>"
            f"{_esc(text)}</span></p>"
        )

    def on_done(self):
        self.start_btn.setEnabled(True)


def _esc(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br>")
    )
