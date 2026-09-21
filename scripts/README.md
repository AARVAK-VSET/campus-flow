# Manual smoke-check scripts

These scripts call the **real** AI and text-to-speech services (or a running
server), so they need an internet connection, an `OPENROUTER_API_KEY` in
`backend/.env`, and - for `check_voice_endpoint.py` - the backend running on
port 8000. They are **not** part of the automated test suite; `pytest` never
runs them. Run them from the project root, for example:

```bash
python scripts/check_tts.py
python scripts/check_form_filler.py
python scripts/check_llm.py
python scripts/check_voice_endpoint.py   # needs the backend running
```

The automated tests for the same code live in `tests/` and use fakes instead.
