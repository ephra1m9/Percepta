import os
import threading
import shutil
import customtkinter as ctk

from tkinter import filedialog
from PIL import Image

import src.ui.ui_components as ui_component
from src.utils import get_image_files
from src.scanner import find_duplicates

def create_single_folder_view(parent, app_state, show_error_callback):
    
    view = ctk.CTkFrame(parent, fg_color="#FFFFFF", corner_radius=15)
    
    content = ctk.CTkFrame(view, fg_color="transparent")
    content.pack(fill="both", expand=True, padx=40, pady=20)
    
    main_container = ctk.CTkFrame(content, fg_color="transparent")
    main_container.pack(fill="both", expand=True)
    main_container.grid_columnconfigure(0, weight=1)
    main_container.grid_rowconfigure(0, weight=1)

    state = {
        "target_folder": "",
        "pending_files": []
    }

    # Иконки
    icon_folder = parent.create_font_icon("\uF3D1", parent.icon_path, size=15, color=ui_component.COLORS["text_main"])
    icon_search = parent.create_font_icon("\uF52A", parent.icon_path, size=16, color=ui_component.COLORS["text_light"])
    icon_move = parent.create_font_icon("\uF3D4", parent.icon_path, size=15, color=ui_component.COLORS["text_main"])
    icon_delete = parent.create_font_icon("\uF5DD", parent.icon_path, size=15, color=ui_component.COLORS["text_main"])
    icon_back = parent.create_font_icon("\uF112", parent.icon_path, size=15, color=ui_component.COLORS["text_main"])

    # ================= ЭКРАН 1: НАСТРОЙКИ =================
    setup_frame = ctk.CTkFrame(main_container, fg_color="transparent")
    setup_frame.grid_columnconfigure(0, weight=1)
    
    ui_component.title(setup_frame, "Поиск дубликатов")
    ui_component.description(setup_frame, "Ищет дубликаты изображений в одной выбранной папке.")

    frame_folder = ctk.CTkFrame(setup_frame, fg_color="transparent", border_width=1, border_color=ui_component.COLORS['border'], corner_radius=10)
    frame_folder.grid(row=2, column=0, sticky="ew", pady=(20, 20))
    
    btn_folder = ctk.CTkButton(frame_folder, text="Выбрать папку", font=ui_component.FONTS['second_btn'], image=icon_folder, **ui_component.BUTTON_SECONDARY)
    btn_folder.pack(side="left", padx=10, pady=10)
    lbl_folder = ctk.CTkLabel(frame_folder, text="Не выбрано", text_color=ui_component.COLORS["text_muted"], font=ui_component.FONTS['second'], anchor="e")
    lbl_folder.pack(side="left", fill="x", expand=True, padx=10, pady=10)

    btn_start = ctk.CTkButton(setup_frame, image=icon_search, text="Начать поиск", font=ui_component.FONTS['main'], **ui_component.BUTTON_PRIMARY)
    btn_start.grid(row=3, column=0, sticky="ew")

    lbl_status = ctk.CTkLabel(setup_frame, text="Выберите папку для начала", font=ui_component.FONTS['second'], text_color=ui_component.COLORS["text_muted"])
    lbl_status.grid(row=4, column=0, pady=10)


    # ================= ЭКРАН 2: ЗАГРУЗКА И СООБЩЕНИЯ =================
    message_frame = ctk.CTkFrame(main_container, fg_color="transparent")
    lbl_message_big = ctk.CTkLabel(message_frame, text="", font=ui_component.FONTS['title'], text_color=ui_component.COLORS["text_muted"])
    lbl_message_big.place(relx=0.5, rely=0.5, anchor="center") 


    # ================= ЭКРАН 3: РЕЗУЛЬТАТЫ И КАРТОЧКИ =================
    results_frame = ctk.CTkFrame(main_container, fg_color="transparent")
    
    # Шапка
    res_top_bar = ctk.CTkFrame(results_frame, fg_color="transparent")
    res_top_bar.pack(side="top", fill="x", pady=(0, 10))
    btn_back = ctk.CTkButton(res_top_bar, text="Назад к настройкам", image=icon_back, font=ui_component.FONTS['second_btn'], **ui_component.BUTTON_SECONDARY)
    btn_back.pack(side="left")
    lbl_results_header = ctk.CTkLabel(res_top_bar, text="", font=ui_component.FONTS['main'], text_color=ui_component.COLORS["text_main"])
    lbl_results_header.pack(side="right", padx=10)

    # Карточки действий (прибиты ко дну)
    actions_grid = ctk.CTkFrame(results_frame, fg_color="transparent")
    actions_grid.pack(side="bottom", fill="x", pady=(10, 0))

    btn_move = ui_component.result_action_btn(
        actions_grid, 
        "В отдельную папку", 
        "Перемещает все найденные дубликаты (копии) в папку 'duplicates'", 
        icon_move
    )

    btn_delete = ui_component.result_action_btn(
        actions_grid, 
        "Удалить дубликаты", 
        "Безвозвратно удаляет все копии, оставляя только файл с лучшим качеством", 
        icon_delete
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
    def select_folder():
        folder = filedialog.askdirectory()
        if folder:
            state["target_folder"] = folder
            lbl_folder.configure(text=os.path.basename(folder), text_color=ui_component.COLORS["text_main"])
            lbl_status.configure(text="✅ Готово к сканированию", text_color=ui_component.COLORS["primary"])

    def render_results(duplicates, total_files):
        for widget in results_scroll.winfo_children():
            widget.destroy()

        count = sum(len(group) - 1 for group in duplicates)
        lbl_results_header.configure(text=f"Проверено: {total_files}   |   Найдено: {count}")

        for group in duplicates:
            group_frame = ctk.CTkFrame(results_scroll, fg_color=ui_component.COLORS["bg_input"], corner_radius=6)
            group_frame.pack(fill="x", pady=(0, 10), padx=5)

            orig_name = os.path.basename(group[0])
            ctk.CTkLabel(group_frame, text=f"⭐ {orig_name} (Оригинал)", font=ui_component.FONTS['main'], text_color=ui_component.COLORS["primary"]).pack(anchor="w", padx=15, pady=(10, 5))

            for dup_path in group[1:]:
                dup_name = os.path.basename(dup_path)
                ctk.CTkLabel(group_frame, text=f"↳ {dup_name}", font=ui_component.FONTS['second'], text_color=ui_component.COLORS["text_main"]).pack(anchor="w", padx=15, pady=(0, 10))

        switch_view("results")

    def process_duplicates(action):
        if not state["pending_files"]: return
            
        count = len(state["pending_files"])
        
        try:
            if action == "move":
                dup_folder = os.path.join(state["target_folder"], "duplicates")
                os.makedirs(dup_folder, exist_ok=True)
                for file_path in state["pending_files"]:
                    shutil.move(file_path, os.path.join(dup_folder, os.path.basename(file_path)))
                show_message(f"✅ Перемещено в 'duplicates': {count}")

            elif action == "delete":
                for file_path in state["pending_files"]:
                    os.remove(file_path)
                show_message(f"✅ Удалено файлов: {count}")
                
            state["pending_files"] = [] 
            view.after(2500, lambda: switch_view("setup"))
                
        except Exception as e:
            show_error_callback(f"Не удалось обработать файлы:\n{e}")

    def run_scan(folder, tolerance):
        try:
            files = get_image_files(folder, recursive=False)
            if not files: 
                view.after(0, lambda: show_message("Изображения не найдены"))
                return view.after(2000, lambda: switch_view("setup"))
            
            total_files = len(files)
            duplicates = find_duplicates(files, tolerance)
            
            def get_image_quality(file_path):
                try:
                    size_bytes = os.path.getsize(file_path)
                    with Image.open(file_path) as img:
                        pixels = img.width * img.height
                    return (pixels, size_bytes)
                except Exception:
                    return (0, 0)

            if not duplicates:
                view.after(0, lambda: show_message("Дубликатов не найдено"))
                view.after(2000, lambda: switch_view("setup"))
            else:
                state["pending_files"] = []
                sorted_duplicates = []
                
                for group in duplicates:
                    sorted_group = sorted(group, key=get_image_quality, reverse=True)
                    sorted_duplicates.append(sorted_group)
                    state["pending_files"].extend(sorted_group[1:])
                
                view.after(0, lambda: render_results(sorted_duplicates, total_files))

        except Exception:
            view.after(0, lambda: show_message("Ошибка сканирования"))
            view.after(2000, lambda: switch_view("setup"))
        finally:
            view.after(0, lambda: btn_start.configure(state="normal"))

    # Привязки
    btn_folder.configure(command=select_folder)
    btn_back.configure(command=lambda: switch_view("setup"))
    btn_start.configure(command=lambda: (btn_start.configure(state="disabled"), show_message("Анализ файлов..."), threading.Thread(target=run_scan, args=(state["target_folder"], app_state["tolerance"])).start()))
    btn_move.configure(command=lambda: process_duplicates("move"))
    btn_delete.configure(command=lambda: process_duplicates("delete"))

    return view