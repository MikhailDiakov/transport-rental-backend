from elasticsearch import Elasticsearch

from app.config import ELASTICSEARCH_URL, LOG_INDEX

es = Elasticsearch(ELASTICSEARCH_URL)


def save_log(log_data: dict):
    es.index(index=LOG_INDEX, body=log_data)
