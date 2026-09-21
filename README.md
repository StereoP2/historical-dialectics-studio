# Historical Dialectics Studio

Thinkers debate a topic while **The Historiographer** fact-checks. Use the **desktop** app or the easier **web** UI.

## Easiest: web (Join & discuss)

Double-click **`Start Web.bat`** (or run the commands below). Browser opens at http://127.0.0.1:7860

- **Join & discuss** — you argue in the Arena; thinkers reply to you
- **Fishbowl** — watch-only auto debate
- Type your own topic; Free or Limited sources

```powershell
cd $HOME\historical-dialectics-studio
git pull
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m dialectics_studio.web
```

Then open http://127.0.0.1:7860

## Desktop (PySide6)

Double-click **`Start Dialectics Studio.bat`**, or:

```powershell
.\.venv\Scripts\python.exe -m dialectics_studio
```

## Archetype roster

| Archetype | Thinkers |
|-----------|----------|
| **Methodical** | René Descartes, Francis Bacon, John Locke, John Stuart Mill, Naval Ravikant, Warren Buffett |
| **Idealistic** | Socrates, Confucius, Plato, Immanuel Kant |
| **Fundamentalist** | Karl Marx, Thomas Hobbes, Thomas Aquinas, Adam Smith |

- No API key → demo still runs
- Live debates → paste an OpenAI-compatible key in the UI (or set `OPENAI_API_KEY`)
