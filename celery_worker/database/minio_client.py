from minio import Minio

from celery_worker.variables import variables


class MinioClient:
    """
    Клас для ініціалізації клієнта MinIO.
    Екземпляр створюється один раз на рівні модуля.
    """

    def __init__(self):
        print("🚀 Ініціалізація клієнта MinIO...")

        try:
            self.client = Minio(
                endpoint=variables.minio_endpoint,
                access_key=variables.minio_access_key,
                secret_key=variables.minio_secret_key,
                secure=variables.minio_secure
            )
            self.client.list_buckets()
            print("✅ З'єднання з MinIO успішно встановлено.")
        except Exception as e:
            print(f"❌ Помилка підключення до MinIO: {e}")
            self.client = None


minio_client = MinioClient().client
