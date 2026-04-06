import os
import threading
import shutil
import customtkinter as ctk

from tkinter import filedialog
from PIL import Image

import src.ui.ui_components as ui_component
from src.utils import get_image_files, update_status
from src.scanner import find_duplicates

def create_single_folder_view(parent, app_state, show_error_callback):
    
    # --- 1. ГЛАВНЫЙ ФОН ---
    view = ctk.CTkFrame(parent, fg_color="#FFFFFF", corner_radius=15)
    
    # --- 2. ФРЕЙМ-ОБЕРТКА ---
    content = ctk.CTkFrame(view, fg_color="transparent")
    content.pack(fill="both", expand=True, padx=40, pady=40)
    
    content.grid_columnconfigure(0, weight=1)
    content.grid_rowconfigure(4, weight=1) 

    state = {
        "target_folder": "",
        "pending_files": []
    }

    # Иконки
    icon_folder = parent.create_font_icon("\uF3D1", parent.icon_path, size=15, color=ui_component.COLORS["text_main"])
    icon_search = parent.create_font_icon("\uF52A", parent.icon_path, size=16, color=ui_component.COLORS["text_light"])
    icon_move = parent.create_font_icon("\uF3D4", parent.icon_path, size=15, color=ui_component.COLORS["text_main"])
    icon_delete = parent.create_font_icon("\uF5DD", parent.icon_path, size=15, color=ui_component.COLORS["text_main"])
    icon_cancel = parent.create_font_icon("\uF622", parent.icon_path, size=15, color=ui_component.COLORS["error"])

    # 0. Заголовок
    ui_component.title(content, "Одна папка")

    # 1. Описание
    ui_component.description(content, "Поиск дубликатов в одной папке.")

    # 2. Выбор папки
    frame_folder = ctk.CTkFrame(content, fg_color="transparent", border_width=1, border_color=ui_component.COLORS['border'], corner_radius=10)
    frame_folder.grid(row=2, column=0, sticky="ew", pady=(0, 20))
    
    btn_folder = ctk.CTkButton(frame_folder, text="Выбрать папку", font=ui_component.FONTS['second_btn'], image=icon_folder, **ui_component.BUTTON_SECONDARY)
    btn_folder.pack(side="left", padx=10, pady=10)
    
    lbl_folder = ctk.CTkLabel(frame_folder, text="Не выбрано", text_color=ui_component.COLORS["text_muted"], font=ui_component.FONTS['second'], anchor="e")
    lbl_folder.pack(side="left", fill="x", expand=True, padx=10, pady=10)

    # 3. Кнопка поиска
    btn_start = ctk.CTkButton(content, image=icon_search, text="Начать поиск", font=ui_component.FONTS['main'], **ui_component.BUTTON_PRIMARY)
    btn_start.grid(row=3, column=0, sticky="ew", pady=(0, 20))

    # 4. ЦЕНТРАЛЬНАЯ ЗОНА (С фиксированной шапкой)
    message_frame = ctk.CTkFrame(content, fg_color="transparent")
    lbl_message = ctk.CTkLabel(message_frame, text="", justify="center")
    lbl_message.place(relx=0.5, rely=0.5, anchor="center") 

    results_container = ctk.CTkFrame(content, fg_color="transparent")
    
    lbl_results_header = ctk.CTkLabel(results_container, text="", font=ui_component.FONTS['main'], text_color=ui_component.COLORS["text_main"])
    lbl_results_header.pack(anchor="w", padx=5, pady=(0, 10))

    results_frame = ctk.CTkScrollableFrame(results_container, fg_color="transparent", border_width=1, border_color=ui_component.COLORS["border"], corner_radius=8)
    results_frame.pack(fill="both", expand=True)

    action_frame = ctk.CTkFrame(content, fg_color="transparent")
    btn_box = ctk.CTkFrame(action_frame, fg_color="transparent")
    btn_box.pack(pady=(10, 20))

    btn_move = ctk.CTkButton(btn_box, image=icon_move, text="В отдельную папку", font=ui_component.FONTS['second_btn'], **ui_component.BUTTON_SECONDARY)
    btn_move.pack(side="left", padx=5)
    btn_delete = ctk.CTkButton(btn_box, image=icon_delete, text="Удалить дубликаты", font=ui_component.FONTS['second_btn'], **ui_component.BUTTON_SECONDARY)
    btn_delete.pack(side="left", padx=5)
    btn_cancel = ctk.CTkButton(btn_box, image=icon_cancel, text="Отмена", font=ui_component.FONTS['second_btn'], **ui_component.BUTTON_SECONDARY_DANGER)
    btn_cancel.pack(side="left", padx=5)


    # --- 3. ЛОГИКА ---
    
    def show_message_state(text, color, font):
        results_container.grid_remove()
        action_frame.grid_remove()
        lbl_message.configure(text=text, text_color=color, font=font)
        message_frame.grid(row=4, column=0, sticky="nsew", pady=(10, 10))

    def show_results_state():
        message_frame.grid_remove()
        results_container.grid(row=4, column=0, sticky="nsew", pady=(10, 10))
        action_frame.grid(row=5, column=0, sticky="ew", pady=(0, 10))

    def select_folder():
        folder = filedialog.askdirectory()
        if folder:
            state["target_folder"] = folder
            folder_name = os.path.basename(folder) or folder
            lbl_folder.configure(text=folder_name, text_color=ui_component.COLORS["text_main"])
            show_message_state("Готово к сканированию", ui_component.COLORS["text_muted"], ui_component.FONTS['main'])

    def render_results(duplicates, total_files):
        for widget in results_frame.winfo_children():
            widget.destroy()

        count = sum(len(group) - 1 for group in duplicates)

        # Обновляем заголовок фиксированной шапки
        header_text = f"Проверено файлов: {total_files}   |   Найдено дубликатов: {count}"
        lbl_results_header.configure(text=header_text)

        for group in duplicates:
            group_frame = ctk.CTkFrame(results_frame, fg_color=ui_component.COLORS["bg_input"], corner_radius=6)
            group_frame.pack(fill="x", pady=(0, 10), padx=5)

            orig_name = os.path.basename(group[0])
            ctk.CTkLabel(group_frame, text=f"{orig_name}", font=ui_component.FONTS['main'], text_color=ui_component.COLORS["text_main"]).pack(anchor="w", padx=15, pady=(10, 5))

            for dup_path in group[1:]:
                dup_name = os.path.basename(dup_path)
                ctk.CTkLabel(group_frame, text=f"↳ {dup_name}", font=ui_component.FONTS['second'], text_color=ui_component.COLORS["text_muted"]).pack(anchor="w", padx=15, pady=(0, 10))

        show_results_state()

    def process_duplicates(action):
        if not state["pending_files"]:
            return
            
        count = len(state["pending_files"])
        
        try:
            if action == "move":
                dup_folder = os.path.join(state["target_folder"], "duplicates")
                os.makedirs(dup_folder, exist_ok=True)
                for file_path in state["pending_files"]:
                    shutil.move(file_path, os.path.join(dup_folder, os.path.basename(file_path)))
                
                show_message_state(f"✅ Перемещено файлов: {count}", ui_component.COLORS["text_main"], ui_component.FONTS['main'])

            elif action == "delete":
                for file_path in state["pending_files"]:
                    os.remove(file_path)
                    
                show_message_state(f"✅ Удалено файлов: {count}", ui_component.COLORS["text_main"], ui_component.FONTS['main'])
                
            state["pending_files"] = [] 
                
        except Exception as e:
            show_error_callback(f"Не удалось обработать файлы:\n{e}")

    def run_scan(folder, tolerance):
        try:
            files = get_image_files(folder, recursive=False)
            if not files: 
                view.after(0, lambda: show_message_state("Изображения не найдены", ui_component.COLORS["text_muted"], ui_component.FONTS['main']))
                return
            
            total_files = len(files)
            show_message_state("Сравнение хешей...", ui_component.COLORS["text_muted"], ui_component.FONTS['main'])
            
            duplicates = find_duplicates(files, tolerance)
            
            # --- Сортировка по качеству для одной папки ---
            def get_image_quality(file_path):
                try:
                    size_bytes = os.path.getsize(file_path)
                    with Image.open(file_path) as img:
                        pixels = img.width * img.height
                    return (pixels, size_bytes)
                except Exception:
                    return (0, 0)

            if not duplicates:
                view.after(0, lambda: show_message_state(f"Проверено файлов: {total_files}\n\nДубликатов не найдено", ui_component.COLORS["text_main"], ui_component.FONTS['main']))
            else:
                state["pending_files"] = []
                sorted_duplicates = []
                
                for group in duplicates:
                    # Ставим файл с лучшим качеством на 0 место
                    sorted_group = sorted(group, key=get_image_quality, reverse=True)
                    sorted_duplicates.append(sorted_group)
                    state["pending_files"].extend(sorted_group[1:])
                
                view.after(0, lambda: render_results(sorted_duplicates, total_files))

        except Exception as e:
            view.after(0, lambda: show_message_state("Произошла ошибка при сканировании", "#E74C3C", ui_component.FONTS['main']))
        finally:
            view.after(0, lambda: btn_start.configure(state="normal"))

    def start_scan():
        if not state["target_folder"]:
            return show_error_callback("Папка не выбрана.")
        
        btn_start.configure(state="disabled")
        show_message_state("Анализ файлов...", ui_component.COLORS["text_muted"], ui_component.FONTS['main'])
        threading.Thread(target=run_scan, args=(state["target_folder"], app_state["tolerance"])).start()

    # --- 4. ПРИВЯЗКА СОБЫТИЙ ---
    btn_folder.configure(command=select_folder)
    btn_start.configure(command=start_scan)
    btn_move.configure(command=lambda: process_duplicates("move"))
    btn_delete.configure(command=lambda: process_duplicates("delete"))
    btn_cancel.configure(command=lambda: show_message_state("Действие отменено", ui_component.COLORS["text_muted"], ui_component.FONTS['main']))

    show_message_state("Папка не выбрана", ui_component.COLORS["text_muted"], ui_component.FONTS['second'])

    return view