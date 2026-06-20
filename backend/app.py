import os
from collections import defaultdict, deque
from datetime import date, datetime
from flask import Flask, jsonify, make_response, request, send_file, send_from_directory
from flask_cors import CORS
from io import BytesIO
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

try:
    from .nlp_service import analyze
    from .repository import ArticleRepository
    from .pdf_service import create_pdf
    from .pdf_ingestion import ingest_newspaper_pdf
    from .news_service import fetch_daily_news
    from .scheduler import start_daily_scheduler
except ImportError:
    from nlp_service import analyze
    from repository import ArticleRepository
    from pdf_service import create_pdf
    from pdf_ingestion import ingest_newspaper_pdf
    from news_service import fetch_daily_news
    from scheduler import start_daily_scheduler


def _bank_text(questions):
    lines = ["UPSCBrief Question Bank", f"Generated: {datetime.now().isoformat(timespec='minutes')}", ""]
    for idx, item in enumerate(questions, start=1):
        lines.append(f"{idx}. [{item.get('kind')}] {item.get('articleTitle')}")
        lines.append(item.get("question", ""))
        if item.get("options"):
            lines.extend(f"   - {option}" for option in item["options"])
        if item.get("answer"):
            lines.append(f"Answer: {item['answer']}")
        if item.get("explanation"):
            lines.append(f"Explanation: {item['explanation']}")
        if item.get("modelAnswerPoints"):
            lines.append("Model answer points: " + "; ".join(item["modelAnswerPoints"]))
        lines.append("")
    return "\n".join(lines)


def _simple_pdf(title, body):
    lines = [title, ""] + body.splitlines()
    escaped = [line[:105].replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)") for line in lines[:28]]
    stream = "BT /F1 13 Tf 54 760 Td " + " Tj 0 -22 Td ".join(f"({line})" for line in escaped) + " Tj ET"
    objects = [
        "1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj",
        "2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj",
        "3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Resources<</Font<</F1 5 0 R>>>>/Contents 4 0 R>>endobj",
        f"4 0 obj<</Length {len(stream)}>>stream\n{stream}\nendstream endobj",
        "5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj",
    ]
    pdf = "%PDF-1.4\n"
    offsets = [0]
    for obj in objects:
        offsets.append(len(pdf.encode()))
        pdf += obj + "\n"
    xref = len(pdf.encode())
    pdf += f"xref\n0 6\n0000000000 65535 f \n" + "".join(f"{o:010d} 00000 n \n" for o in offsets[1:])
    pdf += f"trailer<</Size 6/Root 1 0 R>>\nstartxref\n{xref}\n%%EOF"
    return pdf.encode("latin-1", errors="replace")


