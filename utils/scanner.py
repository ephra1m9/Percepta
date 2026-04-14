import os
import cv2
import numpy as np
import fitz
import re
import imagehash
from PIL import Image
import logging
from functools import lru_cache

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Инициализируем OpenCV
orb = cv2.ORB_create(nfeatures=1500)
bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)

# Глобальный кэш для данных изображений
_image_data_cache = {}


def get_image_data_cached(path):
    """Кэшированная версия get_image_data"""
    if path not in _image_data_cache:
        _image_data_cache[path] = get_image_data(path)
    return _image_data_cache[path]


def clear_image_cache():
    """Очистка кэша изображений"""
    global _image_data_cache
    _image_data_cache.clear()


def get_hashes_with_rotations(img):
    """Получение хешей для разных углов поворота"""
    hashes = []
    for angle in [0, 90, 180, 270]:
        if angle == 0:
            hashes.append(imagehash.phash(img))
        else:
            hashes.append(imagehash.phash(img.rotate(angle, expand=True)))
    return hashes


def get_image_data(path):
    """Получение данных изображения для анализа: хеши, гистограммы, дескрипторы"""
    results = []
    ext = os.path.splitext(path)[1].lower()
    
    try:
        file_size = os.path.getsize(path)
    except Exception:
        file_size = 0
        
    try:
        if ext == '.pdf':
            doc = fitz.open(path)
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                pix = page.get_pixmap(dpi=72)
                img_pil = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                results.append(process_image_logic(img_pil, path, file_size, page_num + 1))
            doc.close()
        else:
            with Image.open(path) as img:
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                results.append(process_image_logic(img, path, file_size, None))
    except Exception as e:
        logger.debug(f"Ошибка чтения {path}: {e}")
    
    return results


def process_image_logic(img_pil, path, file_size, page_num):
    """Ядро анализа изображения"""
    # pHash для разных углов
    hashes = get_hashes_with_rotations(img_pil)
    
    # aHash (средний хеш) - быстрый
    avg_hash = imagehash.average_hash(img_pil)
    
    # dHash (разностный хеш) - для сравнения
    dhash = imagehash.dhash(img_pil)
    
    # Цветовые гистограммы (HSV) - нормализуем с помощью intersection
    img_hsv = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2HSV)
    hist_h = cv2.calcHist([img_hsv], [0], None, [32], [0, 180])
    hist_s = cv2.calcHist([img_hsv], [1], None, [16], [0, 256])
    hist_v = cv2.calcHist([img_hsv], [2], None, [16], [0, 256])
    cv2.normalize(hist_h, hist_h, norm_type=cv2.NORM_L1)
    cv2.normalize(hist_s, hist_s, norm_type=cv2.NORM_L1)
    cv2.normalize(hist_v, hist_v, norm_type=cv2.NORM_L1)
    histograms = (hist_h, hist_s, hist_v)
    
    # OpenCV на увеличенной копии для лучшего детектирования
    img_mini = img_pil.copy()
    img_mini.thumbnail((1000, 1000))
    img_cv = cv2.cvtColor(np.array(img_mini), cv2.COLOR_RGB2GRAY)
    
    kp, des = orb.detectAndCompute(img_cv, None)
    
    return {
        'path': path,
        'hashes': hashes,
        'avg_hash': avg_hash,
        'dhash': dhash,
        'histograms': histograms,
        'descriptors': des,
        'pixels': img_pil.width * img_pil.height,
        'size': file_size,
        'page': page_num
    }


