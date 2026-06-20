# AI Current Affairs Summarizer for Civil Services Aspirants

Production-oriented full-stack rebuild of UPSCBrief: a React + Flask application that turns daily current affairs and uploaded PDFs into syllabus-linked summaries, Prelims MCQs, Mains prompts, PYQ links, and an exportable question bank.

## Rebuilt Features

- Editable aspirant profile with dynamic name across dashboard, sidebar, and local storage
- Default greeting uses "Aspirant" for new users
- Indian tricolor UPSCBrief logo replacing the brain mark
- Daily news sync with source-level retries, duplicate removal, status telemetry, and sample fallback mode
- PDF upload up to 25 MB with pypdf, pdfplumber, and PyMuPDF extraction fallbacks
- Subject classification across Polity, Governance, Economy, Environment, IR, Science and Technology, Security, Social Issues, Agriculture, Ethics, History, and Geography
- Article analysis fields: 100-word summary, detailed summary, facts, keywords, terms, schemes, constitutional articles, committees, reports, and organizations
- Five Prelims MCQs per article and three Mains questions with directive, paper, word limit, and model answer points
- PYQ mapping and exportable question bank
- Admin dashboard metrics for articles, today's articles, questions, PDF uploads, sync status, and API health
- MongoDB support with JSON fallback for local use
- Basic auth endpoints, password hashing, rate limiting, input validation, and security headers

## Project Structure

```text
src/
  App.jsx
  api.js
  styles.css
backend/
  app.py
  repository.py
  nlp_service.py
  news_service.py
  pdf_ingestion.py
  pdf_service.py
  scheduler.py
  database_schema.md
  data/
  tests/
scripts/
  run-backend.js
```

## Local Setup

```bash
npm install
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
npm run dev
```

Open `http://127.0.0.1:5173`. The Flask API runs on `http://127.0.0.1:5000`.

## Environment

Copy `.env.example` to `.env` and set values as needed:

- `MONGO_URI`, `MONGO_DB` for MongoDB
- `NEWS_API_KEY`, `NEWS_API_URL`, `NEWS_SOURCES` for live news collection
- `ENABLE_DAILY_SYNC`, `DAILY_SYNC_HOUR`, `DAILY_SYNC_MINUTE` for automatic sync
- `MAX_PDF_MB` for upload size
- `RATE_LIMIT_PER_MINUTE`, `SECRET_KEY` for deployment hardening

## Verify

```bash
npm test
npm run build
```

The production build is emitted to `dist/`. Flask serves `dist/` when present.

## Database

See `backend/database_schema.md` for MongoDB collections and recommended indexes.