def create_app():
    dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dist"))
    app = Flask(__name__, static_folder=dist, static_url_path="")
    app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_PDF_MB", 25)) * 1024 * 1024
    CORS(app)
    repo = ArticleRepository()
    app.extensions["daily_news_scheduler"] = start_daily_scheduler(repo)
    app.extensions["users"] = {}
    request_times = defaultdict(deque)

    @app.before_request
    def rate_limit():
        if request.path.startswith("/api/"):
            now = datetime.now().timestamp()
            bucket = request_times[request.remote_addr or "local"]
            while bucket and now - bucket[0] > 60:
                bucket.popleft()
            if len(bucket) >= int(os.getenv("RATE_LIMIT_PER_MINUTE", 240)):
                return jsonify({"error": "Too many requests. Please try again shortly."}), 429
            bucket.append(now)

    @app.after_request
    def security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; script-src 'self'"
        return response

    @app.get("/api/health")
    def health():
        return jsonify({
            "status": "healthy",
            "storage": "mongodb" if repo.collection is not None else "json",
            "api": "ok",
            "scheduler": bool(app.extensions.get("daily_news_scheduler")),
            "time": datetime.now().isoformat(timespec="seconds"),
        })

    @app.post("/api/auth/register")
    def register():
        body = request.get_json(silent=True) or {}
        email = str(body.get("email", "")).strip().lower()
        password = str(body.get("password", ""))
        if not email or len(password) < 8:
            return jsonify({"error": "Email and an 8 character password are required"}), 400
        users = app.extensions["users"]
        if email in users:
            return jsonify({"error": "User already exists"}), 409
        users[email] = {"email": email, "passwordHash": generate_password_hash(password)}
        return jsonify({"email": email, "token": f"dev-token-{email}"}), 201

    @app.post("/api/auth/login")
    def login():
        body = request.get_json(silent=True) or {}
        email = str(body.get("email", "")).strip().lower()
        user = app.extensions["users"].get(email)
        if not user or not check_password_hash(user["passwordHash"], str(body.get("password", ""))):
            return jsonify({"error": "Invalid credentials"}), 401
        return jsonify({"email": email, "token": f"dev-token-{email}"})

    @app.get("/api/profile")
    def get_profile():
        return jsonify(repo.get_profile())

    @app.put("/api/profile")
    def save_profile():
        body = request.get_json(silent=True) or {}
        if body.get("email") and "@" not in str(body["email"]):
            return jsonify({"error": "Enter a valid email address"}), 400
        return jsonify(repo.save_profile(body))

    @app.get("/api/articles")
    def articles():
        items = repo.all()
        category = request.args.get("category")
        query = request.args.get("q", "").lower()
        day = request.args.get("date")
        if category and category != "All":
            items = [a for a in items if a["category"] == category]
        if query:
            items = [a for a in items if query in (a["title"] + " " + a["summary"] + " " + " ".join(a["keywords"])).lower()]
        if day:
            items = [a for a in items if a["date"] == day]
        return jsonify(items)

    @app.get("/api/articles/<article_id>")
    def article(article_id):
        item = repo.get(article_id)
        return (jsonify(item), 200) if item else (jsonify({"error": "Article not found"}), 404)

    @app.post("/api/articles")
    def create_article():
        body = request.get_json(silent=True) or {}
        required = ["title", "content", "source"]
        if any(not str(body.get(k, "")).strip() for k in required):
            return jsonify({"error": "Title, source and content are required"}), 400
        generated = analyze(body["title"], body["content"])
        item = repo.create({
            "title": body["title"].strip(),
            "source": body["source"].strip(),
            "date": body.get("date") or date.today().isoformat(),
            "content": body["content"].strip(),
            "sourceType": "manual",
            **generated,
        })
        return jsonify(item), 201

    @app.post("/api/analyze")
    def preview():
        body = request.get_json(silent=True) or {}
        return jsonify(analyze(body.get("title", "Current Affairs"), body.get("content", "")))

    @app.post("/api/ingestion/pdf")
    def ingest_pdf():
        uploaded = request.files.get("newspaper")
        if not uploaded or not uploaded.filename:
            return jsonify({"error": "Choose a newspaper PDF"}), 400
        filename = secure_filename(uploaded.filename)
        data = uploaded.read()
        if not filename.lower().endswith(".pdf") or not data.startswith(b"%PDF"):
            return jsonify({"error": "Only valid PDF files are accepted"}), 400
        source = request.form.get("source", "Uploaded Newspaper").strip() or "Uploaded Newspaper"
        publication_date = request.form.get("date", date.today().isoformat())
        try:
            date.fromisoformat(publication_date)
        except ValueError:
            return jsonify({"error": "Date must use YYYY-MM-DD format"}), 400
        try:
            return jsonify(ingest_newspaper_pdf(data, filename, source, publication_date, repo)), 201
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 422
        except Exception as exc:
            return jsonify({"error": f"PDF processing failed: {exc}"}), 500

    @app.post("/api/ingestion/news")
    def sync_news():
        body = request.get_json(silent=True) or {}
        try:
            target = date.fromisoformat(body["date"]) if body.get("date") else date.today()
            return jsonify(fetch_daily_news(repo, target))
        except ValueError:
            return jsonify({"error": "Date must use YYYY-MM-DD format"}), 400

    @app.get("/api/ingestion/status")
    def ingestion_status():
        status = repo.sync_status()
        return jsonify({
            "provider": os.getenv("NEWS_API_PROVIDER", "NewsAPI compatible provider"),
            "apiConfigured": bool(os.getenv("NEWS_API_KEY")),
            "sampleMode": not bool(os.getenv("NEWS_API_KEY")),
            "dailySyncEnabled": os.getenv("ENABLE_DAILY_SYNC", "false").lower() == "true",
            "schedule": f"{int(os.getenv('DAILY_SYNC_HOUR', 6)):02d}:{int(os.getenv('DAILY_SYNC_MINUTE', 0)):02d} IST",
            "pdfLimitMb": int(os.getenv("MAX_PDF_MB", 25)),
            **status,
        })

    @app.errorhandler(413)
    def too_large(_):
        return jsonify({"error": f"PDF exceeds the {os.getenv('MAX_PDF_MB', '25')} MB limit"}), 413

    @app.get("/api/articles/<article_id>/pdf")
    def pdf(article_id):
        item = repo.get(article_id)
        if not item:
            return jsonify({"error": "Article not found"}), 404
        return send_file(BytesIO(create_pdf(item)), mimetype="application/pdf", as_attachment=True, download_name="current-affairs-summary.pdf")

    @app.get("/api/question-bank")
    def question_bank():
        kind = request.args.get("kind")
        items = repo.question_bank()
        if kind:
            items = [item for item in items if item.get("kind") == kind]
        return jsonify(items)

    @app.get("/api/question-bank/export")
    def export_question_bank():
        fmt = request.args.get("format", "pdf").lower()
        body = _bank_text(repo.question_bank())
        if fmt == "word":
            response = make_response(body)
            response.headers["Content-Type"] = "application/msword"
            response.headers["Content-Disposition"] = "attachment; filename=question-bank.doc"
            return response
        if fmt == "print":
            response = make_response(body)
            response.headers["Content-Type"] = "text/plain; charset=utf-8"
            return response
        return send_file(BytesIO(_simple_pdf("UPSCBrief Question Bank", body)), mimetype="application/pdf", as_attachment=True, download_name="question-bank.pdf")

    @app.get("/api/stats")
    def stats():
        items = repo.all()
        today = date.today().isoformat()
        categories = {}
        for item in items:
            categories[item["category"]] = categories.get(item["category"], 0) + 1
        return jsonify({
            "articles": len(items),
            "todayArticles": len([a for a in items if a.get("date") == today]),
            "questions": sum(len(a.get("mcqs", [])) + len(a.get("practiceQuestions", [])) + len(a.get("pyqs", [])) for a in items),
            "sources": len(set(a["source"] for a in items)),
            "categories": categories,
            "pdfUploads": repo.pdf_upload_count(),
            "activeUsers": 1,
            "sync": repo.sync_status(),
            "apiHealth": "healthy",
        })

    @app.get("/api/admin/metrics")
    def admin_metrics():
        return stats()

    @app.get("/")
    @app.get("/<path:path>")
    def frontend(path=""):
        if os.path.isdir(dist):
            target = os.path.join(dist, path)
            return send_from_directory(dist, path) if path and os.path.isfile(target) else send_from_directory(dist, "index.html")
        return jsonify({"name": "UPSCBrief API", "message": "Build the React client with npm run build."})

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=int(os.getenv("PORT", 5000)), debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")
