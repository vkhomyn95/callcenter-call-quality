FROM python:3.10

WORKDIR /usr/src

COPY /rq_worker/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY /rq_worker /usr/src/

ENV PYTHONPATH /usr/src