def compare_histograms(hist1, hist2):
    """
    Сравнение гистограмм HSV используя normalized intersection.
    Возвращает схожесть 0-1, где 1 = полное совпадение.
    """
    if hist1 is None or hist2 is None:
        return 0.0
    
    try:
        # Normalized intersection - чем ближе к 1, тем больше схожесть
        intersection_h = cv2.compareHist(hist1[0], hist2[0], cv2.HISTCMP_INTERSECT)
        intersection_s = cv2.compareHist(hist1[1], hist2[1], cv2.HISTCMP_INTERSECT)
        intersection_v = cv2.compareHist(hist1[2], hist2[2], cv2.HISTCMP_INTERSECT)
        
        # Нормализуем пересечение (оно может быть от 0 до 1 для каждой гистограммы)
        # H канал более важен для идентификации
        similarity = (intersection_h * 0.5 + intersection_s * 0.3 + intersection_v * 0.2)
        
        return max(0.0, min(1.0, similarity))
    except:
        return 0.0


def compare_ssim(img1, img2):
    """
    Вычисление SSIM (Structural Similarity Index) между двумя изображениями.
    Возвращает значение 0-1, где 1 = полное совпадение.
    """
    try:
        # Ресайзим до одинакового размера если нужно
        h1, w1 = img1.shape[:2]
        h2, w2 = img2.shape[:2]
        
        if h1 != h2 or w1 != w2:
            img2 = cv2.resize(img2, (w1, h1))
        
        # Конвертируем в градации серого
        if len(img1.shape) == 3:
            gray1 = cv2.cvtColor(img1, cv2.COLOR_RGB2GRAY)
        else:
            gray1 = img1
            
        if len(img2.shape) == 3:
            gray2 = cv2.cvtColor(img2, cv2.COLOR_RGB2GRAY)
        else:
            gray2 = img2
        
        # Вычисляем SSIM
        C1 = (0.01 * 255) ** 2
        C2 = (0.03 * 255) ** 2
        
        gray1 = gray1.astype(np.float64)
        gray2 = gray2.astype(np.float64)
        
        mu1 = cv2.GaussianBlur(gray1, (11, 11), 1.5)
        mu2 = cv2.GaussianBlur(gray2, (11, 11), 1.5)
        
        mu1_sq = mu1 ** 2
        mu2_sq = mu2 ** 2
        mu1_mu2 = mu1 * mu2
        
        sigma1_sq = cv2.GaussianBlur(gray1 ** 2, (11, 11), 1.5) - mu1_sq
        sigma2_sq = cv2.GaussianBlur(gray2 ** 2, (11, 11), 1.5) - mu2_sq
        sigma12 = cv2.GaussianBlur(gray1 * gray2, (11, 11), 1.5) - mu1_mu2
        
        ssim_map = ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) / ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))
        
        return float(np.mean(ssim_map))
    except Exception as e:
        logger.debug(f"SSIM error: {e}")
        return 0.0


def are_images_matching(des1, des2, min_matches=None, lowe_ratio=0.72, ratio_threshold=0.10, debug_info=None):
    """
    Улучшенное сравнение ORB дескрипторов.
    Строгие пороги для точности.
    """
    if des1 is None or des2 is None or len(des1) < 10 or len(des2) < 10:
        if debug_info:
            logger.debug(f"ORB пропущен: дескрипторов недостаточно. des1: {len(des1) if des1 is not None else 'None'}, des2: {len(des2) if des2 is not None else 'None'}")
        return False
    
    # Динамический min_matches
    if min_matches is None:
        min_descriptors = min(len(des1), len(des2))
        min_matches = max(15, int(min_descriptors * 0.18))
    
    try:
        matches = bf.knnMatch(des1, des2, k=2)
        
        good_matches = []
        for m_n in matches:
            if len(m_n) == 2:
                m, n = m_n
                if m.distance < lowe_ratio * n.distance:
                    good_matches.append(m)
        
        min_descriptors = min(len(des1), len(des2))
        ratio_ok = len(good_matches) >= min_descriptors * ratio_threshold
        
        result = len(good_matches) >= min_matches and ratio_ok
        
        if debug_info and result:
            logger.debug(f"ORB совпадение: {debug_info}, good={len(good_matches)}, min={min_matches}, ratio_ok={ratio_ok}")
        
        return result
    except Exception as e:
        if debug_info:
            logger.debug(f"ORB ошибка: {e}")
        return False


