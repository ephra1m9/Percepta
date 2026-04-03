import pathlib

from .config import VALID_EXTENSIONS


def get_image_files(directory_path):
    """Проходит по указанной папке (включая вложенные) и возвращает список путей ко всем картинкам."""
    image_paths = []
    path = pathlib.Path(directory_path)

    if not path.exists() or not path.is_dir():
        return image_paths
    
    for file_path in path.rglob('*'):
        if file_path.is_file() and file_path.suffix.lower() in VALID_EXTENSIONS:
            image_paths.append(str(file_path.absolute()))

    return image_paths