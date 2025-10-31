import logging
import os
import asyncio
import argparse
from dotenv import load_dotenv
from app.db.initdb import engine
from app.utils.backfill import update_document_embeddings

load_dotenv()
BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "10"))

async def fill_embeddings(limit=None):
    """CLI wrapper for embedding backfill operation."""
    async with engine.begin() as conn:
        success_count, failed_ids = await update_document_embeddings(
            conn=conn,
            batch_size=BATCH_SIZE,
            limit=limit
        )
        logging.info(f"\nProcessed {success_count + len(failed_ids)} documents:")
        logging.info(f"- {success_count} succeeded")
        logging.info(f"- {len(failed_ids)} failed")
        if failed_ids:
            logging.debug(f"Failed document IDs: {failed_ids}")

def main():
    """Entry point for the CLI script."""
    parser = argparse.ArgumentParser(
        description="Fill missing embeddings for documents in the database."
    )
    parser.add_argument(
        '--limit', '-n',
        type=int,
        default=None,
        help="Maximum number of documents to process"
    )
    args = parser.parse_args()
    asyncio.run(fill_embeddings(limit=args.limit))

if __name__ == '__main__':
    main()