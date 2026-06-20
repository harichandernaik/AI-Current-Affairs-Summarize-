import os
from datetime import date

def start_daily_scheduler(repo):
    repo.update_next_sync()
    if os.getenv("ENABLE_DAILY_SYNC", "false").lower() != "true": return None
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from .news_service import fetch_daily_news
    except ImportError:
        from apscheduler.schedulers.background import BackgroundScheduler
        from news_service import fetch_daily_news
    def run_sync():
        try:
            fetch_daily_news(repo, date.today())
        except Exception as exc:
            repo.save_sync_status({"status": "failed", "errors": [{"source": "scheduler", "error": str(exc)}]})
        finally:
            repo.update_next_sync()
    scheduler = BackgroundScheduler(timezone="Asia/Kolkata")
    scheduler.add_job(run_sync, "cron", hour=int(os.getenv("DAILY_SYNC_HOUR", 6)), minute=int(os.getenv("DAILY_SYNC_MINUTE", 0)), id="daily-news-sync", replace_existing=True, max_instances=1)
    scheduler.start()
    return scheduler
