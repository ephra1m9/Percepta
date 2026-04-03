from PIL import Image
import imagehash
import fitz  # PyMuPDF для работы с PDF
import os

def get_image_data(path):
    """
    Универсальная функция извлечения данных.
    Для обычных картинок возвращает 1 хеш.
    Для PDF рендерит каждую страницу и возвращает хеши всех страниц.
    """
    results = []
    ext = os.path.splitext(path)[1].lower()
    
    if ext == '.pdf':
        try:
            # Открываем PDF-файл
            doc = fitz.open(path)
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                # Рендерим страницу (DPI=150 достаточно для точного хеша)
                pix = page.get_pixmap(dpi=150)
                
                # Конвертируем сырые пиксели из PDF в формат Pillow
                mode = "RGBA" if pix.alpha else "RGB"
                img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
                
                results.append({
                    'path': path,
                    'hash': imagehash.phash(img),
                    'pixels': pix.width * pix.height,
                    'page': page_num + 1 # Запоминаем номер страницы
                })
            doc.close()
        except Exception:
            pass
    else:
        try:
            with Image.open(path) as img:
                # Убираем альфа-канал, если он есть, чтобы phash работал корректно
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                    
                results.append({
                    'path': path,
                    'hash': imagehash.phash(img),
                    'pixels': img.width * img.height,
                    'page': None
                })
        except Exception:
            pass
            
    return results


def find_duplicates(image_paths, tolerance=5):
    hashes = {}
    
    # 1. Собираем данные со всех файлов (включая страницы PDF)
    for path in image_paths:
        data_list = get_image_data(path)
        for data in data_list:
            # Если это страница PDF, добавляем номер страницы к имени, чтобы различать их в логах
            key = f"{data['path']} (Стр. {data['page']})" if data['page'] else data['path']
            hashes[key] = data['hash']

    duplicates_groups = []
    visited = set()
    valid_keys = list(hashes.keys())
    
    # 2. Ищем дубликаты
    for i in range(len(valid_keys)):
        key1 = valid_keys[i]
        if key1 in visited: continue
            
        current_group = [key1]
        hash1 = hashes[key1]
        
        for j in range(i + 1, len(valid_keys)):
            key2 = valid_keys[j]
            if key2 in visited: continue
                
            hash2 = hashes[key2]
            if hash1 - hash2 <= tolerance:
                current_group.append(key2)
                visited.add(key2)
        
        if len(current_group) > 1:
            duplicates_groups.append(current_group)
            
    return duplicates_groups


def find_originals(low_res_paths, high_res_paths, tolerance=5):
    # 1. Собираем данные всех картинок и страниц PDF на сервере
    server_data = []
    for path in high_res_paths:
        server_data.extend(get_image_data(path))

    results = {'found': [], 'not_found': []}

    # 2. Ищем совпадения для превьюшек
    for low_path in low_res_paths:
        low_data_list = get_image_data(low_path)
        if not low_data_list:
            results['not_found'].append(low_path)
            continue
            
        # Обычно превьюшка - это одна картинка (не PDF), берем её хеш
        low_hash = low_data_list[0]['hash']
        
        best_match_path = None
        max_pixels = -1
        
        # Сравниваем со всеми страницами/картинками на сервере
        for s_data in server_data:
            if low_hash - s_data['hash'] <= tolerance:
                # Если нашли совпадение, ищем самое крупное разрешение
                if s_data['pixels'] > max_pixels:
                    max_pixels = s_data['pixels']
                    best_match_path = s_data['path'] # Забираем путь к самому файлу!
        
        if best_match_path:
            # Даже если совпадение нашлось на 5-й странице многостраничного PDF,
            # мы возвращаем путь к самому файлу PDF, чтобы скопировать его целиком.
            results['found'].append((low_path, best_match_path))
        else:
            results['not_found'].append(low_path)

    return results