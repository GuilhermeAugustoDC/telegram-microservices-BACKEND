import re


def validate_telegram_chat_id(chat_id: str) -> bool:
    """Valida formato de ID de chat do Telegram"""
    return chat_id.startswith("-100") and chat_id[4:].isdigit()


def validate_phone_number(phone: str) -> bool:
    """Valida número de telefone internacional"""
    pattern = r"^\+[1-9]\d{1,14}$"
    return bool(re.match(pattern, phone))


def sanitize_filename(filename: str) -> str:
    """Remove caracteres inválidos de nomes de arquivo"""
    return re.sub(r'[<>:"/\\|?*]', "_", filename)


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
