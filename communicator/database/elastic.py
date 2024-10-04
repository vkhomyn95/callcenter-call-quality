from elasticsearch import Elasticsearch
from sqlalchemy.testing.plugin.plugin_base import logging

from communicator.variables import variables


class ElasticDatabase:
    _database_instance = None

    @staticmethod
    def instance():
        return ElasticDatabase._database_instance

    def __init__(self) -> None:
        if ElasticDatabase._database_instance is None:
            try:
                self.session = Elasticsearch(variables.elasticsearch_uri)

            except Exception as e:
                logging.error(f'  >> Error connecting to the elasticsearch database: {e}')
        else:
            raise Exception("{}: Cannot construct, an elasticsearch instance is already running.".format(__file__))

    def load_recognitions(
            self,
            user_id: int,
            task_id: str,
            limit: int,
            offset: int
    ):
        try:
            criteria = []
            criteria.append({"match": {"task_id": task_id}}) if task_id else None
            criteria.append({"match": {"user_id": user_id}}) if user_id else None

            query = {
                "_source": ["_id", "received_date", "@timestamp", "num_channels", "duration", "status", "task_id", "unique_uuid"],
                "query": {
                    # "range": {
                    #     "result.date_done": {
                    #         "gte": "2023-01-01",
                    #         "lte": "2023-12-31"
                    #     }
                    # }
                    "bool": {
                        "must": criteria
                    }
                },
                "sort": [
                    {"@timestamp": {"order": "desc"}}
                ],
                "from": offset,
                "size": limit
            }

            response = self.session.search(index=variables.elasticsearch_index, body=query)
            hits = response['hits']['hits']
            return [x['_source'] for x in hits]
        except Exception as e:
            logging.error(f'  >> Error during query elasticsearch: {e}')
            return None

    def count_recognitions(
            self,
            user_id: int,
            task_id: str
    ):
        try:
            criteria = []
            criteria.append({"match": {"task_id": task_id}}) if task_id else None
            criteria.append({"match": {"user_id": user_id}}) if user_id else None

            query = {
                "query": {
                    # "range": {
                    #     "result.date_done": {
                    #         "gte": "2023-01-01",
                    #         "lte": "2023-12-31"
                    #     }
                    # }
                    "bool": {
                        "must": criteria
                    }
                }
            }

            response = self.session.count(index=variables.elasticsearch_index, body=query)
            return response['count']
        except Exception as e:
            logging.error(f'  >> Error during query elasticsearch: {e}')
            return None

    def load_recognition_by_id(
            self,
            user_id: int,
            task_id: str
    ):
        try:
            query = {
                "_source": [
                    "_id",
                    "received_date",
                    "transcription_date",
                    "@timestamp",
                    "num_channels",
                    "duration",
                    "status",
                    "task_id",
                    "user_id",
                    "unique_uuid",
                    "transcription"
                ],
                "query": {
                    # "range": {
                    #     "result.date_done": {
                    #         "gte": "2023-01-01",
                    #         "lte": "2023-12-31"
                    #     }
                    # }
                    "bool": {
                        "must": [
                            # {
                            #     "match": {
                            #         "status": "SUCCESS"
                            #     }
                            # },
                            {
                                "match": {
                                    "task_id": task_id
                                }
                            }
                        ]
                    }
                },
                "size": 1
            }

            response = self.session.search(index=variables.elasticsearch_index, body=query)
            hits = response['hits']['hits']
            if len(hits) > 0:
                return hits[0]['_source']
            return None
        except Exception as e:
            logging.error(f'  >> Error during query elasticsearch: {e}')
            return None

    def load_user_dashboard(self, user_id: int):
        try:
            query_today = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "range": {
                                    "@timestamp": {
                                        "gte": "now/d",
                                        "lt": "now+1d/d"
                                    }
                                }
                            },
                            {
                                "term": {
                                    "user_id": user_id
                                }
                            }
                        ]
                    }
                },
                "size": 0,
                "aggs": {
                    "total_duration_today": {
                        "sum": {
                            "field": "duration"
                        }
                    },
                    "total_transcriptions_today": {
                        "value_count": {
                            "field": "user_id"
                        }
                    }
                }
            }

            query_this_week = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "range": {
                                    "@timestamp": {
                                        "gte": "now/w",
                                        "lt": "now+1w/w"
                                    }
                                }
                            },
                            {
                                "term": {
                                    "user_id": user_id
                                }
                            }
                        ]
                    }
                },
                "size": 0,
                "aggs": {
                    "total_duration_this_week": {
                        "sum": {
                            "field": "duration"
                        },
                    },
                    "total_transcriptions_week": {
                        "value_count": {
                            "field": "user_id"
                        }
                    }
                }
            }

            query_this_month = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "range": {
                                    "@timestamp": {
                                        "gte": "now/M",
                                        "lt": "now+1M/M"
                                    }
                                }
                            },
                            {
                                "term": {
                                    "user_id": user_id
                                }
                            }
                        ]
                    }
                },
                "size": 0,
                "aggs": {
                    "total_duration_this_month": {
                        "sum": {
                            "field": "duration"
                        }
                    },
                    "total_transcriptions_month": {
                        "value_count": {
                            "field": "user_id"
                        }
                    }
                }
            }

            # Execute the queries and get the results
            result_today = self.session.search(index=variables.elasticsearch_index, body=query_today)
            result_this_week = self.session.search(index=variables.elasticsearch_index, body=query_this_week)
            result_this_month = self.session.search(index=variables.elasticsearch_index, body=query_this_month)

            # Extract the sum of durations
            return {
                "today": {
                    "duration": result_today['aggregations']['total_duration_today']['value'],
                    "records": result_today['aggregations']['total_transcriptions_today']['value'],
                },
                "week": {
                    "duration": result_this_week['aggregations']['total_duration_this_week']['value'],
                    "records": result_this_week['aggregations']['total_transcriptions_week']['value'],
                },
                "month": {
                    "duration": result_this_month['aggregations']['total_duration_this_month']['value'],
                    "records": result_this_month['aggregations']['total_transcriptions_month']['value']
                }
            }

        except Exception as e:
            logging.error(f'  >> Error during query elasticsearch: {e}')
            return None


elastic = ElasticDatabase()
