"""Module dedicated to spawn rq workers."""
import os

from dotenv import load_dotenv
from redis import Redis
from rq import Connection, Queue
from rq.worker import Worker

load_dotenv()

listen = [
    os.getenv(
        "REDIS_QUEUE_NAME",
        "webhook_queue"
    )
]
redis_conn = Redis.from_url(
    os.getenv(
        "REDIS_URL",
        "redis://localhost:6379/1"
    )
)


if __name__ == "__main__":
    with Connection(redis_conn):
        worker = Worker(map(Queue, listen), name="transcription_postback_hook_worker")
        worker.work(with_scheduler=True)
