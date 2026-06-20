import json
import os
from datetime import date, datetime, timedelta
from pathlib import Path
from time import sleep

try:
    import requests
except ImportError:
    class _MissingRequests:
        def get(self, *_, **__):
            raise RuntimeError("requests is required for live news provider sync")
    requests = _MissingRequests()

try:
    from .nlp_service import analyze, category_scores
except ImportError:
    from nlp_service import analyze, category_scores

DEFAULT_SOURCES = [
    "The Hindu", "Indian Express", "PIB", "PRS India", "Down To Earth",
    "Business Standard", "Livemint", "RBI Releases", "NITI Aayog", "Ministry Websites",
]


def _clean(value):
    return (value or "").replace("[Removed]", "").strip()


def _source_queries():
    configured = [x.strip() for x in os.getenv("NEWS_SOURCES", "").split(",") if x.strip()]
    sources = configured or DEFAULT_SOURCES
    return [(source, f"{source} India UPSC current affairs") for source in sources]


def _provider_request(api_key, source, query, target):
    params = {
        "apiKey": api_key,
        "q": query,
        "language": os.getenv("NEWS_API_LANGUAGE", "en"),
        "from": target.isoformat(),
        "to": (target + timedelta(days=1)).isoformat(),
        "sortBy": "publishedAt",
        "pageSize": int(os.getenv("NEWS_API_PAGE_SIZE", 20)),
    }
    response = requests.get(os.getenv("NEWS_API_URL", "https://newsapi.org/v2/everything"), params=params, timeout=25)
    response.raise_for_status()
    payload = response.json()
    if payload.get("status") == "error":
        raise RuntimeError(payload.get("message", f"{source} rejected the request"))
    return payload.get("articles", [])


def _sample_articles(target):
    path = Path(__file__).parent / "data" / "sample_articles.json"
    try:
        sample = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        sample = []
    expanded = []
    for idx, item in enumerate(sample):
        expanded.append({
            "title": item.get("title"),
            "description": item.get("content") or item.get("summary"),
            "content": item.get("content") or item.get("summary"),
            "publishedAt": target.isoformat(),
            "url": f"local-sample://{idx}",
            "source": {"name": item.get("source", "Curated Sample")},
        })
    return expanded


def _create_from_raw(repo, raw, target, source_name, seen=None):
    title = _clean(raw.get("title"))
    content = _clean(raw.get("content"))
    description = _clean(raw.get("description"))
    body = content if len(content) >= 180 else " ".join(x for x in [description, content] if x)
    published = (raw.get("publishedAt") or target.isoformat())[:10]
    url = raw.get("url")
    dedupe_key = (url or f"{title}:{published}").lower()
    if seen is not None and dedupe_key in seen:
        return None, "duplicate-or-short"
    if not title or len(body) < 120 or repo.exists(title, published, url):
        return None, "duplicate-or-short"
    if seen is not None:
        seen.add(dedupe_key)
    if max(category_scores(f"{title} {body}").values()) == 0:
        return None, "not-upsc-relevant"
    source = (raw.get("source") or {}).get("name") or source_name
    return repo.create({
        "title": title,
        "source": source,
        "date": published,
        "content": body,
        "originalUrl": url,
        "sourceType": "news-api",
        **analyze(title, body),
    }), None


def _save_status(repo, payload):
    if hasattr(repo, "save_sync_status"):
        return repo.save_sync_status(payload)
    return payload


def _update_next(repo):
    if hasattr(repo, "update_next_sync"):
        repo.update_next_sync()


def fetch_daily_news(repo, target_date=None):
    target = target_date or date.today()
    api_key = os.getenv("NEWS_API_KEY", "").strip()
    _save_status(repo, {"status": "running", "lastSyncTime": datetime.now().isoformat(timespec="seconds"), "errors": [], "sourceResults": []})
    source_results, errors, created, skipped = [], [], [], 0
    seen = set()

    if not api_key:
        raw_items = _sample_articles(target)
        for raw in raw_items:
            item, reason = _create_from_raw(repo, raw, target, (raw.get("source") or {}).get("name", "Curated Sample"), seen)
            if item:
                created.append(item)
            else:
                skipped += 1
        source_results.append({"source": "Local curated sample", "status": "ok", "fetched": len(raw_items), "created": len(created), "mode": "sample"})
    else:
        for source, query in _source_queries():
            fetched, source_created, source_skipped = 0, 0, 0
            source_error = None
            for attempt in range(1, 4):
                try:
                    raw_items = _provider_request(api_key, source, query, target)
                    fetched = len(raw_items)
                    for raw in raw_items:
                        item, reason = _create_from_raw(repo, raw, target, source, seen)
                        if item:
                            created.append(item)
                            source_created += 1
                        else:
                            skipped += 1
                            source_skipped += 1
                    break
                except Exception as exc:
                    source_error = str(exc)
                    if attempt < 3:
                        sleep(0.4 * attempt)
            result = {"source": source, "status": "failed" if source_error and fetched == 0 else "ok", "fetched": fetched, "created": source_created, "skipped": source_skipped}
            if source_error and fetched == 0:
                result["error"] = source_error
                errors.append({"source": source, "error": source_error})
            source_results.append(result)

    status = "partial" if errors and created else "failed" if errors and not created else "success"
    sync_status = _save_status(repo, {
        "status": status,
        "lastSyncTime": datetime.now().isoformat(timespec="seconds"),
        "articlesFetched": sum(x.get("fetched", 0) for x in source_results),
        "createdCount": len(created),
        "skippedCount": skipped,
        "sourceResults": source_results,
        "errors": errors,
    })
    _update_next(repo)
    return {
        "created": created,
        "createdCount": len(created),
        "skippedCount": skipped,
        "provider": os.getenv("NEWS_API_PROVIDER", "NewsAPI compatible provider") if api_key else "Local curated sample",
        "sourceResults": source_results,
        "errors": errors,
        "syncStatus": sync_status,
    }
