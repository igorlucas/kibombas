import httpx
import logging
from src.services.geolocator import GeolocatorService
from src.core.config import settings

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class DGEGService:
    def __init__(self):
        self.api_preco_combustivel_url = (
            settings.DGEG_PRECO_COMB_API_URL
        )
        self.async_client = httpx.AsyncClient()

    async def buscar_tipos_combustiveis(self):
        url = f"{self.api_preco_combustivel_url}/GetTiposCombustiveis"
        try:
            response = await self.async_client.get(f"{url}", timeout=5.0)
            data = response.json()
            if data.get("status") == True and data.get("resultado"):
                logger.warning(
                    f'{len(data.get("resultado", []))} resultados para busca de combustíveis'
                )
                return data["resultado"]
            else:
                logger.warning(
                    f"Sem resultados para busca de combustíveis"
                )
        except httpx.HTTPStatusError as e:
            return {"erro": f"Erro na API externa: {e.response.status_code}"}
        except Exception as e:
            return {"erro": f"Falha na conexão: {str(e)}"}

    async def buscar_tipo_combustivel(self, tipo_combustivel_id: int):
        try:
            tipos_combustiveis = await self.buscar_tipos_combustiveis()
            tipo_combustivel = next(
                (
                    item
                    for item in tipos_combustiveis
                    if item.get("Id") == tipo_combustivel_id
                ),
                None,
            )
            if tipo_combustivel:
                logger.warning(
                    f"Retornou busca para tipo de combustível ID: {tipo_combustivel_id}"
                )
            else:
                logger.warning(
                    f"Sem resultado para busca de combustível ID: {tipo_combustivel_id}"
                )
            return tipo_combustivel
        except httpx.HTTPStatusError as e:
            return {"erro": f"Erro na API externa: {e.response.status_code}"}
        except Exception as e:
            return {"erro": f"Falha na conexão: {str(e)}"}

    async def buscar_municipios(self):
        url = f"{self.api_preco_combustivel_url}/GetMunicipios"
        try:
            response = await self.async_client.get(f"{url}", timeout=5.0)
            data = response.json()
            if data.get("status") == True and data.get("resultado"):
                logger.warning(
                    f'{len(data.get("resultado", []))} resultados para a busca de municipios'
                )
                return data["resultado"]
            else:
                logger.warning(
                    f"Sem resultados para a busca de municipios"
                )
        except httpx.HTTPStatusError as e:
            return {"erro": f"Erro na API externa: {e.response.status_code}"}
        except Exception as e:
            return {"erro": f"Falha na conexão: {str(e)}"}
    
    async def buscar_municipio(self, latitude: float, longitude: float):
        ## TODO: Testar cenários onde não existam municipios encontrados para as coordenadas informadas.
        geolocator_service = GeolocatorService()
        address = geolocator_service.reverse_geocode(latitude, longitude)
        municipality = address.get("municipality")
        city = address.get("city")
        municipios = await self.buscar_municipios()
        municipio = next(
            (
                m
                for m in municipios
                if (
                    m["Descritivo"].lower() == city.lower()
                    or m["Descritivo"].lower() == municipality.lower()
                )
            ),
            None,
        )
        if not municipio:
            logger.warning(f"Sem resultado para a busca de municipio")
            return None
        
        logger.warning(f"Retornou busca de municipio")
        return municipio

    async def buscar_preco_combustiveis(
        self, tipo_combustivel_id: int, distrito_id: int, municipio_id: int
    ):
        url = f"{self.api_preco_combustivel_url}/PesquisarPostos"
        resultados = []
        pagina = 1
        logger.warning(
            f"Buscando preços dos postos para o tipo de combustível: {tipo_combustivel_id}, distrito: {distrito_id} e municipio: {municipio_id}"
        )
        try:
            while True:
                response = await self.async_client.get(
                    f"{url}?idsTiposComb={tipo_combustivel_id}&idDistrito={distrito_id}&idsMunicipios={municipio_id}&qtdPorPagina=50&pagina={pagina}",
                    timeout=5.0,
                )
                data = response.json()
                if data.get("status") == True and data.get("resultado"):
                    logger.warning(
                        f'Página: {pagina}, Resultados: {len(data.get("resultado", []))}'
                    )
                    resultados.extend(data["resultado"])
                    pagina += 1
                else:
                    logger.warning(f"Sem mais resultados")
                    break
            logger.warning(
                f"Total de resultados para o tipo de combustivel: {tipo_combustivel_id}, distrito: {distrito_id} e municipio: {municipio_id} é {len(resultados)}"
            )
            return resultados
        except httpx.HTTPStatusError as e:
            return {"erro": f"Erro na API externa: {e.response.status_code}"}
        except Exception as e:
            return {"erro": f"Falha na conexão: {str(e)}"}
