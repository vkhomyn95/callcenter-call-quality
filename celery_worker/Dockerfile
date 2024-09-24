FROM python:3.10

WORKDIR /

COPY /celery_worker/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY /celery_worker /celery_worker