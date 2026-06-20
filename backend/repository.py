import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

DEFAULT_PROFILE = {
    "userId": "default",
    "fullName": "",
    "email": "",
    "targetYear": "2027",
    "optionalSubject": "",
    "state": "",
    "examType": "Civil Services Examination",
}

DEFAULT_SYNC = {
    "status": "idle",
    "lastSyncTime": None,
    "nextScheduledSync": None,
    "articlesFetched": 0,
    "createdCount": 0,
    "skippedCount": 0,
    "sourceResults": [],
    "errors": [],
}


def normalize_title(value):
    cleaned = re.sub(r"[^a-z0-9 ]+", " ", str(value).lower())
    cleaned = re.sub(r"\b(the|a|an|and|or|to|of|in|on|for|with|by|from|new|india|indian)\b", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


class ArticleRepository:
    def __init__(self):
        self.data_dir = Path(__file__).parent / "data"
        self.file = self.data_dir / "articles.json"
        self.seed = self.data_dir / "sample_articles.json"
        self.profiles_file = self.data_dir / "profiles.json"
        self.sync_file = self.data_dir / "sync_status.json"
        self.pdf_uploads_file = self.data_dir / "pdf_uploads.json"
        self.collection = None
        self.profile_collection = None
        self.pdf_collection = None
        uri = os.getenv("MONGO_URI")
        if uri:
            try:
                from pymongo import ASCENDING, MongoClient
                client = MongoClient(uri, serverSelectionTimeoutMS=900)
                client.admin.command("ping")
                db = client[os.getenv("MONGO_DB", "current_affairs")]
                self.collection = db["news_articles"]
                self.profile_collection = db["profiles"]
                self.pdf_collection = db["pdf_uploads"]
                db["question_bank"].create_index([("articleId", ASCENDING)])
                self.collection.create_index([("date", ASCENDING), ("category", ASCENDING)])
                self.collection.create_index([("title", ASCENDING), ("date", ASCENDING)], unique=False)
                self.profile_collection.create_index([("userId", ASCENDING)], unique=True)
            except Exception:
                self.collection = None
                self.profile_collection = None
                self.pdf_collection = None
        self.data_dir.mkdir(parents=True, exist_ok=True)
        if self.collection is None and not self.file.exists():
            self.file.write_text(self.seed.read_text(encoding="utf-8"), encoding="utf-8")
        if self.collection is None and not self.profiles_file.exists():
            self._write_json(self.profiles_file, [DEFAULT_PROFILE])
        if self.collection is None and not self.sync_file.exists():
            self._write_json(self.sync_file, DEFAULT_SYNC)
        if self.collection is None and not self.pdf_uploads_file.exists():
            self._write_json(self.pdf_uploads_file, [])
        self.update_next_sync()

    def _read_json(self, path, fallback):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return fallback

    def _write_json(self, path, value):
        path.write_text(json.dumps(value, indent=2), encoding="utf-8")

    def _normalize_article(self, item):
        if not item:
            return None
        item = dict(item)
        if "_id" in item:
            item["_id"] = str(item["_id"])
        item.setdefault("mcqs", [])
        item.setdefault("practiceQuestions", [])
        item.setdefault("shortAnswerQuestions", [])
        item.setdefault("mainsQuestions", [])
        item.setdefault("pyqs", [])
        item.setdefault("keyFacts", [])
        item.setdefault("importantTerms", item.get("keywords", [])[:6])
        item.setdefault("shortSummary", item.get("summary", ""))
        item.setdefault("detailedSummary", item.get("summary", ""))
        return item

    def all(self):
        if self.collection is not None:
            return [self._normalize_article(x) for x in self.collection.find().sort("date", -1)]
        return [self._normalize_article(x) for x in self._read_json(self.file, [])]

    def get(self, article_id):
        if self.collection is not None:
            from bson import ObjectId
            try:
                item = self.collection.find_one({"_id": ObjectId(article_id)})
            except Exception:
                item = None
            return self._normalize_article(item)
        return next((a for a in self.all() if a["_id"] == article_id), None)

    def create(self, article):
        if self.collection is not None:
            result = self.collection.insert_one(article)
            return self._normalize_article({**article, "_id": result.inserted_id})
        items = self._read_json(self.file, [])
        record = {"_id": uuid4().hex[:12], **article}
        items.insert(0, record)
        self._write_json(self.file, items)
        return self._normalize_article(record)

    def exists(self, title, date=None, original_url=None):
        if self.collection is not None:
            query = {"originalUrl": original_url} if original_url else {"title": title, **({"date": date} if date else {})}
            if self.collection.count_documents(query, limit=1) > 0:
                return True
            normalized = normalize_title(title)
            for item in self.collection.find({"date": date} if date else {}, {"title": 1}).limit(500):
                if normalize_title(item.get("title", "")) == normalized:
                    return True
            return False
        normalized = normalize_title(title)
        return any(
            (original_url and a.get("originalUrl") == original_url) or
            ((not date or a.get("date") == date) and normalize_title(a.get("title", "")) == normalized)
            for a in self.all()
        )

    def create_many(self, articles):
        return [self.create(article) for article in articles]

    def get_profile(self, user_id="default"):
        if self.profile_collection is not None:
            item = self.profile_collection.find_one({"userId": user_id})
            if item:
                item["_id"] = str(item["_id"])
                return item
        profiles = self._read_json(self.profiles_file, [DEFAULT_PROFILE])
        return next((p for p in profiles if p.get("userId") == user_id), DEFAULT_PROFILE)

    def save_profile(self, profile, user_id="default"):
        cleaned = {**DEFAULT_PROFILE, **self.get_profile(user_id), **profile, "userId": user_id}
        for key in ["fullName", "email", "targetYear", "optionalSubject", "state", "examType"]:
            cleaned[key] = str(cleaned.get(key, "")).strip()
        if self.profile_collection is not None:
            self.profile_collection.update_one({"userId": user_id}, {"$set": cleaned}, upsert=True)
            return self.get_profile(user_id)
        profiles = [p for p in self._read_json(self.profiles_file, []) if p.get("userId") != user_id]
        profiles.append(cleaned)
        self._write_json(self.profiles_file, profiles)
        return cleaned

    def sync_status(self):
        status = self._read_json(self.sync_file, DEFAULT_SYNC)
        return {**DEFAULT_SYNC, **status}

    def save_sync_status(self, status):
        merged = {**self.sync_status(), **status}
        self._write_json(self.sync_file, merged)
        return merged

    def update_next_sync(self):
        hour = int(os.getenv("DAILY_SYNC_HOUR", 6))
        minute = int(os.getenv("DAILY_SYNC_MINUTE", 0))
        now = datetime.now()
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if next_run <= now:
            next_run += timedelta(days=1)
        self.save_sync_status({"nextScheduledSync": next_run.isoformat(timespec="minutes")})

    def record_pdf_upload(self, upload):
        record = {"_id": uuid4().hex[:12], "uploadedAt": datetime.now().isoformat(timespec="seconds"), **upload}
        if self.pdf_collection is not None:
            result = self.pdf_collection.insert_one(record)
            return {**record, "_id": str(result.inserted_id)}
        uploads = self._read_json(self.pdf_uploads_file, [])
        uploads.insert(0, record)
        self._write_json(self.pdf_uploads_file, uploads)
        return record

    def pdf_upload_count(self):
        if self.pdf_collection is not None:
            return self.pdf_collection.count_documents({})
        return len(self._read_json(self.pdf_uploads_file, []))

    def question_bank(self):
        questions = []
        for article in self.all():
            for idx, q in enumerate(article.get("mcqs", []), start=1):
                questions.append({"kind": "Prelims", "number": idx, "articleId": article["_id"], "articleTitle": article["title"], "category": article.get("category"), **q})
            for idx, q in enumerate(article.get("mainsQuestions", []), start=1):
                questions.append({"kind": "Mains", "number": idx, "articleId": article["_id"], "articleTitle": article["title"], "category": article.get("category"), **q})
            for idx, q in enumerate(article.get("pyqs", []), start=1):
                questions.append({"kind": "PYQ", "number": idx, "articleId": article["_id"], "articleTitle": article["title"], "category": article.get("category"), **q})
        return questions
