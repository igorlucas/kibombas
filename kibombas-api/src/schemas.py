from datetime import datetime
from typing import List
from pydantic import BaseModel

class PrecoCombustivel(BaseModel):
    id: int
    posto_combustivel: str
    tipo_combustivel: str
    preco: float
    distancia: int
    data_atualizacao: datetime

class BuscarPrecoCombustivelRequest(BaseModel):
    tipo_combustivel_id: int
    latitude: float
    longitude: float


class BuscarPrecoCombustivelResponse(BaseModel):
    mensagem: str
    resultado: List[PrecoCombustivel]


