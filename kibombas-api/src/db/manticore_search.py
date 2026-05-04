import logging
from manticoresearch.api.utils_api import UtilsApi
from manticoresearch import (
    Configuration,
    ApiClient,
    SearchApi,
    IndexApi,
    SearchRequest,
    InsertDocumentRequest
)
from src.core.config import settings
from src.db.entities import PostoCombustivelEntity, PrecoCombustivelEntity, TipoCombustivelEntity
from src.utils.mapper import Mapper

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class ManticoreSearchRepository:

    def __init__(self):
        host = settings.MANTICORE_SEARCH_URL
        logger.info("Initializing ManticoreSearchRepository")
        logger.info("Manticore Search URL: %s", host)
        self._config = Configuration(host=host)
        self._client = None
        self._utils_api = None

    async def get_client(self):
        if not self._client:
            self._client = ApiClient(self._config)
            
        return self._client
        
    async def initialize_schema(self):
        queries = [
            """
            CREATE TABLE IF NOT EXISTS posto_combustivel (
                posto_combustivel_id BIGINT,
                nome TEXT,
                marca TEXT,
                tipo TEXT,
                distrito TEXT,
                municipio TEXT,
                morada TEXT,
                localidade TEXT,
                cod_postal TEXT,
                latitude FLOAT,
                longitude FLOAT,
                data_indexacao TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS tipo_combustivel (
                tipo_combustivel_id BIGINT,
                municipio_id BIGINT,
                nome TEXT,
                data_indexacao TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS preco_combustivel (
                posto_combustivel_id BIGINT,
                posto_combustivel_nome TEXT,
                tipo_combustivel_id BIGINT,
                tipo_combustivel_nome TEXT,
                preco FLOAT,
                data_atualizacao TIMESTAMP,
                data_indexacao TIMESTAMP
            )
            """
        ]

        for sql in queries:
            try:
                client = await self.get_client()
                utils_api = UtilsApi(client)
                await utils_api.sql(sql.strip())
                print(f"Table created successfully.")
            except Exception as e:
                print(f"Error initializing Manticore table: {e}")
                raise e

    async def search_tipo_combustivel(
        self, tipo_combustivel_id: int, municipio_id: int
    ):
        client = await self.get_client()
        search_api = SearchApi(client)
        logger.info(f"Searching for tipo_combustivel_id={tipo_combustivel_id} and municipio_id={municipio_id}")
        logger.info(f"Using Manticore : {search_api.api_client.configuration.host}")
        request = SearchRequest(
            table="tipo_combustivel",
            query={
                "bool": {
                    "must": [
                        {"equals": {"tipo_combustivel_id": tipo_combustivel_id}},
                        {"equals": {"municipio_id": municipio_id}},
                    ]
                }
            },
            limit=1,
        )
        return await search_api.search(request)

    async def search_postos_combustiveis(
        self, distrito: str, municipio: str, limite: int = 100
    ):
        client = await self.get_client()
        search_api = SearchApi(client)
        logger.info(f"Using Manticore : {search_api.api_client.configuration.host}")
        request = SearchRequest(
            table="posto_combustivel",
            query={
                "bool": {
                    "must": [
                        {"match": {"distrito": distrito}},
                        {"match": {"municipio": municipio}},
                    ]
                }
            },
            limit=limite,
        )
        return await search_api.search(request)

    async def search_precos_combustiveis(
        self, postos_ids: list, tipo_combustivel_id: int, limite: int = 1000
    ):
        if not postos_ids or not tipo_combustivel_id:
            return []

        client = await self.get_client()
        search_api = SearchApi(client)
        logger.info(f"Using Manticore : {search_api.api_client.configuration.host}")
        request = SearchRequest(
            table="preco_combustivel",
            query={
                "bool": {
                    "must": [
                        {"in": {"posto_combustivel_id": postos_ids}},
                        {"equals": {"tipo_combustivel_id": tipo_combustivel_id}},
                    ]
                }
            },
            limit=limite,
            sort=[{"preco": "asc"}],
        )
        return await search_api.search(request)

    async def upsert_tipo_combustivel(self, tipo_combustivel: TipoCombustivelEntity):
        client = await self.get_client()
        index_api = IndexApi(client)
        doc = {
            "tipo_combustivel_id": tipo_combustivel.tipo_combustivel_id,
            "nome": tipo_combustivel.nome,
            "municipio_id": tipo_combustivel.municipio_id,
            "data_indexacao": tipo_combustivel.data_indexacao,
        }
        await index_api.replace(
            InsertDocumentRequest(table="tipo_combustivel", id=tipo_combustivel.id, doc=doc)
        )

    async def upsert_preco_combustivel(self, preco_combustivel: PrecoCombustivelEntity):
        client = await self.get_client()
        index_api = IndexApi(client)
        doc = {
            "posto_combustivel_id": preco_combustivel.posto_combustivel_id,
            "posto_combustivel_nome": preco_combustivel.posto_combustivel_nome,
            "tipo_combustivel_id": preco_combustivel.tipo_combustivel_id,
            "tipo_combustivel_nome": preco_combustivel.tipo_combustivel_nome,
            "preco": preco_combustivel.preco,
            "data_atualizacao": preco_combustivel.data_atualizacao,
            "data_indexacao": preco_combustivel.data_indexacao,
        }
        await index_api.insert(
            InsertDocumentRequest(table="preco_combustivel", id=preco_combustivel.id, doc=doc)
        )

    async def upsert_posto_combustivel(self, posto_combustivel: PostoCombustivelEntity):
        client = await self.get_client()
        index_api = IndexApi(client)
        doc = {
            "posto_combustivel_id": posto_combustivel.posto_combustivel_id,
            "nome": posto_combustivel.nome,
            "marca": posto_combustivel.marca,
            "tipo": posto_combustivel.tipo,
            "distrito": posto_combustivel.distrito,
            "municipio": posto_combustivel.municipio,
            "morada": posto_combustivel.morada,
            "localidade": posto_combustivel.localidade,
            "cod_postal": posto_combustivel.cod_postal,
            "latitude": posto_combustivel.latitude,
            "longitude": posto_combustivel.longitude,
            "data_indexacao": posto_combustivel.data_indexacao,
        }
        await index_api.replace(
            InsertDocumentRequest(table="posto_combustivel", id=posto_combustivel.id, doc=doc)
        )
