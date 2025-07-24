from elasticsearch import AsyncElasticsearch

from app.config import ELASTICSEARCH_URL, LOG_INDEX

es = AsyncElasticsearch([ELASTICSEARCH_URL])


async def save_log(log_data: dict):
    await es.index(index=LOG_INDEX, document=log_data)