def find_reference_matches(reference_paths, search_paths, tolerance=15):
    """
    Улучшенный поиск по эталону.
    Комбинирует pHash, гистограммы, SSIM и ORB для максимального обнаружения.
    """
    logger.info(f"Поиск по эталону: {len(reference_paths)} эталонов, {len(search_paths)} для поиска")
    
    # Рассчитываем адаптивные пороги (баланс между точностью и полнотой)
    phash_tolerance = min(18, tolerance + 5)  # Ослаблен для отретушированных
    histogram_threshold = 0.65  # Снижен для гибкости
    ssim_threshold = 0.85  # Снижен для ретушированных
    
    logger.info(f"Пороги: pHash<={phash_tolerance}, hist>={histogram_threshold}, SSIM>={ssim_threshold}")
    
    matches = []
    matched_search = set()
    
    # Обрабатываем эталонные файлы
    for ref_path in reference_paths:
        ref_data_list = get_image_data_cached(ref_path)
        if not ref_data_list:
            continue
        
        for ref_data in ref_data_list:
            for search_path in search_paths:
                if search_path in matched_search:
                    continue
                
                search_data_list = get_image_data_cached(search_path)
                if not search_data_list:
                    continue
                
                for search_data in search_data_list:
                    match_result = check_images_match(
                        ref_data, search_data,
                        phash_tolerance, histogram_threshold, ssim_threshold
                    )
                    
                    if match_result:
                        matches.append([ref_path, search_path])
                        matched_search.add(search_path)
                        logger.info(f"Совпадение: {os.path.basename(ref_path)} -> {os.path.basename(search_path)}")
                        break  # Нашли совпадение для этого search_path, берём следующий
    
    logger.info(f"Найдено {len(matches)} совпадений")
    return matches


def check_images_match(ref_data, search_data, phash_tolerance, histogram_threshold, ssim_threshold):
    """
    Проверка совпадения двух изображений с использованием всех методов.
    Требует совпадения минимум 2 методов для точности.
    """
    match_count = 0
    match_reasons = []
    
    # 1. Проверка pHash (самый быстрый и надёжный)
    min_hash_diff = 100
    for h1 in ref_data['hashes']:
        for h2 in search_data['hashes']:
            diff = h1 - h2
            if diff < min_hash_diff:
                min_hash_diff = diff
    
    if min_hash_diff <= phash_tolerance:
        match_count += 1
        match_reasons.append(f"pHash:{min_hash_diff}")
    
    # 2. Проверка aHash
    avg_diff = ref_data['avg_hash'] - search_data['avg_hash']
    if avg_diff <= phash_tolerance // 2:
        match_count += 1
        match_reasons.append(f"aHash:{avg_diff}")
    
    # 3. Проверка гистограмм
    hist_similarity = compare_histograms(ref_data['histograms'], search_data['histograms'])
    if hist_similarity >= histogram_threshold:
        match_count += 1
        match_reasons.append(f"hist:{hist_similarity:.2f}")
    
    # 4. Проверка SSIM
    try:
        img1 = Image.open(ref_data['path'])
        if img1.mode != 'RGB':
            img1 = img1.convert('RGB')
        img1_np = np.array(img1)
        img1.close()
        
        img2 = Image.open(search_data['path'])
        if img2.mode != 'RGB':
            img2 = img2.convert('RGB')
        img2_np = np.array(img2)
        img2.close()
        
        ssim_score = compare_ssim(img1_np, img2_np)
        if ssim_score >= ssim_threshold:
            match_count += 1
            match_reasons.append(f"SSIM:{ssim_score:.2f}")
    except Exception:
        pass
    
    # 5. Проверка ORB (ослаблен для кадрированных)
    des1 = ref_data['descriptors']
    des2 = search_data['descriptors']
    
    if des1 is not None and des2 is not None and len(des1) > 10 and len(des2) > 10:
        min_des_len = min(len(des1), len(des2))
        dynamic_min_matches = max(12, int(min_des_len * 0.15))
        
        if are_images_matching(
            des1, des2,
            min_matches=dynamic_min_matches,
            lowe_ratio=0.75,
            ratio_threshold=0.08
        ):
            match_count += 1
            match_reasons.append("ORB")
    
    # Требуем минимум 2 совпадения для точности
    if match_count >= 2:
        logger.debug(f"Совпадение подтверждено ({match_count}): {', '.join(match_reasons)}")
        return True
    
    return False


