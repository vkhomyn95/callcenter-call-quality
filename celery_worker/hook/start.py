"""Module dedicated to spawn rq workers."""
import logging
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


def terminate_existing_workers():
    workers = Worker.all(connection=redis_conn)
    for worker in workers:
        try:
            worker.teardown()
            worker._shutdown()
        except Exception as e:
            logging.error("Error terminating worker ", worker.name, e)


if __name__ == "__main__":
    worker_name = "transcription_postback_hook_worker"
    terminate_existing_workers()
    with Connection(redis_conn):
        worker = Worker(map(Queue, listen), name=worker_name)
        worker.work(with_scheduler=True)
