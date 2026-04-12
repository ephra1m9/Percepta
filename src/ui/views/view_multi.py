import os
import re
import threading
import shutil
import customtkinter as ctk
import logging

from tkinter import filedialog
from PIL import Image

import src.ui.ui_components as ui_component
from src.utils import get_image_files
from src.scanner import find_duplicates, get_image_data, are_images_matching, compare_histograms, find_reference_matches

# Настройка логирования
logger = logging.getLogger(__name__)


def create_multi_folder_view(parent, app_state, show_error_callback):
    view = ctk.CTkFrame(parent, fg_color="#FFFFFF", corner_radius=15)
    
    content = ctk.CTkFrame(view, fg_color="transparent")
    content.pack(fill="both", expand=True, padx=40, pady=20)
    
    main_container = ctk.CTkFrame(content, fg_color="transparent")
    main_container.pack(fill="both", expand=True)
    main_container.grid_columnconfigure(0, weight=1)
    main_container.grid_rowconfigure(0, weight=1)

    state = {
        "reference_folder": "", 
        "target_folders": [],   
        "found_groups": [] 
    }

    # Иконки
    icon_folder = parent.create_font_icon("\uF3D1", parent.icon_path, size=15, color=ui_component.COLORS["text_main"])
    icon_add = parent.create_font_icon("\uF4F9", parent.icon_path, size=15, color=ui_component.COLORS["text_main"]) 
    icon_clear = parent.create_font_icon("\uF5DD", parent.icon_path, size=15, color="#E74C3C") 
    icon_search = parent.create_font_icon("\uF52A", parent.icon_path, size=16, color=ui_component.COLORS["text_light"])
    icon_copy = parent.create_font_icon("\uF2E1", parent.icon_path, size=15, color=ui_component.COLORS["text_main"])
    icon_delete = parent.create_font_icon("\uF5DD", parent.icon_path, size=15, color=ui_component.COLORS["text_main"])
    icon_cancel = parent.create_font_icon("\uF622", parent.icon_path, size=15, color="#E74C3C")

    # ================= ЭКРАН 1: НАСТРОЙКИ =================
    setup_frame = ctk.CTkFrame(main_container, fg_color="transparent")
    setup_frame.grid_columnconfigure(0, weight=1)

    ui_component.title(setup_frame, "Поиск по эталону")
    ui_component.description(
        setup_frame, 
        "Программа проверит добавленные папки и найдет в них те изображения, которые уже присутствуют в эталонной папке."
    )

    frame_ref = ctk.CTkFrame(setup_frame, fg_color="transparent", border_width=1, border_color=ui_component.COLORS['border'], corner_radius=10)
    frame_ref.grid(row=2, column=0, sticky="ew", pady=(20, 10))
    btn_ref = ctk.CTkButton(frame_ref, text="Эталонная папка", image=icon_folder, font=ui_component.FONTS['second_btn'], **ui_component.BUTTON_SECONDARY)
    btn_ref.pack(side="left", padx=10, pady=10)
    lbl_ref = ctk.CTkLabel(frame_ref, text="Изображения которые нужно найти", text_color=ui_component.COLORS["text_muted"], font=ui_component.FONTS['second'], anchor="e")
    lbl_ref.pack(side="left", padx=10, pady=10, fill="x", expand=True)

    frame_btns = ctk.CTkFrame(setup_frame, fg_color="transparent")
    frame_btns.grid(row=3, column=0, sticky="ew", pady=(20, 10))
    btn_add = ctk.CTkButton(frame_btns, text="Добавить папку для поиска", font=ui_component.FONTS['second_btn'], image=icon_add, **ui_component.BUTTON_SECONDARY)
    btn_add.pack(side="left", padx=(0, 10))
    btn_clear = ctk.CTkButton(frame_btns, text="Очистить список", font=ui_component.FONTS['second_btn'], image=icon_clear, **ui_component.BUTTON_SECONDARY_DANGER)
    btn_clear.pack(side="left")

    listbox = ctk.CTkTextbox(setup_frame, height=120, state="disabled", font=ui_component.FONTS['second'], fg_color=ui_component.COLORS["bg_input"], text_color=ui_component.COLORS["text_main"], border_width=0, corner_radius=8)
    listbox.grid(row=4, column=0, sticky="ew", pady=(0, 20))

    btn_start = ctk.CTkButton(setup_frame, image=icon_search, text="Начать поиск", font=ui_component.FONTS['main'], **ui_component.BUTTON_PRIMARY)
    btn_start.grid(row=5, column=0, sticky="ew")

    lbl_status = ctk.CTkLabel(setup_frame, text="Настройте папки для начала", font=ui_component.FONTS['second'], text_color=ui_component.COLORS["text_muted"])
    lbl_status.grid(row=6, column=0, pady=10)


    # ================= ЭКРАН 2: ЗАГРУЗКА И СООБЩЕНИЯ =================
    message_frame = ctk.CTkFrame(main_container, fg_color="transparent")
    lbl_message_big = ctk.CTkLabel(message_frame, text="", font=ui_component.FONTS['title'], text_color=ui_component.COLORS["text_muted"])
    lbl_message_big.place(relx=0.5, rely=0.5, anchor="center")


    # ================= ЭКРАН 3: РЕЗУЛЬТАТЫ И КАРТОЧКИ =================
    results_frame = ctk.CTkFrame(main_container, fg_color="transparent")

    # Шапка
    res_top_bar = ctk.CTkFrame(results_frame, fg_color="transparent")
    res_top_bar.pack(side="top", fill="x", pady=(0, 10))
    btn_back = ctk.CTkButton(res_top_bar, text="Отмена", image=icon_cancel, font=ui_component.FONTS['second_btn'], **ui_component.BUTTON_SECONDARY_DANGER)
    btn_back.pack(side="left")
    lbl_results_header = ctk.CTkLabel(res_top_bar, text="", font=ui_component.FONTS['main'], text_color=ui_component.COLORS["text_main"])
    lbl_results_header.pack(side="right", padx=10)

    # Карточки действий (прибиты ко дну)
    actions_grid = ctk.CTkFrame(results_frame, fg_color="transparent")
    actions_grid.pack(side="bottom", fill="x", pady=(10, 0))

    ui_component.result_action_card_btn(
        actions_grid, 
        "Скопировать найденные", 
        "Копирует найденные изображения из рабочих папок в эталонную папку", 
        icon_copy,
        lambda: process_duplicates("copy")
    )

    ui_component.result_action_card_btn(
        actions_grid, 
        "Удалить", 
        "Удаляет из эталонной папки те изображения, которые нашлись в остальных папках", 
        icon_delete,
        lambda: process_duplicates("delete")
    )

    # Список
    results_scroll = ctk.CTkScrollableFrame(results_frame, fg_color="transparent", border_width=1, border_color=ui_component.COLORS["border"], corner_radius=8)
    results_scroll.pack(side="top", fill="both", expand=True, pady=(0, 5))


    # --- ЛОГИКА ИНТЕРФЕЙСА ---
    def switch_view(view_name):
        setup_frame.grid_remove()
        message_frame.grid_remove()
        results_frame.grid_remove()

        if view_name == "setup":
            setup_frame.grid(row=0, column=0, sticky="nsew")
        elif view_name == "message":
            message_frame.grid(row=0, column=0, sticky="nsew")
        elif view_name == "results":
            results_frame.grid(row=0, column=0, sticky="nsew")


    def show_message(text):
        lbl_message_big.configure(text=text)
        switch_view("message")

    switch_view("setup")


    # --- ЛОГИКА РАБОТЫ ---
    def set_reference_folder():
        folder = filedialog.askdirectory()
        if folder:
            state["reference_folder"] = folder
            lbl_ref.configure(text=os.path.basename(folder), text_color=ui_component.COLORS["text_main"])
            check_ready_state()


    def update_list():
        listbox.configure(state="normal")
        listbox.delete("1.0", "end")
        if not state["target_folders"]:
            listbox.insert("end", "Список папок поиска пуст.")
        else:
            for i, folder in enumerate(state["target_folders"], 1):
                listbox.insert("end", f"  {i}. {os.path.basename(folder)}\n")
        listbox.configure(state="disabled")
        check_ready_state()


    def add_search_folder():
        folder = filedialog.askdirectory()
        if folder and folder not in state["target_folders"]:
            state["target_folders"].append(folder)
            update_list()


    def clear_folders():
        state["target_folders"].clear()
        update_list()


    def check_ready_state():
        if state["reference_folder"] and state["target_folders"]:
            lbl_status.configure(text="✅ Готово к сканированию", text_color=ui_component.COLORS["primary"])
        else:
            lbl_status.configure(text="Настройте папки для начала", text_color=ui_component.COLORS["text_muted"])


    def render_results(duplicates, total_files):
        for widget in results_scroll.winfo_children():
            widget.destroy()
        
        count = sum(len(group) - 1 for group in duplicates)
        lbl_results_header.configure(text=f"Найдено совпадений: {count}")

        for group in duplicates:
            group_frame = ctk.CTkFrame(results_scroll, fg_color=ui_component.COLORS["bg_surface"], border_width=1, border_color=ui_component.COLORS["border"], corner_radius=6)
            group_frame.pack(fill="x", pady=(0, 10), padx=5)

            ctk.CTkLabel(group_frame, text=f"⭐ {os.path.basename(group[0])}", font=ui_component.FONTS['main'], text_color=ui_component.COLORS["primary"]).pack(anchor="w", padx=15, pady=(10, 5))
            for dup_path in group[1:]:
                ctk.CTkLabel(group_frame, text=f"↳ {os.path.basename(dup_path)}", font=ui_component.FONTS['second'], text_color=ui_component.COLORS["text_main"]).pack(anchor="w", padx=15, pady=(0, 10))

        switch_view("results")


    def process_duplicates(action):
        if not state["found_groups"]: return
        
        count = 0
        try:
            if action == "copy":
                for group in state["found_groups"]:
                    ref_name = os.path.basename(group[0])
                    name, ext = os.path.splitext(ref_name)
                    
                    # Копируем все найденные файлы для этого эталона
                    for i, found_path in enumerate(group[1:], 1):
                        # Если найдена только одна копия, не добавляем индекс
                        if len(group) == 2:
                            new_name = f"{name}_found-copy{ext}"
                        else:
                            new_name = f"{name}_found-copy_{i}{ext}"
                            
                        dest_path = os.path.join(state["reference_folder"], new_name)
                        
                        # Защита от перезаписи, если файл уже существует
                        counter = 1
                        while os.path.exists(dest_path):
                            new_name = f"{name}_found-copy_{i}_{counter}{ext}"
                            dest_path = os.path.join(state["reference_folder"], new_name)
                            counter += 1
                            
                        shutil.copy2(found_path, dest_path)
                        count += 1
                show_message(f"✅ Скопировано в архив: {count}")

            elif action == "delete":
                to_delete = {group[0] for group in state["found_groups"]}
                for file_path in to_delete:
                    if os.path.exists(file_path): os.remove(file_path)
                show_message(f"✅ Удалено из эталона: {len(to_delete)}")
                
            state["found_groups"] = []
            view.after(2500, lambda: switch_view("setup"))
                
        except Exception as e:
            show_error_callback(f"Ошибка:\n{e}")


    def run_scan(ref_folder, search_folders, tolerance):
        try:
            logger.info(f"=== НАЧАЛО СКАНИРОВАНИЯ ===")
            logger.info(f"Эталонная папка: {ref_folder} ({len(search_folders)} папок для поиска)")
            logger.info(f"Толерантность: {tolerance}")
            
            is_recursive = app_state.get("search_recursive", False)
            ref_files = get_image_files(ref_folder, recursive=is_recursive)
            
            search_files = []
            for folder in search_folders:
                search_files.extend(get_image_files(folder, recursive=is_recursive))

            logger.info(f"Найдено эталонных файлов: {len(ref_files)}")
            logger.info(f"Найдено файлов для поиска: {len(search_files)}")

            if not ref_files or not search_files:
                logger.warning("Папки пусты")
                view.after(0, lambda: show_message("Папки пусты"))
                view.after(2000, lambda: switch_view("setup"))
                return

            def clean_filename(filename):
                stem = os.path.splitext(os.path.basename(filename))[0].lower().strip()
                return re.sub(r'(_original|_edit|_retouch|-copy|\(\d+\))$', '', stem).strip()

            ref_by_name = {}
            for p in ref_files:
                stem = clean_filename(p)
                if stem not in ref_by_name: ref_by_name[stem] = []
                ref_by_name[stem].append(p)

            target_duplicates = []
            matched_searches = set()
            matched_refs = set()
            ref_data_map = {}
            relaxed_tolerance = max(8, tolerance - 5)
            
            logger.info(f"ШАГ 1: Поиск по именам (relaxed_tolerance={relaxed_tolerance})")

            # ШАГ 1: Поиск с использованием имен
            name_matches = 0
            orb_matches = 0
            for s_path in search_files:
                s_stem = clean_filename(s_path)
                
                if s_stem in ref_by_name:
                    name_matches += 1
                    s_data_list = get_image_data(s_path)
                    if not s_data_list: continue
                    s_data = s_data_list[0]
                    
                    for r_path in ref_by_name[s_stem]:
                        if r_path not in ref_data_map:
                            r_data_list = get_image_data(r_path)
                            if not r_data_list: continue
                            ref_data_map[r_path] = r_data_list[0]
                        
                        r_data = ref_data_map[r_path]
                        
                        # МАГИЯ: Сравниваем точки (хватает 10 совпадений, так как имена уже похожи)
                        match_result = are_images_matching(
                            s_data['descriptors'],
                            r_data['descriptors'],
                            min_matches=relaxed_tolerance,
                            ratio_threshold=0.05,
                            debug_info=f"{os.path.basename(s_path)} <-> {os.path.basename(r_path)}"
                        )
                        if match_result:
                            target_duplicates.append([r_path, s_path])
                            matched_searches.add(s_path)
                            # Убрали matched_refs.add(r_path), чтобы эталон мог находить несколько копий
                            orb_matches += 1
                            logger.info(f"Найдено совпадение по имени+ORB: {os.path.basename(r_path)} <-> {os.path.basename(s_path)}")
                            break

            logger.info(f"ШАГ 1 завершен: совпадений по именам={name_matches}, ORB совпадений={orb_matches}")

            # ШАГ 2: Используем улучшенный алгоритм поиска по эталону для всех файлов
            # Это заменит сложную логику и будет искать даже переименованные/отретушированные изображения
            logger.info(f"ШАГ 2: Запуск улучшенного поиска по эталону")
            
            # Используем новую функцию find_reference_matches с увеличенным tolerance
            # для лучшего обнаружения ретушированных изображений
            enhanced_tolerance = min(30, tolerance + 5)
            reference_matches = find_reference_matches(ref_files, search_files, tolerance=enhanced_tolerance)
            
            # Добавляем найденные совпадения
            for ref_path, search_path in reference_matches:
                if search_path not in matched_searches:
                    target_duplicates.append([ref_path, search_path])
                    matched_searches.add(search_path)
            
            logger.info(f"Улучшенный поиск нашел {len(reference_matches)} совпадений")

            logger.info(f"ИТОГО найдено совпадений: {len(target_duplicates)}")
            
            if not target_duplicates:
                logger.info("Совпадений не найдено")
                view.after(0, lambda: show_message("Совпадений не найдено"))
                view.after(2000, lambda: switch_view("setup"))
            else:
                # Группируем результаты по эталонному файлу
                grouped_results = {}
                for ref_path, search_path in target_duplicates:
                    if ref_path not in grouped_results:
                        grouped_results[ref_path] = [ref_path]
                    if search_path not in grouped_results[ref_path]:
                        grouped_results[ref_path].append(search_path)
                
                # Преобразуем словарь в список списков
                final_groups = list(grouped_results.values())
                
                state["found_groups"] = final_groups
                view.after(0, lambda: render_results(final_groups, len(ref_files + search_files)))
                logger.info(f"Успешно найдено {len(final_groups)} групп совпадений")

        except Exception as e:
            logger.error(f"Ошибка сканирования: {e}", exc_info=True)
            print(f"Ошибка сканирования: {e}")
            view.after(0, lambda: show_message("Ошибка сканирования"))
            view.after(2000, lambda: switch_view("setup"))
        finally:
            view.after(0, lambda: btn_start.configure(state="normal"))

    # Привязки
    btn_ref.configure(command=set_reference_folder)
    btn_add.configure(command=add_search_folder)
    btn_clear.configure(command=clear_folders)
    btn_back.configure(command=lambda: switch_view("setup"))
    btn_start.configure(command=lambda: (btn_start.configure(state="disabled"), show_message("Анализ файлов..."), threading.Thread(target=run_scan, args=(state["reference_folder"], list(state["target_folders"]), app_state["tolerance"])).start()))
    # btn_copy.configure(command=lambda: process_duplicates("copy"))
    # btn_delete.configure(command=lambda: process_duplicates("delete"))

    update_list()
    return view