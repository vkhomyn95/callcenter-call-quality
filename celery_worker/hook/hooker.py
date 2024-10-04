import re
import uuid
from http import HTTPStatus
from http.client import HTTPException
from typing import Optional, Any

import httpx
import redis
from pydantic import BaseModel
from rq import Queue, Retry
from rq.job import Job

from celery_worker.variables import variables


class HookerRequestPayload(BaseModel):
    """Pydantic model to declare and validate webhook payload."""

    url: str  # Webhook callback url
    auth: Optional[str]  # Webhook callback auth
    payload: dict[str, Any]  # The actual payload to be sent to 'to_url'


redis_conn = redis.Redis.from_url(variables.redis_url)
queue = Queue(
    variables.redis_queue_name,
    connection=redis_conn
)


def validate_url(url: str) -> str:
    regex = re.compile(
        r"^(?:http|ftp)s?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # domain...
        r"localhost|"  # localhost...
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )
    return bool(re.match(regex, url))


def send_post_request(webhook_payload: HookerRequestPayload) -> None:
    headers = {
        "Content-Type": "application/json",
    }
    print("Sending POST request")

    with httpx.Client(http2=True) as session:
        print(webhook_payload)
        response = session.post(
            webhook_payload["url"],
            headers=headers,
            json=webhook_payload["payload"],
            timeout=10,
        )

        if not response.status_code == HTTPStatus.OK:
            print("Error POST request")
            raise HTTPException(
                f"Sending webhook failed.\n"
                f"to_url: {webhook_payload['url']}\n"
                f"payload: {webhook_payload['payload']}\n, code: {response.status_code}"
            )


def report_failure(job, connection, type, value, traceback):
    """
    Flag a job as failed if it has 0 or None reties left
    """

    if job.retries_left:
        return


def send_webhook(*, webhook_payload: HookerRequestPayload) -> Job:
    return queue.enqueue(
        send_post_request,
        webhook_payload,
        retry=Retry(10, 60),
        job_timeout=20,
        job_id=f"{webhook_payload['payload']['task_id']}"
    )
