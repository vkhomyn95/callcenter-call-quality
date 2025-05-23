==============Development==============
This project consist of three main modules:
- celery_worker - where are two system part: monitoring dashboard (flower) and celery worker of transcriptions
- rq_worker - where are two system part: monitoring dashboard and worker thread of webhook
- communicator - entrypoint of app


Run scribe:
celery --app celery_worker.worker.worker.celery worker --concurrency=1 --queues=scribe_v1_queue -E --hostname=worker1@%h

Run 4o transcribe:
celery --app celery_worker.worker.worker.celery worker --concurrency=1 --queues=openai_whisper_queue -E --hostname=worker2@%h

celery --app celery_worker.worker.worker.celery worker --concurrency=1 --queues=gemini_queue -E --hostname=worker3@%h
