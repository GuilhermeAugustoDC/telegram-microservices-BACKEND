# utils/file_helpers.py
import os
from datetime import datetime, timedelta
from pathlib import Path


def ensure_directory(path: str) -> None:
    """Garante que diretório existe, criando se necessário"""
    Path(path).mkdir(parents=True, exist_ok=True)


def verify_directory_exist(directory: str) -> bool:
    """Verifica se o diretório existe"""
    return os.path.exists(path=directory)


def get_file_extension(filename: str) -> str:
    """Retorna extensão do arquivo"""
    return Path(filename).suffix.lower()


def is_image_file(filename: str) -> bool:
    """Verifica se arquivo é uma imagem"""
    image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
    return get_file_extension(filename) in image_extensions


def is_video_file(filename: str) -> bool:
    """Verifica se arquivo é um vídeo"""
    video_extensions = {
        ".mp4",
        ".avi",
        ".mov",
        ".wmv",
        ".flv",
        ".mkv",
        ".webm",
        ".mpeg",
        ".mpg",
    }
    os.path.exists()
    return get_file_extension(filename) in video_extensions


def remove_file(file_path: str) -> bool:
    """Remove arquivo se existir"""
    if not os.path.exists(file_path):
        return False
    os.remove(file_path)
    return True


def clean_old_files(directory: str, days_old: int = 7) -> int:
    """Remove arquivos mais antigos que N dias"""
    if verify_directory_exist(directory):
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
