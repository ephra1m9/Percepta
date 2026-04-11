# Percepta

Percepta is a desktop application for finding similar images, duplicate files, and matching originals across folders.  
It supports image files and PDF pages, uses perceptual hashing, and provides a simple GUI for reviewing and managing results.

## Features

- Find duplicate images in a single folder
- Compare one reference folder against multiple target folders
- Find higher-quality originals for compressed or low-resolution images
- Scan PDF pages as image sources
- Adjust similarity tolerance from `0` to `15`
- Enable or disable recursive search in subfolders
- Move, delete, copy, or export matched results depending on the mode

## Supported Files

Percepta scans files with these extensions:

- `.jpg`
- `.jpeg`
- `.png`
- `.webp`
- `.bmp`
- `.pdf`

## Requirements

- Python 3.10+ recommended
- Windows is the primary target platform
- Dependencies from `requirements.txt`

## Installation

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

## Usage

### 1. Duplicate Search

Choose one folder and scan it for duplicate images.

Available actions:

- Move duplicates to a `duplicates` folder
- Delete duplicate copies and keep the best-quality file

### 2. Search by Reference Folder

Choose one reference folder and one or more folders to scan. Percepta finds images that already exist in the reference folder.

Available actions:

- Copy found images into the reference folder
- Delete matching files from the reference folder

### 3. Find Originals

Choose a folder with compressed or low-resolution images and a folder with higher-quality sources. Percepta matches the low-quality images to their originals.

Available actions:

- Replace low-quality files with originals
- Copy originals next to the low-quality files
- Copy originals into a `Found_Originals` folder and create a text report

## Settings

- `Tolerance` controls how strict the visual matching is
- `Search in subfolders` enables recursive scanning

## Project Structure

```text
main.py
src/
  config.py
  scanner.py
  utils.py
  ui/
    app.py
    ui_components.py
    views/
      view_single.py
      view_multi.py
      view_originals.py
      view_settings.py
assets/
  fonts/
```

## Notes

- The app uses perceptual hashing, so visually similar images can be matched even if they are not identical files.
- PDF files are processed page by page.
- When files are copied or replaced, Percepta may create additional folders and report files next to the scanned data.

---

# Percepta

Percepta - это настольное приложение для поиска похожих изображений, дубликатов и оригиналов между папками.  
Программа поддерживает изображения и страницы PDF, использует перцептивное хеширование и предоставляет удобный интерфейс для просмотра и обработки результатов.

## Возможности

- Поиск дубликатов изображений в одной папке
- Сравнение одной эталонной папки с несколькими папками поиска
- Поиск оригиналов для сжатых или изображений низкого качества
- Обработка страниц PDF как отдельных изображений
- Настройка чувствительности от `0` до `15`
- Включение и отключение рекурсивного поиска по подпапкам
- Перемещение, удаление, копирование и экспорт найденных результатов в зависимости от режима

## Поддерживаемые файлы

Percepta обрабатывает файлы с расширениями:

- `.jpg`
- `.jpeg`
- `.png`
- `.webp`
- `.bmp`
- `.pdf`

## Требования

- Рекомендуется Python 3.10+
- Основная платформа - Windows
- Зависимости из файла `requirements.txt`

## Установка

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Запуск

```bash
python main.py
```

## Использование

### 1. Поиск дубликатов

Выберите одну папку и запустите поиск дубликатов изображений.

Доступные действия:

- Переместить дубликаты в папку `duplicates`
- Удалить копии, оставив файл с лучшим качеством

### 2. Поиск по эталону

Выберите одну эталонную папку и одну или несколько папок для поиска. Percepta найдет изображения, которые уже есть в эталонной папке.

Доступные действия:

- Скопировать найденные изображения в эталонную папку
- Удалить совпадающие файлы из эталонной папки

### 3. Поиск оригиналов

Выберите папку с сжатыми или низкокачественными изображениями и папку с исходниками более высокого качества. Percepta сопоставит изображения низкого качества с оригиналами.

Доступные действия:

- Заменить низкокачественные файлы оригиналами
- Скопировать оригиналы рядом с файлами низкого качества
- Скопировать оригиналы в папку `Found_Originals` и создать текстовый отчет

## Настройки

- `Tolerance` управляет строгостью сравнения изображений
- `Search in subfolders` включает поиск во вложенных папках

## Структура проекта

```text
main.py
src/
  config.py
  scanner.py
  utils.py
  ui/
    app.py
    ui_components.py
    views/
      view_single.py
      view_multi.py
      view_originals.py
      view_settings.py
assets/
  fonts/
```

## Примечания

- Приложение использует перцептивное хеширование, поэтому может находить визуально похожие изображения, даже если файлы не совпадают полностью.
- PDF-файлы обрабатываются постранично.
- При копировании или замене файлов Percepta может создавать дополнительные папки и текстовые отчеты рядом с исходными данными.
