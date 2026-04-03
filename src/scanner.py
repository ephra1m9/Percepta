import imagehash

from PIL import Image


def find_duplicates(image_paths, tolerance=5):
    """Принимает список путей к изображениям, вычисляет их хеши и группирует похожие."""
    hashes = {}

    for path in image_paths:
        try:
            with Image.open(path) as img:
                hashes[path] = imagehash.phash(img)
        except Exception as e:
            print(f"Ошибка чтения файла {path}: {e}")
            continue

    duplicates_groups = []
    visited = set() # пути картинок, которые уже попали в дубликаты
    valid_paths = list(hashes.keys()) # список всех успешно прочитанных файлов

    for i in range(len(valid_paths)):
        path1 = valid_paths[i]

        if path1 in visited:
            continue

        current_group = [path1]
        hash1 = hashes[path1]

        for j in range(i + 1, len(valid_paths)):
            path2 = valid_paths[j]

            if path2 in visited:
                continue

            hash2 = hashes[path2]

            if hash1 - hash2 <= tolerance:
                current_group.append(path2)
                visited.add(path2)

        if len(current_group) > 1:
            duplicates_groups.append(current_group)

    return duplicates_groups