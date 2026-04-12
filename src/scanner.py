import os
import cv2
import numpy as np
import fitz
import re
import imagehash
from PIL import Image

# Инициализируем OpenCV с ограничением в 500 точек (хватит для ретуши)
orb = cv2.ORB_create(nfeatures=500)
bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)

def get_hashes_with_rotations(img):
    """Быстрый глобальный хеш"""
    return [
        imagehash.phash(img),
        imagehash.phash(img.rotate(90, expand=True)),
        imagehash.phash(img.rotate(180, expand=True)),
        imagehash.phash(img.rotate(270, expand=True))
    ]

def get_image_data(path):
    """Оптимизированное чтение: ресайз до 500px перед анализом точек"""
    results = []
    ext = os.path.splitext(path)[1].lower()
    
    try: file_size = os.path.getsize(path)
    except Exception: file_size = 0
        
    try:
        if ext == '.pdf':
            doc = fitz.open(path)
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                pix = page.get_pixmap(dpi=72) # Низкий DPI для скорости поиска
                img_pil = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                results.append(process_image_logic(img_pil, path, file_size, page_num + 1))
            doc.close()
        else:
            with Image.open(path) as img:
                if img.mode in ('RGBA', 'P'): img = img.convert('RGB')
                results.append(process_image_logic(img, path, file_size, None))
    except Exception:
        pass
    return results

def process_image_logic(img_pil, path, file_size, page_num):
    """Ядро анализа: делаем превью 500px для OpenCV, чтобы не греть CPU"""
    # 1. pHash (делаем на оригинальном превью)
    hashes = get_hashes_with_rotations(img_pil)
    
    # 2. OpenCV (делаем на ОЧЕНЬ маленькой копии)
    img_mini = img_pil.copy()
    img_mini.thumbnail((500, 500)) 
    img_cv = cv2.cvtColor(np.array(img_mini), cv2.COLOR_RGB2GRAY)
    
    kp, des = orb.detectAndCompute(img_cv, None)
    
    return {
        'path': path,
        'hashes': hashes,
        'descriptors': des,
        'pixels': img_pil.width * img_pil.height,
        'size': file_size,
        'page': page_num
    }

def are_images_matching(des1, des2, min_matches=25, lowe_ratio=0.65):
    """Улучшенное сравнение с более строгими параметрами"""
    if des1 is None or des2 is None or len(des1) < 15 or len(des2) < 15:
        return False
    try:
        matches = bf.knnMatch(des1, des2, k=2)
        # Более строгий коэффициент Лоу (0.65 вместо 0.7)
        good_matches = []
        for m_n in matches:
            if len(m_n) == 2:
                m, n = m_n
                if m.distance < lowe_ratio * n.distance:
                    good_matches.append(m)
        
        # Дополнительная проверка: минимум 30% matches от минимального количества дескрипторов
        min_descriptors = min(len(des1), len(des2))
        ratio_ok = len(good_matches) >= min_descriptors * 0.3
        
        return len(good_matches) >= min_matches and ratio_ok
    except:
        return False

def find_duplicates(image_paths, tolerance=15):
    """Поиск дубликатов СТРОГО по pHash (как и должно быть)"""
    phash_tolerance = max(1, tolerance // 3)
    data_cache = {}
    
    for path in image_paths:
        for data in get_image_data(path):
            key = f"{data['path']}_{data['page']}"
            data_cache[key] = data

    groups = []
    visited = set()
    keys = list(data_cache.keys())
    
    for i, k1 in enumerate(keys):
        if k1 in visited: continue
        group = [data_cache[k1]['path']]
        for k2 in keys[i+1:]:
            if k2 in visited: continue
            # Сравниваем ТОЛЬКО хеши (быстро и точно для дубликатов)
            if any(h1 - h2 <= phash_tolerance for h1 in data_cache[k1]['hashes'] for h2 in data_cache[k2]['hashes']):
                group.append(data_cache[k2]['path'])
                visited.add(k2)
        if len(group) > 1: groups.append(group)
    return groups

def find_originals(low_res_paths, high_res_paths, tolerance=20, phash_threshold=None, quality_ratio=None):
    """Поиск оригиналов: гибридный подход pHash + ORB + проверка качества"""
    results = {'found': [], 'not_found': []}
    
    def clean_name(p):
        return re.sub(r'(_original|_edit|_retouch|-copy|\(\d+\))$', '',
                      os.path.splitext(os.path.basename(p))[0].lower()).strip()

    # Кэширование данных изображений
    cache = {}
    def get_cached(p):
        if p not in cache:
            cache[p] = get_image_data(p)
        return cache[p]
    
    # Настраиваемые параметры (значения по умолчанию)
    if phash_threshold is None:
        phash_threshold = 10  # Максимальная разница pHash (0-64)
    if quality_ratio is None:
        quality_ratio = 1.2  # Оригинал должен быть минимум на 20% лучше
    
    orb_min_matches = max(25, tolerance)  # Минимум совпадений ORB
    
    # Предварительная обработка high-res файлов для быстрого поиска по имени
    high_res_map = {}
    for p in high_res_paths:
        name = clean_name(p)
        if name not in high_res_map:
            high_res_map[name] = []
        high_res_map[name].append(p)

    for lp in low_res_paths:
        l_data_list = get_cached(lp)
        if not l_data_list:
            results['not_found'].append(lp)
            continue
            
        l_data = l_data_list[0]
        found = False
        name = clean_name(lp)
        
        # Список кандидатов для проверки (приоритет: совпадение по имени)
        candidates = []
        if name in high_res_map:
            candidates.extend(high_res_map[name])
        
        # Добавляем остальные файлы если не нашли по имени
        if not candidates:
            candidates = high_res_paths
        
        for hp in candidates:
            for h_data in get_cached(hp):
                # Шаг 1: Быстрая фильтрация по pHash
                phash_match = any(
                    h1 - h2 <= phash_threshold
                    for h1 in l_data['hashes']
                    for h2 in h_data['hashes']
                )
                
                if not phash_match:
                    continue
                
                # Шаг 2: Более точная проверка ORB
                if not are_images_matching(
                    l_data['descriptors'],
                    h_data['descriptors'],
                    min_matches=orb_min_matches
                ):
                    continue
                
                # Шаг 3: Проверка что оригинал действительно лучше
                # Проверяем по размеру файла ИЛИ по разрешению
                size_ok = h_data['size'] >= l_data['size'] * quality_ratio
                resolution_ok = h_data['pixels'] >= l_data['pixels'] * quality_ratio
                
                if size_ok or resolution_ok:
                    results['found'].append((lp, h_data['path'], h_data['page']))
                    found = True
                    break
            
            if found:
                break
        
        if not found:
            results['not_found'].append(lp)
    
    return results