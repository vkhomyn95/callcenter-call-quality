FROM python:3.10

WORKDIR /usr/src/

COPY /celery_worker/requirements.txt .

RUN  apt-get update && apt-get install -y 'ffmpeg'

RUN python -m pip install -U torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu124

RUN pip install --no-cache-dir -r requirements.txt

COPY /celery_worker /usr/src/celery_worker

ENV PYTHONPATH /usr/src