def find_duplicates(image_paths, tolerance=15):
    """Поиск дубликатов по pHash"""
    phash_tolerance = max(8, tolerance // 2)
    logger.info(f"Поиск дубликатов: {len(image_paths)} файлов, tolerance={phash_tolerance}")
    
    # Кэшируем данные
    for path in image_paths:
        get_image_data_cached(path)
    
    groups = []
    visited = set()
    
    keys = []
    for path in image_paths:
        for data in get_image_data_cached(path):
            key = f"{data['path']}_{data['page']}"
            keys.append(key)
    
    for i, k1 in enumerate(keys):
        if k1 in visited:
            continue
            
        group = [_image_data_cache[k1]['path']]
        
        for k2 in keys[i+1:]:
            if k2 in visited:
                continue
            
            # Сравниваем хеши
            min_hash_diff = 100
            for h1 in _image_data_cache[k1]['hashes']:
                for h2 in _image_data_cache[k2]['hashes']:
                    diff = h1 - h2
                    if diff < min_hash_diff:
                        min_hash_diff = diff
            
            if min_hash_diff <= phash_tolerance:
                group.append(_image_data_cache[k2]['path'])
                visited.add(k2)
                logger.debug(f"Дубликат: {os.path.basename(_image_data_cache[k1]['path'])} <-> {os.path.basename(_image_data_cache[k2]['path'])} diff={min_hash_diff}")
        
        if len(group) > 1:
            groups.append(group)
            logger.info(f"Группа дубликатов: {len(group)} файлов")
    
    logger.info(f"Итог: {len(groups)} групп")
    return groups


def find_originals(low_res_paths, high_res_paths, tolerance=20, phash_threshold=None, quality_ratio=None):
    """Поиск оригиналов: гибридный подход pHash + ORB + проверка качества"""
    results = {'found': [], 'not_found': []}
    
    def clean_name(p):
        return re.sub(r'(_original|_edit|_retouch|-copy|\(\d+\))$', '',
                      os.path.splitext(os.path.basename(p))[0].lower()).strip()
    
    # Кэшируем данные
    for p in set(low_res_paths + high_res_paths):
        get_image_data_cached(p)
    
    if phash_threshold is None:
        phash_threshold = 12
    if quality_ratio is None:
        quality_ratio = 1.2
    
    orb_min_matches = max(20, tolerance)
    
    # Предварительная индексация high-res файлов
    high_res_map = {}
    for p in high_res_paths:
        name = clean_name(p)
        if name not in high_res_map:
            high_res_map[name] = []
        high_res_map[name].append(p)
    
    for lp in low_res_paths:
        l_data_list = get_image_data_cached(lp)
        if not l_data_list:
            results['not_found'].append(lp)
            continue
        
        l_data = l_data_list[0]
        found = False
        name = clean_name(lp)
        
        # Кандидаты для проверки
        candidates = []
        if name in high_res_map:
            candidates.extend(high_res_map[name])
        else:
            candidates = high_res_paths
        
        for hp in candidates:
            for h_data in get_image_data_cached(hp):
                # Проверка pHash
                phash_match = any(
                    h1 - h2 <= phash_threshold
                    for h1 in l_data['hashes']
                    for h2 in h_data['hashes']
                )
                
                if not phash_match:
                    continue
                
                # Проверка ORB
                if not are_images_matching(
                    l_data['descriptors'],
                    h_data['descriptors'],
                    min_matches=orb_min_matches
                ):
                    continue
                
                # Проверка качества
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
