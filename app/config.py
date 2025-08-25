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
    
    # Configurações do banco de dados
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///telegram-micro-services/backend/telegram_automation.db")

    # Configurações do servidor
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # Configurações do Telegram
    API_ID = os.getenv("API_ID")
    API_HASH = os.getenv("API_HASH")
    
    # Diretórios
    BASE_DIR = Path(__file__).resolve().parent.parent
    SESSIONS_DIR = BASE_DIR / "sessions"
    
    # Cria o diretório de sessões se não existir
    SESSIONS_DIR.mkdir(exist_ok=True)

# Instância de configuração
settings = Settings()
