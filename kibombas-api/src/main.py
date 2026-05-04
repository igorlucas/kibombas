import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.db.manticore_search import ManticoreSearchRepository
from src import routes
from src.core.config import settings


manticore_repo = ManticoreSearchRepository()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # O que acontece antes da API começar a receber requisições
    retries = 5
    while retries > 0:
        try:
            await manticore_repo.initialize_schema()
            break
        except Exception:
            retries -= 1
            print(f"Manticore not ready, retrying... ({retries} left)")
            await asyncio.sleep(5)
    
    yield
    # O que acontece quando a API está sendo desligada
    
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)
app.include_router(routes.router)