# Historical Dialectics Studio

Native Windows-friendly desktop app (Python + PySide6): historical and modern thinkers debate a topic while **The Historiographer** fact-checks in a side panel.

## Archetype roster

| Archetype | Thinkers |
|-----------|----------|
| **Methodical** | René Descartes, Francis Bacon, John Locke, John Stuart Mill, Naval Ravikant, Warren Buffett |
| **Idealistic** | Socrates, Confucius, Plato, Immanuel Kant |
| **Fundamentalist** | Karl Marx, Thomas Hobbes, Thomas Aquinas, Adam Smith |

## Run (Windows PowerShell)

```powershell
git clone https://github.com/StereoP2/historical-dialectics-studio.git
cd historical-dialectics-studio
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m dialectics_studio
```

- No API key → demo transcript still runs (Marx vs Descartes).
- Live multi-agent debates → paste an OpenAI-compatible key in the UI (or set `OPENAI_API_KEY`).

## Sources & custom topics

- **Your topic:** type anything in the topic field (presets optional).
- **Free sources:** debaters cite their own historically plausible works/evidence.
- **Limited sources:** paste links and/or excerpts; debaters may only argue from those materials.

## Layout

Left: pick 2–3 debaters + topic · Center: Arena · Right: Historiographer + citation tips

Prompts live in `dialectics_studio/prompts/` and `prompts/`.
