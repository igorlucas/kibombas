from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from src.core.config import settings
from src.schemas import BuscarPrecoCombustivelRequest
from src.services.manticore_search import ManticoreService

manticore_service = ManticoreService()
router = APIRouter()

@router.get("/", response_class=HTMLResponse)
def home():
    return f"<h1>Servidor {settings.PROJECT_NAME} em execução!</h1>"

@router.post("/api/combustiveis/precos")
async def buscar_precos_combustiveis(req: BuscarPrecoCombustivelRequest):
    return await manticore_service.buscar_precos_postos_combustiveis(
        req.tipo_combustivel_id, req.latitude, req.longitude
    )
    