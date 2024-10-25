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


def terminate_existing_worker(worker_name):
    workers = Worker.all(connection=redis_conn)
    for worker in workers:
        if worker.name == worker_name:
            worker.request_stop()  # Gracefully stop the worker
            print(f"Terminated existing worker: {worker_name}")


if __name__ == "__main__":
    worker_name = "transcription_postback_hook_worker"
    terminate_existing_worker(worker_name)
    with Connection(redis_conn):
        worker = Worker(map(Queue, listen), name=worker_name)
        worker.work(with_scheduler=True)
