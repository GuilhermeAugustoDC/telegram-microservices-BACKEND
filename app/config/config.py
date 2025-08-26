import os
from dotenv import load_dotenv
from pathlib import Path

# Carrega as variáveis de ambiente do arquivo .env na raiz do backend
load_dotenv()


class Settings:
    # Configurações da API
    API_TITLE = "Telegram Automation API"
    API_DESCRIPTION = "API para automação de encaminhamento de mensagens do Telegram"
    API_VERSION = "1.0.0"

    # Configurações do servidor
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", 8000))
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    HOST_AND_PORT = f"{HOST}:{PORT}"
    
    # Configurações do Telegram
    API_ID = os.getenv("API_ID")
    API_HASH = os.getenv("API_HASH")
    SESSION_EXTENSION_FILE = os.getenv("SESSION_EXTENSION_FILE", ".session")

    # Diretórios
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATABASE_DIR = BASE_DIR / "databases"
    SESSIONS_DIR = BASE_DIR / "sessions"
    PHOTO_GROUP_DIR = BASE_DIR / "static"

    # Cria os diretórios se não existirem
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    PHOTO_GROUP_DIR.mkdir(parents=True, exist_ok=True)

    # Configurações do banco de dados
    DATABASE_URL = os.getenv(
        "DATABASE_URL", f"sqlite:///{DATABASE_DIR / 'telegram_automation.db'}"
    )


# Instância de configuração
settings = Settings()
