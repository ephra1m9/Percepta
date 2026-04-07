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
    view = ctk.CTkFrame(parent, fg_color="#FFFFFF", corner_radius=15)
    
    content = ctk.CTkFrame(view, fg_color="transparent")
    content.pack(fill="both", expand=True, padx=40, pady=40)
    
    content.grid_columnconfigure(0, weight=1)
    content.grid_rowconfigure(7, weight=1)

    state = {
        "reference_folder": "", 
        "target_folders": [],   
        "found_groups": [] # Храним целые группы для обработки
    }

    # Иконки
    icon_folder = parent.create_font_icon("\uF3D1", parent.icon_path, size=15, color=ui_component.COLORS["text_main"])
    icon_add = parent.create_font_icon("\uF4F9", parent.icon_path, size=15, color=ui_component.COLORS["text_main"]) 
    icon_clear = parent.create_font_icon("\uF5DD", parent.icon_path, size=15, color="#E74C3C") 
    icon_search = parent.create_font_icon("\uF52A", parent.icon_path, size=16, color=ui_component.COLORS["text_light"])
    icon_copy = parent.create_font_icon("\uF2E1", parent.icon_path, size=15, color=ui_component.COLORS["text_main"])
    icon_delete = parent.create_font_icon("\uF5DD", parent.icon_path, size=15, color=ui_component.COLORS["error"])
    icon_cancel = parent.create_font_icon("\uF622", parent.icon_path, size=15, color=ui_component.COLORS["text_main"])

    # 0. Заголовок
    ui_component.title(content, "Поиск по эталону")

    # 1. Описание
    ui_component.description(
        content, 
        "Программа проверит добавленные папки и найдет в них те изображения, которые уже присутствуют в эталонной папке."
    )

    # 2. БЛОК 1: Эталонная папка
    frame_ref = ctk.CTkFrame(content, fg_color="transparent", border_width=1, border_color=ui_component.COLORS['border'], corner_radius=10)
    frame_ref.grid(row=2, column=0, sticky="ew", pady=(0, 20))
    
    btn_ref = ctk.CTkButton(frame_ref, text="Эталонная папка", image=icon_folder, font=ui_component.FONTS['second_btn'], **ui_component.BUTTON_SECONDARY)
    btn_ref.pack(side="left", padx=10, pady=10)
    
    lbl_ref = ctk.CTkLabel(frame_ref, text="Папка, где мы ищем дубликаты (Архив)", text_color=ui_component.COLORS["text_muted"], font=ui_component.FONTS['second'], anchor="e")
    lbl_ref.pack(side="left", padx=10, pady=10, fill="x", expand=True) 

    # 3. БЛОК 2: Папки для поиска
    frame_btns = ctk.CTkFrame(content, fg_color="transparent")
    frame_btns.grid(row=3, column=0, sticky="ew", pady=(0, 10))
    
    btn_add = ctk.CTkButton(frame_btns, text="Добавить папку поиска", font=ui_component.FONTS['second_btn'], image=icon_add, **ui_component.BUTTON_SECONDARY)
    btn_add.pack(side="left", padx=(0, 10))
    
    btn_clear = ctk.CTkButton(frame_btns, text="Очистить список", font=ui_component.FONTS['second_btn'], image=icon_clear, **ui_component.BUTTON_SECONDARY_DANGER)
    btn_clear.pack(side="left")

    listbox = ctk.CTkTextbox(content, height=80, state="disabled", font=ui_component.FONTS['second'], 
                             fg_color=ui_component.COLORS["bg_input"], text_color=ui_component.COLORS["text_main"], 
                             border_width=0, corner_radius=8)
    listbox.grid(row=4, column=0, sticky="ew", pady=(0, 20))

    btn_start = ctk.CTkButton(content, image=icon_search, text="Начать поиск", font=ui_component.FONTS['main'], **ui_component.BUTTON_PRIMARY)
    btn_start.grid(row=5, column=0, sticky="ew", pady=(0, 20))

    # 5. ЦЕНТРАЛЬНАЯ ЗОНА
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
    btn_box.pack(pady=(10, 0))

    btn_copy = ctk.CTkButton(btn_box, image=icon_copy, text="Скопировать найденные", font=ui_component.FONTS['second_btn'], **ui_component.BUTTON_SECONDARY)
    btn_copy.pack(side="left", padx=5)
    
    btn_delete = ctk.CTkButton(btn_box, image=icon_delete, text="Удалить найденные", font=ui_component.FONTS['second_btn'], **ui_component.BUTTON_SECONDARY_DANGER)
    btn_delete.pack(side="left", padx=5)
    
    btn_cancel = ctk.CTkButton(btn_box, image=icon_cancel, text="Отмена", font=ui_component.FONTS['second_btn'], **ui_component.BUTTON_SECONDARY)
    btn_cancel.pack(side="left", padx=5)


    # --- ЛОГИКА ---
    def show_message_state(text, color, font):
        results_container.grid_remove()
        action_frame.grid_remove()
        lbl_message.configure(text=text, text_color=color, font=font)
        message_frame.grid(row=6, column=0, sticky="nsew", pady=(10, 10))

    def show_results_state():
        message_frame.grid_remove()
        results_container.grid(row=6, column=0, sticky="nsew", pady=(10, 10))
        action_frame.grid(row=7, column=0, sticky="ew", pady=(0, 10))

    def set_reference_folder():
        folder = filedialog.askdirectory()
        if folder:
            state["reference_folder"] = folder
            
            folder_name = os.path.basename(folder) or folder
            
            lbl_ref.configure(text=folder_name, text_color=ui_component.COLORS["text_main"])
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
            show_message_state("Готово к сканированию", ui_component.COLORS["text_muted"], ui_component.FONTS['main'])
        else:
            show_message_state("Настройте папки для начала работы", ui_component.COLORS["text_muted"], ui_component.FONTS['second'])

    def render_results(duplicates, total_files):
        for widget in results_frame.winfo_children():
            widget.destroy()
        
        count = sum(len(group) - 1 for group in duplicates)
        lbl_results_header.configure(text=f"Найдено совпадений: {count}")

        for group in duplicates:
            group_frame = ctk.CTkFrame(results_frame, fg_color=ui_component.COLORS["bg_input"], corner_radius=6)
            group_frame.pack(fill="x", pady=(0, 10), padx=5)

            # Эталон (из архива)
            ctk.CTkLabel(group_frame, text=f"⭐ {os.path.basename(group[0])}", font=ui_component.FONTS['main'], text_color=ui_component.COLORS["primary"]).pack(anchor="w", padx=15, pady=(10, 5))

            # Копии (из рабочих папок)
            for dup_path in group[1:]:
                ctk.CTkLabel(group_frame, text=f"↳ {os.path.basename(dup_path)}", font=ui_component.FONTS['second'], text_color=ui_component.COLORS["text_main"]).pack(anchor="w", padx=15, pady=(0, 10))

        show_results_state()

    def process_duplicates(action):
        if not state["found_groups"]:
            return
        
        count = 0
        try:
            if action == "copy":
                for group in state["found_groups"]:
                    ref_name = os.path.basename(group[0])
                    name, ext = os.path.splitext(ref_name)
                    # Имя по твоему правилу
                    new_name = f"{name}_found-copy{ext}"
                    dest_path = os.path.join(state["reference_folder"], new_name)
                    
                    # Копируем самую первую найденную копию
                    shutil.copy2(group[1], dest_path)
                    count += 1
                show_message_state(f"✅ Скопировано в архив: {count}", ui_component.COLORS["text_main"], ui_component.FONTS['main'])

            elif action == "delete":
                # Удаляем сам эталон из архива, если для него нашлись дубли
                to_delete = {group[0] for group in state["found_groups"]}
                for file_path in to_delete:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                show_message_state(f"✅ Удалено из эталонной папки: {len(to_delete)}", ui_component.COLORS["text_main"], ui_component.FONTS['main'])
                
            state["found_groups"] = [] 
                
        except Exception as e:
            show_error_callback(f"Ошибка обработки:\n{e}")

    def run_scan(ref_folder, search_folders, tolerance):
        try:
            ref_files = get_image_files(ref_folder)
            search_files = []
            for folder in search_folders:
                search_files.extend(get_image_files(folder))

            all_files = ref_files + search_files
            if not ref_files or not search_files: 
                view.after(0, lambda: show_message_state("Папки пусты", ui_component.COLORS["text_muted"], ui_component.FONTS['main']))
                return
            
            show_message_state("Анализ совпадений...", ui_component.COLORS["text_muted"], ui_component.FONTS['main'])
            raw_duplicates = find_duplicates(all_files, tolerance)
            
            ref_path_norm = os.path.normpath(ref_folder)
            def is_ref(path): return os.path.normpath(path).startswith(ref_path_norm)

            target_duplicates = []
            for group in raw_duplicates:
                refs = [p for p in group if is_ref(p)]
                searches = [p for p in group if not is_ref(p)]
                
                if refs and searches:
                    # Гарантируем, что эталон всегда на 0-м месте
                    target_duplicates.append(refs + searches)
            
            if not target_duplicates:
                view.after(0, lambda: show_message_state("Совпадений не найдено", ui_component.COLORS["text_main"], ui_component.FONTS['main']))
            else:
                state["found_groups"] = target_duplicates
                view.after(0, lambda: render_results(target_duplicates, len(all_files)))

        except Exception:
            view.after(0, lambda: show_message_state("Ошибка сканирования", "#E74C3C", ui_component.FONTS['main']))
        finally:
            view.after(0, lambda: btn_start.configure(state="normal"))

    # Привязки
    btn_ref.configure(command=set_reference_folder)
    btn_add.configure(command=add_search_folder)
    btn_clear.configure(command=clear_folders)
    btn_start.configure(command=lambda: threading.Thread(target=run_scan, args=(state["reference_folder"], list(state["target_folders"]), app_state["tolerance"])).start())
    btn_copy.configure(command=lambda: process_duplicates("copy"))
    btn_delete.configure(command=lambda: process_duplicates("delete"))
    btn_cancel.configure(command=lambda: show_message_state("Отменено", ui_component.COLORS["text_muted"], ui_component.FONTS['main']))

    update_list()
    return view