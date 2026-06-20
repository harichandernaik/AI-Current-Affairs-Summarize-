import os, sys, unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1]))
from news_service import fetch_daily_news
from pdf_ingestion import ingest_newspaper_pdf

class MemoryRepo:
    def __init__(self): self.items = []
    def exists(self, *args): return False
    def create(self, item): self.items.append({"_id": str(len(self.items)+1), **item}); return self.items[-1]
    def record_pdf_upload(self, item): self.upload = item; return item

class Response:
    def raise_for_status(self): pass
    def json(self):
        return {"status":"ok","articles":[{"title":"India expands renewable climate programme","description":"A new climate and renewable energy programme will reduce industrial emissions and support forest conservation across India through green technology investment.","content":"The environment ministry described implementation standards, finance safeguards and conservation targets for the national programme.","publishedAt":"2026-06-19T05:00:00Z","url":"https://licensed.example/story","source":{"name":"Licensed Daily"}}]}

class IngestionTests(unittest.TestCase):
    @patch.dict(os.environ, {"NEWS_API_KEY":"test-key"})
    @patch("news_service.requests.get", return_value=Response())
    def test_news_sync_creates_grounded_brief(self, mocked_get):
        repo = MemoryRepo(); result = fetch_daily_news(repo)
        self.assertEqual(result["createdCount"], 1)
        self.assertEqual(repo.items[0]["sourceType"], "news-api")
        self.assertTrue(repo.items[0]["mcqs"])
        self.assertNotIn("test-key", str(repo.items[0]))

    @patch("pdf_ingestion.extract_pdf_text")
    def test_pdf_ingestion_skips_duplicate_articles_in_same_upload(self, mocked_extract):
        article = "PARLIAMENT REVIEWS DIGITAL COMPETITION BILL\n" + ("The parliament reviewed constitutional safeguards, rights, competition law and ministry accountability for digital markets. " * 7)
        mocked_extract.return_value = (article + "\n\n" + article, 2, "test")
        repo = MemoryRepo()
        result = ingest_newspaper_pdf(b"%PDF fake", "paper.pdf", "Daily", "2026-06-20", repo)
        self.assertEqual(result["detectedCount"], 2)
        self.assertEqual(result["createdCount"], 1)
        self.assertEqual(result["ignoredCount"], 1)
        self.assertEqual(repo.items[0]["category"], "Polity")

if __name__ == "__main__": unittest.main()
