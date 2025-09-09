from app.config.config import settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import uvicorn
from app.models.database import create_tables
from app.api.routes import automations, sessions, channels, logs

import logging

logging.basicConfig(
    level=logging.INFO,  # Mostra INFO, WARNING e ERROR
    format="%(asctime)s [%(levelname)s] %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    print("Startup complete. Database tables created.")
    yield
    print("Shutdown complete.")


app = FastAPI(
    title="Telegram Automation API",
    description="API para automação de encaminhamento de mensagens do Telegram",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(
    "/app/static",
    StaticFiles(directory=settings.PHOTO_GROUP_DIR),
    name="static",
)

# Inclui os roteadores
app.include_router(automations.router, prefix="/api", tags=["Automations"])
app.include_router(sessions.router, prefix="/api", tags=["Sessions"])
app.include_router(channels.router, prefix="/api", tags=["Channels"])
app.include_router(logs.router, prefix="/api", tags=["Logs"])

if __name__ == "__main__":
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
