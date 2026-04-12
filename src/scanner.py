import os
import cv2
import numpy as np
import fitz
import re
import imagehash
from PIL import Image
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Инициализируем OpenCV с ограничением в 800 точек
orb = cv2.ORB_create(nfeatures=800)
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


def find_reference_matches(reference_paths, search_paths, tolerance=15):
    """
    Улучшенный поиск по эталону: находит изображения из search_paths, которые совпадают с reference_paths.
    Использует комбинированный подход: pHash + гистограммы + ORB для лучшего обнаружения
    отретушированных и кадрированных изображений.
    """
    logger.info(f"Улучшенный поиск по эталону: {len(reference_paths)} эталонов, {len(search_paths)} для поиска")
    
    # Кэшируем данные для всех файлов
    data_cache = {}
    all_paths = reference_paths + search_paths
    
    for path in all_paths:
        for data in get_image_data(path):
            key = f"{data['path']}_{data['page']}"
            data_cache[key] = data
    
    # Группируем по reference/search
    ref_keys = [k for k in data_cache.keys() if data_cache[k]['path'] in reference_paths]
    search_keys = [k for k in data_cache.keys() if data_cache[k]['path'] in search_paths]
    
    matches = []
    matched_search = set()
    
    # Увеличиваем порог pHash для ретушированных изображений
    phash_tolerance = tolerance  # Увеличили с tolerance//3 до tolerance
    histogram_threshold = 0.70
    
    logger.info(f"Параметры поиска: pHash tolerance={phash_tolerance}, histogram threshold={histogram_threshold}")
    
    for ref_key in ref_keys:
        ref_data = data_cache[ref_key]
        
        for search_key in search_keys:
            if search_key in matched_search:
                continue
                
            search_data = data_cache[search_key]
            
            # 1. Проверка pHash с увеличенным порогом
            phash_match = False
            min_hash_diff = 100
            for h1 in ref_data['hashes']:
                for h2 in search_data['hashes']:
                    diff = h1 - h2
                    if diff < min_hash_diff:
                        min_hash_diff = diff
            
            if min_hash_diff <= phash_tolerance:
                phash_match = True
                logger.debug(f"pHash совпадение: {os.path.basename(ref_data['path'])} <-> {os.path.basename(search_data['path'])} diff={min_hash_diff}")
            
            # 2. Проверка гистограмм (для ретушированных изображений)
            hist_match = False
            if not phash_match:
                hist_similarity = compare_histograms(ref_data['histograms'], search_data['histograms'])
                if hist_similarity >= histogram_threshold:
                    hist_match = True
                    logger.debug(f"Гистограмма совпадение: {os.path.basename(ref_data['path'])} <-> {os.path.basename(search_data['path'])} similarity={hist_similarity:.3f}")
            
            # 3. Проверка ORB (для кадрированных изображений)
            orb_match = False
            if not phash_match and not hist_match:
                des1 = ref_data['descriptors']
                des2 = search_data['descriptors']
                
                if des1 is not None and des2 is not None and len(des1) > 10 and len(des2) > 10:
                    # Мягкие параметры для кадрированных изображений
                    min_des_len = min(len(des1), len(des2))
                    dynamic_min_matches = max(10, int(min_des_len * 0.15))
                    
                    orb_match = are_images_matching(
                        des1, des2,
                        min_matches=dynamic_min_matches,
                        lowe_ratio=0.7,
                        ratio_threshold=0.10,
                        debug_info=None
                    )
                    if orb_match:
                        logger.debug(f"ORB совпадение: {os.path.basename(ref_data['path'])} <-> {os.path.basename(search_data['path'])}")
            
            # Если хотя бы один метод показал совпадение
            if phash_match or hist_match or orb_match:
                matches.append([ref_data['path'], search_data['path']])
                matched_search.add(search_key)
                logger.info(f"Найдено совпадение: {os.path.basename(ref_data['path'])} -> {os.path.basename(search_data['path'])}")
    
    logger.info(f"Найдено {len(matches)} совпадений по эталону")
    return matches

def process_image_logic(img_pil, path, file_size, page_num):
    """Ядро анализа: делаем превью 800px для OpenCV + гистограммы"""
    # 1. pHash (делаем на оригинальном превью)
    hashes = get_hashes_with_rotations(img_pil)
    
    # 2. Цветовые гистограммы (HSV)
    img_hsv = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2HSV)
    hist_h = cv2.calcHist([img_hsv], [0], None, [16], [0, 180])
    hist_s = cv2.calcHist([img_hsv], [1], None, [16], [0, 256])
    hist_v = cv2.calcHist([img_hsv], [2], None, [16], [0, 256])
    cv2.normalize(hist_h, hist_h)
    cv2.normalize(hist_s, hist_s)
    cv2.normalize(hist_v, hist_v)
    histograms = (hist_h, hist_s, hist_v)
    
    # 3. OpenCV (делаем на увеличенной копии для лучшего детектирования)
    img_mini = img_pil.copy()
    img_mini.thumbnail((800, 800))
    img_cv = cv2.cvtColor(np.array(img_mini), cv2.COLOR_RGB2GRAY)
    
    kp, des = orb.detectAndCompute(img_cv, None)
    
    return {
        'path': path,
        'hashes': hashes,
        'histograms': histograms,
        'descriptors': des,
        'pixels': img_pil.width * img_pil.height,
        'size': file_size,
        'page': page_num
    }

