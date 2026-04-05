import os
import threading
import shutil
import customtkinter as ctk

from tkinter import filedialog
from PIL import Image

import src.ui.ui_components as ui_component
from src.utils import get_image_files
from src.scanner import find_duplicates

def create_multi_folder_view(parent, app_state, show_error_callback):
    
    # --- 1. ГЛАВНЫЙ ФОН ---
    view = ctk.CTkFrame(parent, fg_color="#FFFFFF", corner_radius=15)
    
    # --- 2. ФРЕЙМ-ОБЕРТКА (Глобальные отступы) ---
    content = ctk.CTkFrame(view, fg_color="transparent")
    content.pack(fill="both", expand=True, padx=40, pady=40)
    
    content.grid_columnconfigure(0, weight=1)
    content.grid_rowconfigure(5, weight=1) # 5 строка - это центральная зона для результатов

    state = {
        "target_folders": [],
        "pending_files": []
    }

    # Иконки
    icon_add = parent.create_font_icon("\uF4F9", parent.icon_path, size=16, color=ui_component.COLORS["text_main"]) 
    icon_clear = parent.create_font_icon("\uF5DD", parent.icon_path, size=16, color="#E74C3C") 
    icon_search = parent.create_font_icon("\uF52A", parent.icon_path, size=16, color=ui_component.COLORS["text_light"])
    icon_move = parent.create_font_icon("\uF3D4", parent.icon_path, size=16, color=ui_component.COLORS["text_main"])
    icon_delete = parent.create_font_icon("\uF5DD", parent.icon_path, size=16, color=ui_component.COLORS["text_main"])
    icon_cancel = parent.create_font_icon("\uF622", parent.icon_path, size=16, color=ui_component.COLORS["text_main"])

    # 0. Заголовок
    ui_component.title(content, "Несколько папок")

    # 1. Описание
    ui_component.description(content, "Сравнивает выбранные папки между собой и ищет дубликаты.")

    # 2. Кнопки управления списком
    frame_btns = ctk.CTkFrame(content, fg_color="transparent")
    frame_btns.grid(row=2, column=0, sticky="ew", pady=(0, 10))
    
    btn_add = ctk.CTkButton(frame_btns, text="Добавить папку", font=ui_component.FONTS['main'], image=icon_add, **ui_component.BUTTON_SECONDARY)
    btn_add.pack(side="left", padx=(0, 10))
    
    # Стилизуем кнопку очистки под опасное действие (красный контур)
    btn_clear = ctk.CTkButton(frame_btns, text="Очистить список", font=ui_component.FONTS['main'], image=icon_clear, **ui_component.BUTTON_SECONDARY_DANGER)
    btn_clear.pack(side="left")

    # 3. Список добавленных папок (Оставляем Textbox, так как он отлично подходит для списка)
    listbox = ctk.CTkTextbox(content, height=80, state="disabled", font=ui_component.FONTS['second'], 
                             fg_color=ui_component.COLORS["bg_input"], text_color=ui_component.COLORS["text_main"], 
                             border_width=0, corner_radius=8)
    listbox.grid(row=3, column=0, sticky="ew", pady=(0, 20))

    # 4. Кнопка поиска
    btn_start = ctk.CTkButton(content, image=icon_search, text="Начать поиск", font=ui_component.FONTS['main'], **ui_component.BUTTON_PRIMARY)
    btn_start.grid(row=4, column=0, sticky="ew", pady=(0, 20))

    # 5. ЦЕНТРАЛЬНАЯ ЗОНА (Аналогично view_single)
    message_frame = ctk.CTkFrame(content, fg_color="transparent")
    lbl_message = ctk.CTkLabel(message_frame, text="", justify="center")
    lbl_message.place(relx=0.5, rely=0.5, anchor="center") 

    # --- НОВОЕ: Контейнер, который держит и фиксированный заголовок, и скролл ---
    results_container = ctk.CTkFrame(content, fg_color="transparent")
    
    # Фиксированный заголовок
    lbl_results_header = ctk.CTkLabel(results_container, text="", font=ui_component.FONTS['main'], text_color=ui_component.COLORS["text_main"])
    lbl_results_header.pack(anchor="w", padx=5, pady=(0, 10))

    # Сам список (теперь он внутри results_container)
    results_frame = ctk.CTkScrollableFrame(results_container, fg_color="transparent", border_width=1, border_color=ui_component.COLORS["border"], corner_radius=8)
    results_frame.pack(fill="both", expand=True)
    # -------------------------------------------------------------------------

    action_frame = ctk.CTkFrame(content, fg_color="transparent")
    btn_box = ctk.CTkFrame(action_frame, fg_color="transparent")
    btn_box.pack(pady=(10, 0))

    btn_move = ctk.CTkButton(btn_box, image=icon_move, text="В 'duplicates'", font=ui_component.FONTS['main'], **ui_component.BUTTON_SECONDARY)
    btn_move.pack(side="left", padx=5)
    
    btn_delete = ctk.CTkButton(btn_box, image=icon_delete, text="Удалить дубликаты", font=ui_component.FONTS['main'], **ui_component.BUTTON_SECONDARY)
    btn_delete.pack(side="left", padx=5)
    
    btn_cancel = ctk.CTkButton(btn_box, image=icon_cancel, text="Отмена", font=ui_component.FONTS['main'], **ui_component.BUTTON_SECONDARY)
    btn_cancel.pack(side="left", padx=5)


    # --- 3. ЛОГИКА ---

    def show_message_state(text, color, font):
        results_container.grid_remove()
        action_frame.grid_remove()
        lbl_message.configure(text=text, text_color=color, font=font)
        message_frame.grid(row=5, column=0, sticky="nsew", pady=(10, 10))

    def show_results_state():
        message_frame.grid_remove()
        results_container.grid(row=5, column=0, sticky="nsew", pady=(10, 10))
        action_frame.grid(row=6, column=0, sticky="ew", pady=(0, 10))

    def update_list():
        listbox.configure(state="normal")
        listbox.delete("1.0", "end")
        
        if not state["target_folders"]:
            listbox.insert("end", "Список папок пуст.\nНажмите «Добавить папку»")
            show_message_state("Папки не выбраны", ui_component.COLORS["text_muted"], ui_component.FONTS['second'])
        else:
            for i, folder in enumerate(state["target_folders"], 1):
                folder_name = os.path.basename(folder) or folder
                
                listbox.insert("end", f"  {i}. {folder_name}\n")
                
            show_message_state("Готово к сканированию", ui_component.COLORS["text_muted"], ui_component.FONTS['main'])
            
        listbox.configure(state="disabled")

    def add_folder():
        folder = filedialog.askdirectory()
        if folder and folder not in state["target_folders"]:
            state["target_folders"].append(folder)
            update_list()

    def clear_folders():
        state["target_folders"].clear()
        update_list()

    def render_results(duplicates, total_files):
        for widget in results_frame.winfo_children():
            widget.destroy()

        count = sum(len(group) - 1 for group in duplicates)

        header_text = f"Проверено файлов: {total_files}   |   Найдено дубликатов: {count}"
        lbl_results_header.configure(text=header_text)

        for group in duplicates:
            group_frame = ctk.CTkFrame(results_frame, fg_color=ui_component.COLORS["bg_input"], corner_radius=6)
            group_frame.pack(fill="x", pady=(0, 10), padx=5)

            # 1. Выводим Оригинал (добавили вывод имени его папки)
            orig_dir = os.path.basename(os.path.dirname(group[0]))
            orig_name = os.path.basename(group[0])
            
            ctk.CTkLabel(
                group_frame, 
                text=f"[{orig_dir}] {orig_name}", 
                font=ui_component.FONTS['main'], 
                text_color=ui_component.COLORS["text_main"]
            ).pack(anchor="w", padx=15, pady=(10, 5))

            # 2. Выводим Копии (убрали слэш, сделали формат как ты просил)
            for dup_path in group[1:]:
                dup_dir = os.path.basename(os.path.dirname(dup_path))
                dup_name = os.path.basename(dup_path)
                
                ctk.CTkLabel(
                    group_frame, 
                    text=f"↳ [{dup_dir}] {dup_name}", 
                    font=ui_component.FONTS['second'], 
                    text_color=ui_component.COLORS["text_muted"]
                ).pack(anchor="w", padx=15, pady=(0, 10))

        show_results_state()

    def process_duplicates(action):
        if not state["pending_files"]:
            return
            
        count = len(state["pending_files"])
        
        try:
            if action == "move":
                for file_path in state["pending_files"]:
                    # Умное перемещение: создаем папку duplicates внутри той папки, где лежит сам файл
                    base_dir = os.path.dirname(file_path)
                    dup_folder = os.path.join(base_dir, "duplicates")
                    os.makedirs(dup_folder, exist_ok=True)
                    shutil.move(file_path, os.path.join(dup_folder, os.path.basename(file_path)))
                
                show_message_state(f"✅ Перемещено файлов: {count}", ui_component.COLORS["text_main"], ui_component.FONTS['main'])

            elif action == "delete":
                for file_path in state["pending_files"]:
                    os.remove(file_path)
                    
                show_message_state(f"✅ Удалено файлов: {count}", ui_component.COLORS["text_main"], ui_component.FONTS['main'])
                
            state["pending_files"] = [] 
                
        except Exception as e:
            show_error_callback(f"Не удалось обработать файлы:\n{e}")

    def run_scan(folders, tolerance):
        try:
            all_files = []
            for folder in folders:
                all_files.extend(get_image_files(folder))

            if not all_files: 
                view.after(0, lambda: show_message_state("Изображения не найдены", ui_component.COLORS["text_muted"], ui_component.FONTS['main']))
                return
            
            total_files = len(all_files)
            
            show_message_state("Сравнение хешей...", ui_component.COLORS["text_muted"], ui_component.FONTS['main'])
            
            raw_duplicates = find_duplicates(all_files, tolerance)
            
            def get_folder_index(file_path):
                norm_path = os.path.normpath(file_path)
                for i, folder in enumerate(folders):
                    if norm_path.startswith(os.path.normpath(folder)):
                        return i
                return 999

            # --- НОВАЯ ФУНКЦИЯ ОЦЕНКИ КАЧЕСТВА ---
            def get_image_quality(file_path):
                try:
                    size_bytes = os.path.getsize(file_path) # Вес файла
                    with Image.open(file_path) as img:
                        pixels = img.width * img.height   # Общее количество пикселей
                    
                    # Возвращаем кортеж (разрешение, вес)
                    return (pixels, size_bytes)
                except Exception:
                    # Если файл битый, даем ему нулевой приоритет
                    return (0, 0)
            # ------------------------------------

            cross_folder_duplicates = []
            
            for group in raw_duplicates:
                represented_folders = {get_folder_index(path) for path in group}
                
                if len(represented_folders) > 1:
                    # Сортируем группу по качеству (от большего к меньшему). 
                    # reverse=True поставит самое тяжелое/большое изображение на 0-й индекс (Оригинал)
                    sorted_group = sorted(group, key=get_image_quality, reverse=True)
                    cross_folder_duplicates.append(sorted_group)
            
            if not cross_folder_duplicates:
                view.after(0, lambda: show_message_state(f"Проверено файлов: {total_files}\n\nСовпадений МЕЖДУ папками не найдено", ui_component.COLORS["text_main"], ui_component.FONTS['main']))
            else:
                state["pending_files"] = []
                for group in cross_folder_duplicates:
                    state["pending_files"].extend(group[1:]) # Все, кроме 0-го индекса, идут на удаление
                
                view.after(0, lambda: render_results(cross_folder_duplicates, total_files))

        except Exception as e:
            view.after(0, lambda: show_message_state("Произошла ошибка при сканировании", "#E74C3C", ui_component.FONTS['main']))
        finally:
            view.after(0, lambda: btn_start.configure(state="normal"))

    def start_scan():       
        if len(state["target_folders"]) < 2:
            return show_error_callback("Для сравнения добавьте минимум 2 папки!")
        
        btn_start.configure(state="disabled")
        show_message_state("Анализ файлов...", ui_component.COLORS["text_muted"], ui_component.FONTS['main'])
        
        threading.Thread(target=run_scan, args=(list(state["target_folders"]), app_state["tolerance"])).start()

    # --- 4. ПРИВЯЗКА СОБЫТИЙ ---
    btn_add.configure(command=add_folder)
    btn_clear.configure(command=clear_folders)
    btn_start.configure(command=start_scan)
    btn_move.configure(command=lambda: process_duplicates("move"))
    btn_delete.configure(command=lambda: process_duplicates("delete"))
    btn_cancel.configure(command=lambda: show_message_state("Действие отменено", ui_component.COLORS["text_muted"], ui_component.FONTS['main']))

    update_list()

    return view