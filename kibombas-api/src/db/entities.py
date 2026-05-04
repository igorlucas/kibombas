from pydantic import BaseModel

class TipoCombustivelEntity(BaseModel):
    id: int
    tipo_combustivel_id: int
    municipio_id: int
    nome: str
    data_indexacao: int

class PostoCombustivelEntity(BaseModel):
    id: int
    posto_combustivel_id: int
    nome: str
    marca: str
    tipo: str
    distrito: str
    municipio: str
    morada: str
    localidade: str
    cod_postal: str
    latitude: float
    longitude: float
    data_indexacao: int

class PrecoCombustivelEntity(BaseModel):
    id: int
    posto_combustivel_id: int
    posto_combustivel_nome: str
    tipo_combustivel_id: int
    tipo_combustivel_nome: str
    preco: float
    data_atualizacao: int
    data_indexacao: int