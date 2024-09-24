from datetime import datetime, timezone
import elasticsearch
from celery import Celery
from celery.backends.elasticsearch import ElasticsearchBackend
from kombu import serialization

from celery_worker.variables import variables


class CustomElasticsearchBackend(ElasticsearchBackend):

    index = variables.elasticsearch_index

    def _set_with_state(self, key, value, state):
        print(value)
        body = {
            'status': value["status"],
            'task_id': value["task_id"],
            'duration': value["result"]["duration"],
            'num_channels': value["result"]["num_channels"],
            'user_id': value["result"]["user_id"],
            'talk_record_id': value["result"]["talk_record_id"],
            'transcription': value["result"]["transcription"],
            'received_date': value["result"]["received_date"],
            'transcription_date': value["result"]["transcription_date"],
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
    'broker_connection_retry_on_startup': True
})