def compare_histograms(hist1, hist2):
    """Сравнение гистограмм HSV (возвращает схожесть 0-1)"""
    if hist1 is None or hist2 is None:
        return 0.0
    
    try:
        # Сравниваем каждую компоненту (H, S, V)
        similarity_h = cv2.compareHist(hist1[0], hist2[0], cv2.HISTCMP_CORREL)
        similarity_s = cv2.compareHist(hist1[1], hist2[1], cv2.HISTCMP_CORREL)
        similarity_v = cv2.compareHist(hist1[2], hist2[2], cv2.HISTCMP_CORREL)
        
        # Усредняем (больше веса у Hue - тон цвета)
        similarity = (similarity_h * 0.5 + similarity_s * 0.3 + similarity_v * 0.2)
        
        # Нормализуем в 0-1
        similarity = max(0.0, min(1.0, (similarity + 1.0) / 2.0))
        return similarity
    except:
        return 0.0

def are_images_matching(des1, des2, min_matches=None, lowe_ratio=0.65, ratio_threshold=0.25, debug_info=None):
    """Улучшенное сравнение с динамическим min_matches"""
    if des1 is None or des2 is None or len(des1) < 10 or len(des2) < 10:
        if debug_info:
            logger.debug(f"ORB сравнение пропущено: дескрипторы None или слишком мало. des1: {len(des1) if des1 is not None else 'None'}, des2: {len(des2) if des2 is not None else 'None'}")
        return False
    
    # Динамический min_matches: минимум 15 или 20% от меньшего количества дескрипторов
    if min_matches is None:
        min_descriptors = min(len(des1), len(des2))
        min_matches = max(15, int(min_descriptors * 0.2))
    
    try:
        matches = bf.knnMatch(des1, des2, k=2)
        # Более мягкий коэффициент Лоу для кадрированных изображений
        good_matches = []
        for m_n in matches:
            if len(m_n) == 2:
                m, n = m_n
                if m.distance < lowe_ratio * n.distance:
                    good_matches.append(m)
        
        # Более мягкая проверка: минимум ratio_threshold matches от минимального количества дескрипторов
        min_descriptors = min(len(des1), len(des2))
        ratio_ok = len(good_matches) >= min_descriptors * ratio_threshold
        
        result = len(good_matches) >= min_matches and ratio_ok
        
        if debug_info:
            logger.debug(f"ORB сравнение: хороших совпадений={len(good_matches)}, минимум={min_matches}, дескрипторов={len(des1)}/{len(des2)}, ratio_ok={ratio_ok}, результат={result}")
            if not result and len(good_matches) > 0:
                logger.debug(f"  Причина провала: хороших совпадений {len(good_matches)} < {min_matches} или ratio_ok={ratio_ok}")
        
        return result
    except Exception as e:
        if debug_info:
            logger.debug(f"ORB сравнение ошибка: {e}")
        return False

def find_duplicates(image_paths, tolerance=15):
    """Поиск дубликатов СТРОГО по pHash"""
    phash_tolerance = max(1, tolerance // 3)
    logger.info(f"Поиск дубликатов: {len(image_paths)} файлов, pHash tolerance={phash_tolerance}")
    
    data_cache = {}
    
    for path in image_paths:
        for data in get_image_data(path):
            key = f"{data['path']}_{data['page']}"
            data_cache[key] = data

    groups = []
    visited = set()
    keys = list(data_cache.keys())
    
    total_comparisons = 0
    matches_found = 0
    
    for i, k1 in enumerate(keys):
        if k1 in visited: continue
        group = [data_cache[k1]['path']]
        for k2 in keys[i+1:]:
            if k2 in visited: continue
            total_comparisons += 1
            
            # Сравниваем ТОЛЬКО хеши (быстро и точно для дубликатов)
            min_hash_diff = 100
            for h1 in data_cache[k1]['hashes']:
                for h2 in data_cache[k2]['hashes']:
                    diff = h1 - h2
                    if diff < min_hash_diff:
                        min_hash_diff = diff
            
            if min_hash_diff <= phash_tolerance:
                group.append(data_cache[k2]['path'])
                visited.add(k2)
                matches_found += 1
                logger.debug(f"pHash совпадение: {os.path.basename(data_cache[k1]['path'])} <-> {os.path.basename(data_cache[k2]['path'])} diff={min_hash_diff}")
        
        if len(group) > 1:
            groups.append(group)
            logger.info(f"Найдена группа из {len(group)} дубликатов")
    
    logger.info(f"Итог: {len(groups)} групп, {matches_found} совпадений из {total_comparisons} сравнений")
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