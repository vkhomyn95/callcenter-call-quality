FROM python:3.10

WORKDIR /usr/src/

COPY /celery_worker/requirements.txt .



RUN pip install --no-cache-dir -r requirements.txt

COPY /celery_worker /usr/src/celery_worker

ENV PYTHONPATH /usr/src