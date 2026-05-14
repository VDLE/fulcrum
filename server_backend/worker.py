#!/usr/bin/env python
"""Worker for processing analytics tasks in a separate process"""
import os
import logging
import redis
from rq import Worker, Queue
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

try:
    logger.info(f"Connecting to Redis at {REDIS_HOST}:{REDIS_PORT}")
    redis_conn = redis.Redis(
        host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, password=REDIS_PASSWORD
    )
    redis_conn.ping()
    logger.info("Successfully connected to Redis")
except Exception as e:
    logger.error(f"Failed to connect to Redis: {str(e)}")
    raise

QUEUES = ["analytics"]

if __name__ == "__main__":
    logger.info(f"Starting worker, listening to queues: {', '.join(QUEUES)}")
    queues = [Queue(name, connection=redis_conn) for name in QUEUES]

    def exception_handler(job, exc_type, exc_value, tb):
        logger.error(f"Error in job {job.id}: {exc_type.__name__} - {str(exc_value)}")
        import traceback
        tb_str = "".join(traceback.format_exception(exc_type, exc_value, tb))
        logger.error(f"Traceback:\n{tb_str}")
        from rq.handlers import move_to_failed_queue
        return move_to_failed_queue(job, exc_type, exc_value, tb)

    worker = Worker(
        queues, connection=redis_conn, exception_handlers=[exception_handler]
    )
    logger.info(f"Worker created for queues: {', '.join(QUEUES)}")
    worker.work()
