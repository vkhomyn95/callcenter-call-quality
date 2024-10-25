FROM python:3.10

WORKDIR /usr/src

COPY /communicator/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir /usr/src/communicator

COPY /communicator /usr/src/communicator/

ENV PYTHONPATH=/usr/src
