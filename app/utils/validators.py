import re


"""Valida formato do ID do chat do Telegram"""


def validate_telegram_chat_id(chat_id: str) -> bool:
    return chat_id.startswith("-100") and chat_id[4:].isdigit()


"""Valida número de telefone internacional"""


def validate_phone_number(phone: str) -> bool:
    pattern = r"^\+[1-9]\d{1,14}$"
    return bool(re.match(pattern, phone))


"""Remove caracteres inválidos de nomes de arquivo"""


def sanitize_filename(filename: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', "_", filename)


"""Formata tamanho de arquivo em formato legível"""


def format_file_size(size_bytes: int) -> bool:
    if size_bytes == 0:
        return "0B"
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.1f}{size_names[i]}"
