import elasticsearch
from celery import Celery
from celery.backends.elasticsearch import ElasticsearchBackend
from kombu import serialization

from communicator.variables import variables


class CustomElasticsearchBackend(ElasticsearchBackend):

    index = variables.elasticsearch_index

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
    backend='communicator.job.start.CustomElasticsearchBackend',
    result_serializer='elasticsearch',
    accept_content=['application/json', 'application/x-elasticsearch']
)

celery.conf.update({
    'broker_connection_retry': True,
    'broker_connection_retry_on_startup': True
})