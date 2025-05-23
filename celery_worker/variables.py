import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Variables:
    """ This class is responsible for saving and
        loading variables from the system environment.

        Initiated at the entry point
    """
    license_server_access_token: str = os.getenv(
        "LICENSE_SERVER_ACCESS_TOKEN", "TOKEN"
    )

    elasticsearch_uri: str = os.getenv(
        "ELASTICSEARCH_URI", "http://localhost:9200"
    )
    elasticsearch_index: str = os.getenv(
        "ELASTICSEARCH_INDEX", "transcriptions"
    )

    admin_default_password: str = os.getenv(
        "MARIADB_DATABASE_DEFAULT_PASSWORD", "password"
    )

    mariadb_database_user: str = os.getenv(
        "MARIADB_DATABASE_USER", "root"
    )
    mariadb_database_password: str = os.getenv(
        "MARIADB_DATABASE_PASSWORD", "root"
    )
    mariadb_database_host: str = os.getenv(
        "MARIADB_DATABASE_HOST", "127.0.0.1"
    )
    mariadb_database_port: int = int(os.getenv(
        "MARIADB_DATABASE_PORT", 3306
    ))
    mariadb_database_name: str = os.getenv(
        "MARIADB_DATABASE_NAME", "recognition"
    )

    # worker configuration constants
    celery_broker: str = os.getenv(
        "CELERY_BROKER", "amqp://user:password@localhost:5672/"
    )
    celery_backend: str = os.getenv(
        "CELERY_BACKEND", "elasticsearch://localhost:9200/transcriptions"
    )

    redis_url: str = os.getenv(
        "REDIS_URL", "redis://localhost:6379/1"
    )
    redis_queue_name: str = os.getenv(
        "REDIS_QUEUE_NAME", "webhook_queue"
    )
    redis_max_retries: int = int(os.getenv(
        "REDIS_MAX_RETRIES", 10
    ))
    redis_retry_delay: float = float(os.getenv(
        "REDIS_RETRY_DELAY", 30.0
    ))

    elevenlabs_api_key: str = os.getenv(
        "ELEVENLABS_API_KEY", ""
    )

    openai_api_key: str = os.getenv(
        "OPENAI_API_KEY", ""
    )

    gemini_api_key: str = os.getenv(
        "GEMINI_API_KEY", ""
    )

    app_host: str = os.getenv(
        "APP_HOST", "127.0.0.1"
    )
    app_port: int = int(os.getenv(
        "APP_PORT", 8000
    ))

    logger_dir: str = os.getenv(
        "LOGGER_DIR", "/stor/data/logs/server/"
    )

    file_dir: str = os.getenv(
        "FILE_DIR", "/stor/data/transcription/"
    )

    telegram_bot_token: str = os.getenv(
        "TELEGRAM_TOKEN", ""
    )


variables = Variables()
