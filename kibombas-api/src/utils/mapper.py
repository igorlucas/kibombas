from datetime import datetime
import hashlib
from typing import List
from manticoresearch import HitsHits
from src.schemas import BuscarPrecoCombustivelResponse, PrecoCombustivel

class Mapper:

    @staticmethod
    def mapear_preco_combustivel_response(
        hits: List[HitsHits] | None,
    ) -> BuscarPrecoCombustivelResponse:
        if None or not hits:
            return BuscarPrecoCombustivelResponse(
                mensagem="Sem resultados para a busca dos preços de combustiveis.",
                resultado=[],
            )

        lista_preco_combustivel: List[PrecoCombustivel] = []
        for hit in hits:
            item = PrecoCombustivel(
                id=hit.id,
                posto_combustivel=hit.source.get("posto_combustivel_nome"),
                tipo_combustivel=hit.source.get("tipo_combustivel_nome"),
                preco=hit.source.get("preco"),
                distancia=hit.source.get("distancia_metros"),
                data_atualizacao=datetime.fromtimestamp(hit.source.get("data_atualizacao")),
            )
            lista_preco_combustivel.append(item)

        return BuscarPrecoCombustivelResponse(
            mensagem="Busca dos preços de combustiveis realizada com sucesso.",
            resultado=lista_preco_combustivel,
        )

    @staticmethod
    def mapear_id_multiplo(*keys: any) -> int:
        # Gerar um ID único a partir de múltiplas chaves usando hashing
        identifier = ":".join(str(k) for k in keys)
        # Manticore usa 64-bit tipo inteiro para IDs
        hash_hex = hashlib.sha256(identifier.encode()).hexdigest()
        # Obtem os primeiros 15 caracteres para garantir que caiba em um inteiro de 64 bits
        return int(hash_hex[:15], 16)