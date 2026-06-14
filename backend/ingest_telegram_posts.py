import asyncio

from app.telegram_ingestion import ingest_telegram_posts


if __name__ == "__main__":
    asyncio.run(ingest_telegram_posts())
