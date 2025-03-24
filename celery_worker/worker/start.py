from datetime import datetime, timezone

import elasticsearch
from celery import Celery
from celery.backends.elasticsearch import ElasticsearchBackend
from elasticsearch import Elasticsearch
from kombu import serialization

from celery_worker.variables import variables


class CustomElasticsearchBackend(ElasticsearchBackend):

    index = variables.elasticsearch_index

    def _set_with_state(self, key, value, state):
        body = {
            "model": value["result"]["model"] if "model" in value["result"] else None,
            'status': value["status"],
            'task_id': value["task_id"],
            'duration': value["result"]["duration"] if "duration" in value["result"] else None,
            'num_channels': value["result"]["num_channels"] if "num_channels" in value["result"] else None,
            'user_id': value["result"]["user_id"] if "user_id" in value["result"] else None,
            'talk_record_id': value["result"]["talk_record_id"] if "talk_record_id" in value["result"] else None,
            'transcription': value["result"]["transcription"] if "transcription" in value["result"] else None,
            'unique_uuid': value["result"]["unique_uuid"] if "unique_uuid" in value["result"] else None,
            'received_date': value["result"]["received_date"] if "received_date" in value["result"] else None,
            'transcription_date': value["result"]["transcription_date"] if "transcription_date" in value["result"] else None,
            '@timestamp': '{}Z'.format(datetime.now(timezone.utc).isoformat()[:-9]),
        }

        try:
            self._index(
                id=key,
                body=body,
            )
        except elasticsearch.exceptions.ConflictError:
            # document already exists, update it
            self._update(key, body, state)

    def get(self, key):
        try:
            res = self._get(key)
            try:
                if res['found']:
                    return {
                        "status": res['_source']['status'],
                        "result": res['_source']['transcription']
                    }
            except (TypeError, KeyError):
                pass
        except elasticsearch.exceptions.NotFoundError:
            pass


es = Elasticsearch(variables.elasticsearch_uri)

if not es.indices.exists(index=variables.elasticsearch_index):
    mapping = {
        "properties": {
            "model": {"type": "keyword"},
            "status": {"type": "keyword"},
            "task_id": {"type": "keyword"},
            "duration": {"type": "float"},
            "num_channels": {"type": "integer"},
            "user_id": {"type": "integer"},
            "talk_record_id": {"type": "integer"},
            "transcription": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "text",
                        "fields": {
                            "keyword": {
                                "type": "keyword",
                                "ignore_above": 256
                            }
                        }
                    },
                    "start": {"type": "float"},
                    "end": {"type": "float"},
                    "speaker_id": {"type": "integer"}
                }
            },
            "unique_uuid": {"type": "keyword"},
            "received_date": {"type": "date"},
            "transcription_date": {"type": "date"},
            "@timestamp": {"type": "date"}
        }

    }
    es.indices.create(index=variables.elasticsearch_index, body={"mappings": mapping})

serialization.register(
    'elasticsearch', lambda x: x, lambda x: x,
    content_type='application/x-elasticsearch',
)

celery = Celery(
    'tasks',
    broker=variables.celery_broker,
    backend='celery_worker.worker.start.CustomElasticsearchBackend',
    result_serializer='elasticsearch',
    accept_content=['application/json', 'application/x-elasticsearch']
)

celery.conf.update({
    'broker_connection_retry': True,
    'broker_connection_retry_on_startup': True,
    'worker_send_task_events': True,
    'task_routes': {
        "celery_worker.worker.worker.transcribe_scribe_v1": {"queue": "scribe_v1_queue"},
        "celery_worker.worker.worker.transcribe_openai_whisper": {"queue": "openai_whisper_queue"},
    }
})