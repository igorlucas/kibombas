from math import atan2, cos, radians, sin, sqrt
import time
import logging
import asyncio
from typing import List
from manticoresearch import HitsHits
from manticoresearch.rest import ApiException
from src.db.entities import PostoCombustivelEntity, PrecoCombustivelEntity, TipoCombustivelEntity
from src.schemas import BuscarPrecoCombustivelResponse
from src.services.dgeg import DGEGService
from src.utils.formatter import Formatter
from src.utils.mapper import Mapper
from src.db.manticore_search import ManticoreSearchRepository

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
manticore_search_repository = ManticoreSearchRepository()


class ManticoreService:

    async def buscar_precos_postos_combustiveis(
        self, tipo_combustivel_id: int, latitude: float, longitude: float
    ) -> BuscarPrecoCombustivelResponse:
        dgeg_service = DGEGService()
        municipio = await dgeg_service.buscar_municipio(latitude, longitude)
        if not municipio:
            return Mapper.mapear_preco_combustivel_response(None)

        municipio_id = municipio.get("Id")
        municipio_name = municipio.get("Descritivo")
        distrito_id = municipio.get("IdDistrito")
        distrito_name = municipio.get("Distrito").get("Descritivo")
        try:
            tipo_combustivel_indexado = (
                await manticore_search_repository.search_tipo_combustivel(
                    tipo_combustivel_id, municipio_id
                )
            )
            data_idexacao_valida = True
            if (
                tipo_combustivel_indexado.hits
                and tipo_combustivel_indexado.hits.total > 0
                and data_idexacao_valida
            ):
                hits = await self._buscar_preco_postos(
                    tipo_combustivel_id,
                    distrito_name,
                    municipio_name,
                    latitude,
                    longitude,
                )
                return Mapper.mapear_preco_combustivel_response(hits)

            if (
                tipo_combustivel_indexado.hits
                and tipo_combustivel_indexado.hits.total == 0
            ):
                tipo_combustivel = await dgeg_service.buscar_tipo_combustivel(
                    tipo_combustivel_id
                )
                if not tipo_combustivel:
                    return Mapper.mapear_preco_combustivel_response(None)

                dgeg_preco_combustiveis = await dgeg_service.buscar_preco_combustiveis(
                    tipo_combustivel_id, distrito_id, municipio_id
                )
                if not dgeg_preco_combustiveis:
                    return Mapper.mapear_preco_combustivel_response(None)

                await self._indexar_dados(
                    tipo_combustivel, municipio_id, municipio_name, dgeg_preco_combustiveis
                )
                hits = await self._buscar_preco_postos(
                    tipo_combustivel_id, 
                    distrito_name, 
                    municipio_name,
                    latitude,
                    longitude
                )
                return Mapper.mapear_preco_combustivel_response(hits)
        except Exception as e:
            logger.error(f"Erro no servidor: {e}")
            return None
        except ApiException as e:
            logger.error(f"Erro na comunicação com ManticoreSearch: {e}")
            return None

    async def _buscar_preco_postos(
        self,
        tipo_combustivel_id: int,
        distrito: str,
        municipio: str,
        usuario_latitude: float,
        usuario_longitude: float,
    ) -> List[HitsHits] | None:
        resultado_postos = await manticore_search_repository.search_postos_combustiveis(
            distrito, municipio
        )
        if (
            not resultado_postos
            or not resultado_postos.hits
            or not resultado_postos.hits.hits
        ):
            return None

        postos_hits = resultado_postos.hits.hits
        postos_coordenadas = {
            hit.source.get("posto_combustivel_id"): (
                hit.source.get("latitude"),
                hit.source.get("longitude"),
            )
            for hit in postos_hits
        }
        postos_ids = [hit.source.get("posto_combustivel_id") for hit in postos_hits]
        precos = await manticore_search_repository.search_precos_combustiveis(
            postos_ids, tipo_combustivel_id
        )
        resultados = []
        for hit in precos.hits.hits:
            posto_id = hit.source.get("posto_combustivel_id")
            posto_latitude, posto_longitude = postos_coordenadas.get(
                posto_id, (None, None)
            )
            if posto_latitude is None:
                continue

            distancia = self._calcular_distancia(
                usuario_latitude, usuario_longitude, posto_latitude, posto_longitude
            )
            hit.source["distancia_metros"] = int(distancia)
            resultados.append(hit)

        # ordenar por distância
        resultados.sort(key=lambda x: x.source.get("distancia_metros"))
        return resultados

    async def _indexar_dados(
        self, tipo_combustivel: dict, municipio_id: int, municipio_name: str, dados: list
    ):
        now = int(time.time())
        tipo_combustivel_id = tipo_combustivel.get("Id")
        tipo_combustivel_nome = tipo_combustivel.get("Descritivo")
        try:
            # 1. Indexa o tipo de combustível
            await self._upsert_tipo_combustivel(
                tipo_combustivel_id, municipio_id, tipo_combustivel_nome, now
            )
            # 2. Prepara tarefas de indexação em lote (Batching simulado via gather)
            # Para performance profissional, não usamos 'await' dentro do loop for
            tasks = []
            for item in dados:
                tasks.append(self._upsert_posto_combustivel(item, municipio_id, municipio_name, now))
                tasks.append(self._upsert_preco_combustivel(item, tipo_combustivel_id, now))

            # Executa todas as indexações em paralelo para não bloquear o processo e ser muito mais rápido
            await asyncio.gather(*tasks)
            logger.info(
                f"Sincronização de {len(dados)} registros concluída para o tipo de combustível ID: {tipo_combustivel_id} e municipio ID: {municipio_id}"
            )
        except ApiException as e:
            logger.error(f"Falha crítica na indexação: {e}")

    async def _upsert_tipo_combustivel(
        self, tipo_combustivel_id: int, municipio_id: int, nome: str, ts: int
    ):
        id=Mapper.mapear_id_multiplo(tipo_combustivel_id, municipio_id)
        entity = TipoCombustivelEntity(
            id=id,
            tipo_combustivel_id=tipo_combustivel_id,
            municipio_id=municipio_id,
            nome=nome,
            data_indexacao=ts
        )
        await manticore_search_repository.upsert_tipo_combustivel(entity)

    async def _upsert_preco_combustivel(self, item: dict, tipo_id: int, ts: int):
        id = Mapper.mapear_id_multiplo(item.get("Id"), tipo_id)
        data_atualizacao = Formatter.date_time_to_timestamp(item.get("DataAtualizacao"))
        entity = PrecoCombustivelEntity(
            id=id,
            posto_combustivel_id=item.get("Id"),
            posto_combustivel_nome=item.get("Nome"),
            tipo_combustivel_id=tipo_id,
            tipo_combustivel_nome=item.get("Combustivel"),
            preco=Formatter.str_price_to_float(item.get("Preco")),
            data_atualizacao=data_atualizacao,
            data_indexacao=ts
        )
        await manticore_search_repository.upsert_preco_combustivel(entity)

    async def _upsert_posto_combustivel(self, item: dict, municipio_id: int, municipio_name: str, ts: int):
        id=Mapper.mapear_id_multiplo(item.get("Id"), municipio_id)
        localidade = item.get("Localidade") if item.get("Localidade") is not None else municipio_name
        entity = PostoCombustivelEntity(
            id=id,
            posto_combustivel_id=item.get("Id"),
            nome=item.get("Nome"),
            marca=item.get("Marca"),
            tipo=item.get("TipoPosto"),
            distrito=item.get("Distrito"),
            municipio=municipio_name,
            morada=item.get("Morada"),
            localidade=localidade,
            cod_postal=item.get("CodPostal"),
            latitude=float(item.get("Latitude")),
            longitude=float(item.get("Longitude")),
            data_indexacao=ts
        )
        await manticore_search_repository.upsert_posto_combustivel(entity)

    def _calcular_distancia(self, lat1, lon1, lat2, lon2):
        R = 6371000  # metros
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = (
            sin(dlat / 2) ** 2
            + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
        )
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return R * c
