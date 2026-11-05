# Validation record

Executed on 5 November 2026 with Python 3.12 and an installed Streamlit runtime.

- `python -m unittest discover -s tests -v`: **7 tests passed**.
- Six core tests cover report validation, public-field projection, secret exclusion from retrieval, baseline search, claim creation and tracking, competing claims, repeat approval rejection, rejection preserving the open report, SQL injection as literal data, invalid tokens and empty results.
- One Streamlit AppTest renders the app, loads fixtures, searches for a bottle, submits ownership evidence and authenticates into staff review. No app exceptions occurred in that tested path.
- `python -m compileall -q app.py core.py matching.py assistant.py`: passed.

Not executed in the authoring environment: transformer model downloads, live FAISS semantic retrieval, Ollama/LangChain generation, Docker build or cross-platform installation. Those paths require their documented dependencies and services. No semantic accuracy, LLM quality, production security or performance claims are made. Dependency ranges are not a tested full-AI lockfile.

## Your full-AI acceptance checklist

1. Install requirements-ai.txt; switch to Semantic; ensure paraphrased bottle query retrieves the bottle.
2. Start Ollama and pull the configured model. Enable LLM; verify clarification questions and explanations reference only visible report IDs.
3. Turn Ollama off; confirm search remains functional and an LLM error is displayed without exposing private information.
4. Submit competing claims; approve one and confirm the other closes and the item disappears from retrieval.
5. Restart app; confirm records persist.
6. Build Docker image and confirm persistence across `docker compose down` / `up` without deleting volumes.
7. Evaluate retrieval using your own labelled examples before adding accuracy metrics to your resume.
