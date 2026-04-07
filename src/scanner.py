import os
import imagehash
import fitz

from PIL import Image


def get_hashes_with_rotations(img):
    """Возвращает список из 4 хешей: оригинал и 3 поворота (90, 180, 270 градусов)."""
    return [
        imagehash.phash(img),
        imagehash.phash(img.rotate(90, expand=True)),
        imagehash.phash(img.rotate(180, expand=True)),
        imagehash.phash(img.rotate(270, expand=True))
    ]


def get_image_data(path):
    """Извлекает данные. Сохраняет сразу 4 хэша (с учетом поворотов)."""
    results = []
    ext = os.path.splitext(path)[1].lower()
    
    if ext == '.pdf':
        try:
            doc = fitz.open(path)
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                pix = page.get_pixmap(dpi=150)
                
                mode = "RGBA" if pix.alpha else "RGB"
                img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
                
                results.append({
                    'path': path,
                    'hashes': get_hashes_with_rotations(img),
                    'pixels': pix.width * pix.height,
                    'page': page_num + 1 
                })
            doc.close()
        except Exception:
            pass
    else:
        try:
            with Image.open(path) as img:
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                    
                results.append({
                    'path': path,
                    'hashes': get_hashes_with_rotations(img),
                    'pixels': img.width * img.height,
                    'page': None
                })
        except Exception:
            pass
            
    return results


def find_duplicates(image_paths, tolerance=5):
    hashes_dict = {}
    
    for path in image_paths:
        data_list = get_image_data(path)
        for data in data_list:
            key = f"{data['path']} (Стр. {data['page']})" if data['page'] else data['path']
            hashes_dict[key] = data['hashes']

    duplicates_groups = []
    visited = set()
    valid_keys = list(hashes_dict.keys())
    
    for i in range(len(valid_keys)):
        key1 = valid_keys[i]
        if key1 in visited: continue
            
        current_group = [key1]
        hashes1 = hashes_dict[key1]
        
        for j in range(i + 1, len(valid_keys)):
            key2 = valid_keys[j]
            if key2 in visited: continue
                
            hashes2 = hashes_dict[key2]
            
            is_match = False
            for h1 in hashes1:
                for h2 in hashes2:
                    if h1 - h2 <= tolerance:
                        is_match = True
                        break
                if is_match: break
            
            if is_match:
                current_group.append(key2)
                visited.add(key2)
        
        if len(current_group) > 1:
            duplicates_groups.append(current_group)
            
    return duplicates_groups


def find_originals(low_res_paths, high_res_paths, tolerance=5):
    server_data = []
    for path in high_res_paths:
        server_data.extend(get_image_data(path))

    results = {'found': [], 'not_found': []}

    for low_path in low_res_paths:
        low_data_list = get_image_data(low_path)
        if not low_data_list:
            results['not_found'].append(low_path)
            continue
            
        low_hashes = low_data_list[0]['hashes']
        
        best_match_path = None
        best_match_page = None # ДОБАВЛЕНО: переменная для хранения номера страницы
        max_pixels = -1
        
        for s_data in server_data:
            # Проверяем совпадение хотя бы по одному из ракурсов
            is_match = False
            for lh in low_hashes:
                for sh in s_data['hashes']:
                    if lh - sh <= tolerance:
                        is_match = True
                        break
                if is_match: break
            
            # Если нашли совпадение в любом из ракурсов
            if is_match:
                if s_data['pixels'] > max_pixels:
                    max_pixels = s_data['pixels']
                    best_match_path = s_data['path'] 
                    best_match_page = s_data['page'] # ДОБАВЛЕНО: запоминаем страницу
        
        if best_match_path:
            # ДОБАВЛЕНО: теперь мы передаем 3 значения (включая страницу)
            results['found'].append((low_path, best_match_path, best_match_page))
        else:
            results['not_found'].append(low_path)

    return results