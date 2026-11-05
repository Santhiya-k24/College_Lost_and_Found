# Campus Return

A college lost-and-found assistant built to be understandable, runnable and extendable. Students submit lost/found reports, search found items and submit ownership evidence. Staff compare private details and record the handover. No automatic ownership decisions.

## Start here (Python 3.11 recommended)

Extract the ZIP, open a terminal inside `campus-return`, then:

```bash
python -m venv .venv
```

Activate the environment:

- Windows PowerShell: `.venv\Scripts\Activate.ps1`
- Windows Command Prompt: `.venv\Scripts\activate.bat`
- macOS/Linux: `source .venv/bin/activate`

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open http://localhost:8501. Select **Load fictional sample reports**, then search **blue water bottle near library**. Demo mode needs no API key or model download. It is lexical matching with a small explicit synonym dictionary, NOT an LLM or neural semantic engine.

### Enable staff review

Set a password of at least 12 characters before starting Streamlit:

```bash
# macOS/Linux
export STAFF_PASSWORD='choose-your-own-long-password'
# PowerShell (use this instead on Windows)
$env:STAFF_PASSWORD='choose-your-own-long-password'
```

Do not literally use the example password. Restart the app after changing environment variables. Local Python does not automatically read `.env`.

## Real semantic matching

```bash
python -m pip install -r requirements-ai.txt
```

Select **Semantic** in the sidebar. First use downloads `sentence-transformers/all-MiniLM-L6-v2` from Hugging Face; internet access and disk space are required. CPU inference is supported. Each query embeds public reports, normalizes vectors and builds a FAISS inner-product index. With normalized vectors the inner product equals cosine similarity. The small-campus implementation deliberately rebuilds the index so returned items disappear immediately. For large deployments maintain an incremental persistent index instead.

## Local LLM with LangChain

Install Ollama from https://ollama.com and run:

```bash
ollama pull llama3.2:3b
ollama serve
```

If the service is already running, do not start a second instance. Install AI requirements above, enable **local LLM**, then try **Help me add missing details** and **Explain these possible matches**. Default endpoint: http://localhost:11434. Model requires a multi-GB download and sufficient local memory. A slow laptop may take time; the matching workflow works without it. Set `OLLAMA_MODEL` or `OLLAMA_BASE_URL` before starting the app to change configuration.

LLM inputs contain public report text only. Hosted/custom Ollama endpoints receive that text. Do not put secrets in public descriptions. The explanation button implements retrieval-augmented generation: retrieve public records, then generate an explanation grounded in them. This is a controlled LangChain workflow, not a CrewAI multi-agent system. CrewAI is intentionally not included.

## Docker

Copy `.env.example` to `.env`, set your own staff password, then:

```bash
docker compose up --build
```

For full AI support set `INSTALL_AI=true` in `.env` before building. AI image builds can be large. Ollama runs on the host; the container uses `host.docker.internal`. On Linux Ollama must accept connections from the Docker bridge (configure Ollama carefully and firewall it); if unavailable, use native Python or leave LLM disabled. Docker uses named volumes for records and model cache. `docker compose down` retains data; adding `-v` deletes those volumes. Docker functionality requires Docker installed and running.

## Demo script

1. Load fictional samples. Open Find a match and search `blue water bottle near library`.
2. Expand the bottle result. Submit a claim with a name, fictional contact and `star sticker beneath base`.
3. Copy the private token and check it on Track a claim: Pending.
4. Open Staff desk with your configured password. Compare the evidence with the private recorded detail.
5. Add a message, choose Approve, confirm handover, and record decision.
6. Track again: Approved. Search again: returned item is absent.
7. Try an unrelated query. No result is preferable to inventing a match.

Sample dates are fixed fixtures (2026-11-05). Only a completely empty database is seeded. The staff reference details for the other sample items are `initials inside lid`, `tiny green turtle charm`, and `red lining in front pocket`.

## Tests

```bash
python -m unittest discover -s tests -v
```

Run `python -m unittest discover -s tests -p test_core.py -v` for core-only tests requiring just the Python standard library. The full suite also needs Streamlit. Core tests they cover public/private separation, matching, input validation, SQL injection resistance, rejection, competing claims, invalid tokens and return status. See VALIDATION.md for exactly what was run by the author.

## Files

- `app.py`: Streamlit UI and staff authentication gate
- `core.py`: SQLite schema and report/claim transitions
- `matching.py`: demo scoring and neural FAISS search
- `assistant.py`: optional LangChain/Ollama extraction and grounded explanations
- `tests/test_core.py`: repeatable workflow tests
- `tests/test_ui.py`: Streamlit UI workflow test
- `STUDY_GUIDE.md`: seven-day plan and interview preparation

## Design and limitations

Private identifying details, claimant evidence and contacts are stored in local SQLite and shown only behind the staff password gate. Tracking tokens are stored as SHA-256 hashes. SQL uses parameter binding. Secrets never enter the retrieval text. Similarity scores are not calibrated probabilities. LLM outputs can be wrong; prompt instructions are not a security boundary, so no LLM output can approve claims or access secrets.

This is a complete educational local application, not a production campus service. It has one staff password, no institutional authentication, no rate limiting, no email verification or notifications, no uploaded photos, no encryption at rest and no self-service report editing. The prototype accepts public reports without login. Anyone with database-file access can read private fields; use fictional data for demonstrations. Do not expose it on the public internet without proper authentication, HTTPS, access controls, retention policies, abuse prevention and backups. Staff approval is final in this prototype; real systems need corrections and audit logs. Broad dependency bounds are compatibility ranges, not a verified lockfile; freeze your installed versions after a successful full-AI setup.

## Technical references

- https://sbert.net/docs/package_reference/sentence_transformer/model.html
- https://reference.langchain.com/python/langchain-ollama/chat_models/ChatOllama/with_structured_output
- https://docs.streamlit.io/
- https://github.com/facebookresearch/faiss/wiki

## Resume use

Until you have run and understood the implementation, keep it marked In Development. After testing, describe only features you actually ran. Do not claim CrewAI, autonomous agents, production deployment or measured accuracy from this project.
