import os
import cv2
import numpy as np
import fitz
import re
import imagehash
from PIL import Image
import logging

from functools import lru_cache
from multiprocessing import Pool, cpu_count

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Инициализируем OpenCV
orb = cv2.ORB_create(nfeatures=800)
bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)

# Глобальный кэш для данных изображений
_image_data_cache = {}
_max_workers = max(1, cpu_count() - 1)


def get_image_data_cached(path):
    """Кэшированная версия get_image_data"""
    if path not in _image_data_cache:
        _image_data_cache[path] = get_image_data(path)
    return _image_data_cache[path]


def clear_image_cache():
    """Очистка кэша изображений"""
    global _image_data_cache
    _image_data_cache.clear()


def _init_worker():
    cv2.setNumThreads(1)


def _process_single_image(path):
    return path, get_image_data(path)


def get_all_image_data_parallel(paths, num_workers=None):
    if num_workers is None:
        num_workers = _max_workers
    num_workers = max(1, min(num_workers, cpu_count()))

    results = {}

    if len(paths) < 10 or num_workers == 1:
        for path in paths:
            data = get_image_data(path)
            if data:
                results[path] = data
    else:
        logger.info(f"Параллельная обработка {len(paths)} файлов на {num_workers} процессах")
        try:
            with Pool(num_workers, initializer=_init_worker) as pool:
                for path, data_list in pool.imap(_process_single_image, paths, chunksize=5):
                    if data_list:
                        results[path] = data_list
        except Exception as e:
            logger.warning(f"Многопроцессорная обработка не удалась: {e}")
            logger.info("Используем последовательную обработку...")
            for path in paths:
                data = get_image_data(path)
                if data:
                    results[path] = data
    
    return results


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
                rect = page.rect
                native_pixels = int(rect.width * 300 / 72) * int(rect.height * 300 / 72)
                page_text = page.get_text().strip()
                results.append(process_image_logic(img_pil, path, file_size, page_num + 1, native_pixels, page_text=page_text))
            doc.close()
        else:
            with Image.open(path) as img:
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                results.append(process_image_logic(img, path, file_size, None))
    except Exception as e:
        logger.debug(f"Ошибка чтения {path}: {e}")
    
    return results


def _text_jaccard(t1, t2, min_words=20):
    """Word-level Jaccard similarity between two texts. Returns None if either is too short."""
    words1 = set(t1.lower().split())
    words2 = set(t2.lower().split())
    if len(words1) < min_words or len(words2) < min_words:
        return None
    union = words1 | words2
    return len(words1 & words2) / len(union)


