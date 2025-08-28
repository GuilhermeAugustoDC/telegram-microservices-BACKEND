# Pasta app/utils

Utilitários e funções auxiliares genéricas que podem ser reutilizadas em todo o projeto. Não contém lógica de negócio específica.

## Estrutura Atual
- **logger.py**: (Exemplo) Sistema de logging customizado

## Tipos de Utilitários

### 1. Validações e Formatação
```python
# utils/validators.py
import re
from typing import Optional

def validate_telegram_chat_id(chat_id: str) -> bool:
    """Valida formato de ID de chat do Telegram"""
    return chat_id.startswith('-100') and chat_id[4:].isdigit()

def validate_phone_number(phone: str) -> bool:
    """Valida número de telefone internacional"""
    pattern = r'^\+[1-9]\d{1,14}$'
    return bool(re.match(pattern, phone))

def sanitize_filename(filename: str) -> str:
    """Remove caracteres inválidos de nomes de arquivo"""
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def format_file_size(size_bytes: int) -> str:
    """Formata tamanho de arquivo em formato legível"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"
```

### 2. Criptografia e Segurança
```python
# utils/security.py
import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
from app.config.config import settings

def generate_api_key(length: int = 32) -> str:
    """Gera chave de API aleatória"""
    return secrets.token_urlsafe(length)

def hash_string(text: str, salt: str = None) -> str:
    """Gera hash SHA-256 de uma string"""
    if salt:
        text = f"{text}{salt}"
    return hashlib.sha256(text.encode()).hexdigest()

def create_jwt_token(data: dict, expires_hours: int = 24) -> str:
    """Cria token JWT"""
    expire = datetime.utcnow() + timedelta(hours=expires_hours)
    data.update({"exp": expire})
    return jwt.encode(data, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def verify_jwt_token(token: str) -> dict:
    """Verifica e decodifica token JWT"""
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise ValueError("Token expirado")
    except jwt.InvalidTokenError:
        raise ValueError("Token inválido")
```

### 3. Manipulação de Datas e Tempo
```python
# utils/datetime_helpers.py
from datetime import datetime, timezone, timedelta
from typing import Optional

def utc_now() -> datetime:
    """Retorna datetime UTC atual"""
    return datetime.now(timezone.utc)

def to_utc(dt: datetime) -> datetime:
    """Converte datetime para UTC"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def format_duration(seconds: int) -> str:
    """Formata duração em segundos para formato legível"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}m {secs}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"

def parse_date_range(date_str: str) -> tuple[datetime, datetime]:
    """Parse string de data para range (ex: '2024-01-01,2024-01-31')"""
    try:
        start_str, end_str = date_str.split(',')
        start_date = datetime.fromisoformat(start_str.strip())
        end_date = datetime.fromisoformat(end_str.strip())
        return start_date, end_date
    except ValueError:
        raise ValueError("Formato de data inválido. Use: YYYY-MM-DD,YYYY-MM-DD")
```

### 4. Manipulação de Arquivos
```python
# utils/file_helpers.py
import os
import shutil
from pathlib import Path
from typing import List, Optional

def ensure_directory(path: str) -> None:
    """Garante que diretório existe, criando se necessário"""
    Path(path).mkdir(parents=True, exist_ok=True)

def get_file_extension(filename: str) -> str:
    """Retorna extensão do arquivo"""
    return Path(filename).suffix.lower()

def is_image_file(filename: str) -> bool:
    """Verifica se arquivo é uma imagem"""
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    return get_file_extension(filename) in image_extensions

def clean_old_files(directory: str, days_old: int = 7) -> int:
    """Remove arquivos mais antigos que N dias"""
    if not os.path.exists(directory):
        return 0
    
    cutoff_time = datetime.now() - timedelta(days=days_old)
    removed_count = 0
    
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            if file_time < cutoff_time:
                os.remove(file_path)
                removed_count += 1
    
    return removed_count
```

### 5. Rate Limiting e Throttling
```python
# utils/rate_limiter.py
import time
from collections import defaultdict, deque
from typing import Dict, Deque

class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, Deque[float]] = defaultdict(deque)
    
    def is_allowed(self, identifier: str) -> bool:
        """Verifica se requisição é permitida para o identificador"""
        now = time.time()
        user_requests = self.requests[identifier]
        
        # Remove requisições antigas
        while user_requests and user_requests[0] <= now - self.window_seconds:
            user_requests.popleft()
        
        # Verifica limite
        if len(user_requests) >= self.max_requests:
            return False
        
        # Adiciona requisição atual
        user_requests.append(now)
        return True
    
    def get_reset_time(self, identifier: str) -> float:
        """Retorna quando o limite será resetado"""
        user_requests = self.requests[identifier]
        if not user_requests:
            return 0
        return user_requests[0] + self.window_seconds
```

### 6. Logging Customizado
```python
# utils/logger.py
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from app.config.config import settings

def setup_logger(name: str, log_file: str = None) -> logging.Logger:
    """Configura logger customizado"""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (se especificado)
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def log_function_call(func):
    """Decorator para logar chamadas de função"""
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        logger.info(f"Chamando {func.__name__} com args={args}, kwargs={kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.info(f"{func.__name__} executado com sucesso")
            return result
        except Exception as e:
            logger.error(f"Erro em {func.__name__}: {e}")
            raise
    return wrapper
```

### 7. Helpers de API
```python
# utils/api_helpers.py
from fastapi import HTTPException, status
from typing import Any, Dict, Optional

def create_response(data: Any = None, message: str = "Success", status_code: int = 200) -> Dict:
    """Cria resposta padronizada da API"""
    response = {
        "success": status_code < 400,
        "message": message,
        "status_code": status_code
    }
    
    if data is not None:
        response["data"] = data
    
    return response

def raise_http_error(status_code: int, message: str, details: Optional[Dict] = None):
    """Levanta HTTPException padronizada"""
    error_detail = {"message": message}
    if details:
        error_detail.update(details)
    
    raise HTTPException(status_code=status_code, detail=error_detail)

def paginate_query(query, page: int = 1, per_page: int = 20):
    """Adiciona paginação a query SQLAlchemy"""
    if page < 1:
        page = 1
    if per_page < 1 or per_page > 100:
        per_page = 20
    
    offset = (page - 1) * per_page
    return query.offset(offset).limit(per_page)
```

## Organização de Arquivos
```
utils/
├── __init__.py
├── validators.py        # Validações e formatação
├── security.py          # Criptografia e segurança
├── datetime_helpers.py  # Manipulação de datas
├── file_helpers.py      # Operações com arquivos
├── rate_limiter.py      # Rate limiting
├── logger.py            # Sistema de logging
├── api_helpers.py       # Helpers para API
└── decorators.py        # Decorators reutilizáveis
```

## Boas Práticas
1. **Funções puras**: Utilitários devem ser funções puras quando possível
2. **Type hints**: Sempre use type hints para documentação
3. **Docstrings**: Documente o propósito e uso de cada função
4. **Testes unitários**: Utilitários devem ser bem testados
5. **Sem dependências externas**: Minimize dependências específicas
6. **Reutilização**: Foque em funcionalidades que serão usadas em múltiplos lugares
7. **Performance**: Considere performance para funções chamadas frequentemente
8. **Tratamento de erros**: Trate casos edge e erros apropriadamente
