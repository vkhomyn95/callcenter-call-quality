import json
import os
from dataclasses import dataclass, field
from typing import List, Dict

from dotenv import load_dotenv

load_dotenv()


def load_flower_state_cleaner() -> List[Dict]:
    return json.loads(os.getenv(
        "FLOWER_STATE_CLEANER",
        '[{"type": "transcribe", "max_count": 100, "timedelta": 30}]'
    ))


@dataclass(frozen=True)
class Variables:
    """ This class is responsible for saving and
        loading variables from the system environment.

        Initiated at the entry point
    """
    license_server_access_token: str = os.getenv(
        "LICENSE_SERVER_ACCESS_TOKEN",
        "TOKEN"
    )

    elasticsearch_uri: str = os.getenv(
        "ELASTICSEARCH_URI",
        "http://localhost:9200"
    )
    elasticsearch_index: str = os.getenv(
        "ELASTICSEARCH_INDEX",
        "transcriptions"
    )

    admin_default_password: str = os.getenv(
        "MARIADB_DATABASE_DEFAULT_PASSWORD",
        "password"
    )

    mariadb_database_user: str = os.getenv(
        "MARIADB_DATABASE_USER",
        "root"
    )
    mariadb_database_password: str = os.getenv(
        "MARIADB_DATABASE_PASSWORD",
        "root"
    )
    mariadb_database_host: str = os.getenv(
        "MARIADB_DATABASE_HOST",
        "127.0.0.1"
    )
    mariadb_database_port: int = int(os.getenv(
        "MARIADB_DATABASE_PORT",
        3306
    ))
    mariadb_database_name: str = os.getenv(
        "MARIADB_DATABASE_NAME",
        "recognition"
    )

    # worker configuration constants
    celery_broker: str = os.getenv(
        "CELERY_BROKER",
        "amqp://user:password@localhost:5672/"
    )
    celery_broker_api: str = os.getenv(
        "CELERY_BROKER_API",
        "http://user:password@localhost:15672/api/"
    )
    celery_backend: str = os.getenv(
        "CELERY_BACKEND",
        "elasticsearch://localhost:9200/transcriptions"
    )

    redis_url: str = os.getenv(
        "REDIS_URL",
        "redis://localhost:6379/1"
    )
    redis_queue_name: str = os.getenv(
        "REDIS_QUEUE_NAME",
        "webhook_queue"
    )
    redis_max_retries: int = int(os.getenv(
        "REDIS_MAX_RETRIES",
        10
    ))
    redis_retry_delay: float = float(os.getenv(
        "REDIS_RETRY_DELAY",
        30.0
    ))

    whisper_model: str = os.getenv(
        "WHISPER_MODEL",
        "openai/whisper-large-v3"
    )

    app_host: str = os.getenv(
        "APP_HOST",
        "127.0.0.1"
    )
    app_port: int = int(os.getenv(
        "APP_PORT",
        8000
    ))

    logger_dir: str = os.getenv(
        "LOGGER_DIR",
        "/stor/data/logs/server/"
    )
    file_dir: str = os.getenv(
        "FILE_DIR",
        "/stor/data/transcription/"
    )
    base_dir = os.path.dirname(__file__)

    # Flower
    purge_offline_workers: int = os.getenv(
        "PURGE_OFFLINE_WORKERS",
        None
    )
    inspect_timeout: float = float(os.getenv(
        "INSPECT_TIMEOUT",
        1000.0
    ))
    flower_db: str = os.getenv(
        "FLOWER_DATABASE",
        "/stor/data/flower"
    )
    flower_persistent: bool = bool(os.getenv(
        "FLOWER_PERSISTENT",
        True
    ))
    flower_state_save_interval: int = int(os.getenv(
        "FLOWER_STATE_SAVE_INTERVAL",
        0
    ))
    flower_enable_events: bool = bool(os.getenv(
        "FLOWER_ENABLE_EVENTS",
        True
    ))
    flower_state_save_failed: bool = bool(os.getenv(
        "FLOWER_STATE_SAVE_FAILED",
        False
    ))
    flower_state_cleaner: list = field(
        default_factory=load_flower_state_cleaner
    )
    flower_max_workers: int = int(os.getenv(
        "FLOWER_MAX_WORKERS",
        5000
    ))
    flower_max_tasks: int = int(os.getenv(
        "FLOWER_MAX_TASKS",
        100000
    ))
    flower_unix_socket: str = os.getenv(
        "FLOWER_UNIX_SOCKET",
        ""
    )
    flower_address: str = os.getenv(
        "FLOWER_ADDRESS",
        ""
    )
    flower_port: int = int(os.getenv(
        "FLOWER_PORT",
        5555
    ))

    telegram_bot_token: str = os.getenv(
        "TELEGRAM_TOKEN", ""
    )


variables = Variables()