def process_image_logic(img_pil, path, file_size, page_num, native_pixels=None, page_text=None):
    """Ядро анализа изображения.
    native_pixels — реальное разрешение страницы PDF при 300 dpi.
    Для обычных изображений совпадает с pixels.
    """
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
    
    # ORB дескрипторы для всех 4 поворотов — инвариантность к ориентации скана
    descriptors_rotated = [des]  # 0° уже вычислен
    for angle in [90, 180, 270]:
        rotated_pil = img_mini.rotate(angle, expand=True)
        rotated_cv = cv2.cvtColor(np.array(rotated_pil), cv2.COLOR_RGB2GRAY)
        _, des_rot = orb.detectAndCompute(rotated_cv, None)
        descriptors_rotated.append(des_rot)
    
    actual_pixels = img_pil.width * img_pil.height
    
    return {
        'path': path,
        'hashes': hashes,
        'avg_hash': avg_hash,
        'dhash': dhash,
        'histograms': histograms,
        'descriptors': des,
        # descriptors_rotated: список дескрипторов для 0°/90°/180°/270°
        # используется в find_originals() для инвариантного к повороту ORB-сравнения
        'descriptors_rotated': descriptors_rotated,
        'pixels': actual_pixels,
        # native_pixels: для PDF — реальное разрешение при 300 dpi,
        # для обычных изображений — совпадает с pixels
        'native_pixels': native_pixels if native_pixels is not None else actual_pixels,
        'size': file_size,
        'page': page_num,
        'text': page_text or '',
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
        h1, w1 = img1.shape[:2]
        h2, w2 = img2.shape[:2]
        
        if h1 != h2 or w1 != w2:
            img2 = cv2.resize(img2, (w1, h1))
        
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


def _load_for_ssim_cmp(path, page, max_size=512):
    """Загружает изображение и даунскейлит до max_size для быстрого SSIM-сравнения."""
    img = load_image_for_ssim(path, page)
    if img is None:
        return None
    h, w = img.shape[:2]
    if max(h, w) > max_size:
        scale = max_size / max(h, w)
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    return img


def load_image_for_ssim(path, page):
    """
    Загружает изображение для вычисления SSIM.
    Для PDF использует fitz для рендеринга нужной страницы.
    Для обычных изображений использует PIL.
    Возвращает numpy array в RGB или None при ошибке.
    """
    try:
        ext = os.path.splitext(path)[1].lower()
        if ext == '.pdf' and page is not None:
            doc = fitz.open(path)
            page_index = page - 1  # page хранится как 1-based
            if page_index < 0 or page_index >= len(doc):
                doc.close()
                return None
            pix = doc.load_page(page_index).get_pixmap(dpi=72)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            doc.close()
            return np.array(img)
        else:
            with Image.open(path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                return np.array(img)
    except Exception as e:
        logger.debug(f"load_image_for_ssim ошибка ({path}, page={page}): {e}")
        return None


def check_images_match(ref_data, search_data, phash_tolerance, histogram_threshold, ssim_threshold):
    """
    Проверка совпадения двух изображений с использованием всех методов.
    Требует совпадения минимум 2 методов для точности.
    """
    match_count = 0
    match_reasons = []
    
    # 1. Проверка pHash
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
    
    # 4. Проверка SSIM — с поддержкой PDF через fitz
    img1_np = load_image_for_ssim(ref_data['path'], ref_data.get('page'))
    img2_np = load_image_for_ssim(search_data['path'], search_data.get('page'))
    if img1_np is not None and img2_np is not None:
        ssim_score = compare_ssim(img1_np, img2_np)
        if ssim_score >= ssim_threshold:
            match_count += 1
            match_reasons.append(f"SSIM:{ssim_score:.2f}")
    
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
    
    # минимум 2 совпадения для точности
    if match_count >= 2:
        logger.debug(f"Совпадение подтверждено ({match_count}): {', '.join(match_reasons)}")
        return True
    
    return False


def find_duplicates(image_paths, tolerance=15, progress_callback=None):
    """Поиск дубликатов по pHash + подтверждение ORB / гистограммой.
    progress_callback(checked, total, found) — вызывается после каждого файла.
    Прогресс: 0.0→1.0 по всем файлам (кэширование + сравнение).
    """
    phash_tolerance = max(4, tolerance // 2)
    # При большом tolerance pHash сам по себе даёт много ложных совпадений —
    # подтверждаем их структурным сравнением ORB (с учётом поворотов).
    # Для сканов документов (преимущественно белый фон) гистограмма почти
    # не отличается, поэтому ORB — основной фильтр; гистограмма используется
    # только как запасной критерий, если на изображениях мало деталей для ORB.
    orb_min_matches = max(15, tolerance // 2)
    histogram_threshold = min(0.9, 0.6 + phash_tolerance * 0.02)
    logger.info(
        f"Поиск дубликатов: {len(image_paths)} файлов, "
        f"phash_tolerance={phash_tolerance}, orb_min_matches={orb_min_matches}, "
        f"histogram_threshold={histogram_threshold:.2f}"
    )
    
    total = len(image_paths)

    # Кэшируем данные — прогресс по реальным файлам (checked идёт от 1 до total)
    for idx, path in enumerate(image_paths):
        get_image_data_cached(path)
        if progress_callback:
            progress_callback(idx + 1, total, 0)
    
    groups = []
    # visited хранит уникальный идентификатор страницы/изображения: (path, page)
    visited = set()

    # Собираем плоский список объектов data — каждая страница PDF как отдельный элемент
    all_data_items = []
    for path in image_paths:
        cached = get_image_data_cached(path)
        if cached:
            all_data_items.extend(cached)

    # Сравнение — прогресс остаётся на 1.0 (кэширование — самый долгий этап)
    for i, d1 in enumerate(all_data_items):
        item_id1 = (d1['path'], d1['page'])
        if item_id1 in visited:
            continue

        group = [d1['path']]

        for d2 in all_data_items[i + 1:]:
            item_id2 = (d2['path'], d2['page'])
            if item_id2 in visited:
                continue

            # Сравниваем pHash
            min_hash_diff = 100
            for h1 in d1['hashes']:
                for h2 in d2['hashes']:
                    diff = h1 - h2
                    if diff < min_hash_diff:
                        min_hash_diff = diff

            if min_hash_diff > phash_tolerance:
                continue

            # Подтверждение: ORB с учётом поворотов — отсекает случаи, когда
            # pHash совпал по общей структуре (например, белый фон документа),
            # а содержимое изображений разное.
            l_descs = d1.get('descriptors_rotated', [d1['descriptors']])
            h_descs = d2.get('descriptors_rotated', [d2['descriptors']])
            enough_features = (
                d1['descriptors'] is not None and len(d1['descriptors']) > 10 and
                d2['descriptors'] is not None and len(d2['descriptors']) > 10
            )

            if enough_features:
                confirmed = any(
                    are_images_matching(ld, hd, min_matches=orb_min_matches)
                    for ld in l_descs if ld is not None
                    for hd in h_descs if hd is not None
                )
                reason = "ORB"
            else:
                # Мало деталей для ORB (однотонные/простые изображения) —
                # подтверждаем схожестью цветовых гистограмм
                hist_similarity = compare_histograms(d1['histograms'], d2['histograms'])
                confirmed = hist_similarity >= histogram_threshold
                reason = f"hist={hist_similarity:.2f}"

            if not confirmed:
                logger.debug(
                    f"pHash совпал, но не подтверждено ({reason}): "
                    f"{os.path.basename(d1['path'])} (стр.{d1['page']}) "
                    f"<-> {os.path.basename(d2['path'])} (стр.{d2['page']}) "
                    f"diff={min_hash_diff}"
                )
                continue

            # Текстовая проверка для PDF: если обе страницы содержат достаточно текста
            # и текст существенно различается — это разные документы, не дубликаты.
            text_sim = _text_jaccard(d1.get('text', ''), d2.get('text', ''))
            if text_sim is not None and text_sim < 0.6:
                logger.debug(
                    f"Текст не совпадает (jaccard={text_sim:.2f}): "
                    f"{os.path.basename(d1['path'])} стр.{d1['page']} "
                    f"<-> {os.path.basename(d2['path'])} стр.{d2['page']}"
                )
                continue

            # SSIM-проверка: финальный фильтр по пиксельному сходству.
            # Отсекает разные рукописные страницы одного бланка — их SSIM значительно
            # ниже, чем у истинных дубликатов (одинаковый скан, разное сжатие/формат).
            # Порог зависит от tolerance: строже при малых значениях, мягче при больших.
            ssim_threshold = max(0.60, 0.82 - tolerance * 0.006)
            img1_np = _load_for_ssim_cmp(d1['path'], d1.get('page'))
            img2_np = _load_for_ssim_cmp(d2['path'], d2.get('page'))
            if img1_np is not None and img2_np is not None:
                ssim_score = compare_ssim(img1_np, img2_np)
                if ssim_score < ssim_threshold:
                    logger.debug(
                        f"SSIM отклонён ({ssim_score:.3f} < {ssim_threshold:.3f}): "
                        f"{os.path.basename(d1['path'])} стр.{d1['page']} "
                        f"<-> {os.path.basename(d2['path'])} стр.{d2['page']}"
                    )
                    continue

            group.append(d2['path'])
            visited.add(item_id2)
            logger.debug(
                f"Дубликат: {os.path.basename(d1['path'])} (стр.{d1['page']}) "
                f"<-> {os.path.basename(d2['path'])} (стр.{d2['page']}) "
                f"diff={min_hash_diff} ({reason})"
            )

        if len(group) > 1:
            groups.append(group)
            logger.info(f"Группа дубликатов: {len(group)} файлов")

    logger.info(f"Итог: {len(groups)} групп")
    return groups


def find_originals(low_res_paths, high_res_paths, tolerance=20, phash_threshold=None, quality_ratio=None, progress_callback=None, max_workers=None):
    """Поиск оригиналов: гибридный подход pHash + ORB + проверка качества.
    progress_callback(checked, total, found) — вызывается после каждого low-res файла.
    max_workers — сколько процессов использовать для кэширования (по умолчанию cpu_count()-1).
    """
    results = {'found': [], 'not_found': []}

    def clean_name(p):
        return re.sub(r'(_original|_edit|_retouch|-copy|\(\d+\))$', '',
                      os.path.splitext(os.path.basename(p))[0].lower()).strip()

    # Кэшируем данные — тяжёлые вычисления (pHash/ORB по 4 поворотам)
    # распределяются по процессам, чтобы не грузить одно ядро на 90%+
    paths_to_cache = [p for p in set(low_res_paths + high_res_paths) if p not in _image_data_cache]
    if paths_to_cache:
        _image_data_cache.update(get_all_image_data_parallel(paths_to_cache, num_workers=max_workers))
    
    if phash_threshold is None:
        phash_threshold = 25
    if quality_ratio is None:
        quality_ratio = 1.2
    
    orb_min_matches = max(20, tolerance)
    total_low = len(low_res_paths)
    
    # Предварительная индексация high-res файлов
    high_res_map = {}
    for p in high_res_paths:
        name = clean_name(p)
        if name not in high_res_map:
            high_res_map[name] = []
        high_res_map[name].append(p)
    
    for idx, lp in enumerate(low_res_paths):
        l_data_list = get_image_data_cached(lp)
        if not l_data_list:
            results['not_found'].append(lp)
            continue
        
        found = False
        name = clean_name(lp)
        
        # Кандидаты для проверки
        candidates = []
        if name in high_res_map:
            candidates.extend(high_res_map[name])
        else:
            candidates = high_res_paths
        
        # Итерируем по всем страницам low-res файла (для PDF — каждая страница)
        for l_data in l_data_list:
            if found:
                break
            
            for hp in candidates:
                if found:
                    break
                
                for h_data in get_image_data_cached(hp):
                    # 1. Проверка pHash (с учётом поворотов 0°/90°/180°/270°)
                    min_phash_diff = min(
                        h1 - h2
                        for h1 in l_data['hashes']
                        for h2 in h_data['hashes']
                    )

                    if min_phash_diff > phash_threshold:
                        logger.debug(
                            f"pHash не прошёл: {os.path.basename(lp)} vs "
                            f"{os.path.basename(hp)} стр.{h_data['page']}: "
                            f"diff={min_phash_diff} > {phash_threshold}"
                        )
                        continue

                    # 2. Структурная проверка: ORB с инвариантностью к повороту.
                    # Проверяем все 4 поворота l_data против всех 4 поворотов h_data.
                    # Это позволяет найти совпадение даже если скан повёрнут на 90°/180°/270°.
                    # ORB обязателен всегда — он отсекает изображения с похожим белым фоном
                    # (паспортное фото vs документ), которые дают одинаковый pHash.
                    l_descs = l_data.get('descriptors_rotated', [l_data['descriptors']])
                    h_descs = h_data.get('descriptors_rotated', [h_data['descriptors']])
                    orb_ok = any(
                        are_images_matching(ld, hd, min_matches=orb_min_matches)
                        for ld in l_descs if ld is not None
                        for hd in h_descs if hd is not None
                    )
                    if not orb_ok:
                        logger.debug(
                            f"ORB (все повороты) не прошёл: {os.path.basename(lp)} vs "
                            f"{os.path.basename(hp)} стр.{h_data['page']}: "
                            f"diff={min_phash_diff}"
                        )
                        continue

                    # 3. Проверка качества: используем native_pixels для корректного
                    # сравнения PDF (рендер при 72 dpi) с PNG/JPG превью.
                    # native_pixels для PDF = реальное разрешение страницы при 300 dpi.
                    # size используем как запасной критерий только для одноформатных пар.
                    resolution_ok = h_data['native_pixels'] >= l_data['native_pixels'] * quality_ratio
                    size_ok = (
                        os.path.splitext(h_data['path'])[1].lower() == os.path.splitext(l_data['path'])[1].lower()
                        and h_data['size'] >= l_data['size'] * quality_ratio
                    )

                    if resolution_ok or size_ok:
                        logger.debug(
                            f"Оригинал найден: {os.path.basename(lp)} -> "
                            f"{os.path.basename(hp)} стр.{h_data['page']} "
                            f"(pHash={min_phash_diff}, orb=True)"
                        )
                        results['found'].append((lp, h_data['path'], h_data['page']))
                        found = True
                        break
                    else:
                        logger.debug(
                            f"Качество не прошло: {os.path.basename(lp)} vs "
                            f"{os.path.basename(hp)} стр.{h_data['page']}: "
                            f"resolution_ok={resolution_ok} "
                            f"(native_pixels: {h_data['native_pixels']} vs {l_data['native_pixels']}*{quality_ratio}), "
                            f"size_ok={size_ok}"
                        )
        
        if not found:
            results['not_found'].append(lp)
        
        if progress_callback:
            progress_callback(idx + 1, total_low, len(results['found']))
    
    return results
