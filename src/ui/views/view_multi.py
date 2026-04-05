import os
import threading
import customtkinter as ctk

from tkinter import filedialog

import src.ui.ui_components as ui_component
from src.utils import get_image_files
from src.scanner import find_duplicates

def create_multi_folder_view(parent, app_state, show_error_callback):
    view = ctk.CTkFrame(parent)
    state = {"target_folders": []}

    view.grid_columnconfigure(0, weight=1)
    view.grid_rowconfigure(4, weight=1) 

    ctk.CTkLabel(view, text="Несколько папок", font=ui_component.FONTS['title']).grid(row=0, column=0, sticky="w", padx=30, pady=(30, 20))

    desc_frame = ctk.CTkFrame(view, fg_color=ui_component.COLORS["bg_input"], corner_radius=8)
    desc_frame.grid(row=1, column=0, padx=30, pady=(0, 20), sticky="ew")
    description = ctk.CTkLabel(desc_frame, text="Сравнивает папки и ищет дубликаты.", text_color=ui_component.COLORS["text_main"], font=ui_component.FONTS['second'], anchor="w")
    description.pack(fill="x", padx=14, pady=14)

    frame_btns = ctk.CTkFrame(view, fg_color="transparent")
    frame_btns.grid(row=2, column=0, sticky="ew", padx=30, pady=20)
    
    btn_add = ctk.CTkButton(frame_btns, text="+ Добавить папку", font=ui_component.FONTS['main'], height=40)
    btn_add.pack(side="left", padx=(0, 15))
    
    btn_clear = ctk.CTkButton(frame_btns, text="Очистить список", font=ui_component.FONTS['main'], height=40, fg_color="#E74C3C", hover_color="#C0392B")
    btn_clear.pack(side="left")

    listbox = ctk.CTkTextbox(view, height=100, state="disabled", font=ui_component.FONTS['second'], fg_color="#F9F9FB", border_width=1, border_color="#E5E5EA")
    listbox.grid(row=3, column=0, sticky="ew", padx=30, pady=(0, 20))

    btn_start = ctk.CTkButton(view, text="Начать поиск", font=ui_component.FONTS['main'], height=45, fg_color="#2FA572", hover_color="#108955")
    btn_start.grid(row=4, column=0, sticky="ew", padx=30, pady=(0, 20))

    textbox = ctk.CTkTextbox(view, state="disabled", font=ui_component.FONTS['second'], fg_color="#F9F9FB", border_width=1, border_color="#E5E5EA")
    textbox.grid(row=5, column=0, sticky="nsew", padx=30, pady=(0, 30))

    def log(message):
        textbox.configure(state="normal")
        textbox.insert("end", message + "\n")
        textbox.see("end") 
        textbox.configure(state="disabled")

    def update_list():
        listbox.configure(state="normal")
        listbox.delete("1.0", "end")
        if not state["target_folders"]:
            listbox.insert("end", "\n  Список папок пуст.\n  Нажмите «+ Добавить папку»")
        else:
            for i, folder in enumerate(state["target_folders"], 1):
                listbox.insert("end", f"  {i}. {folder}\n")
        listbox.configure(state="disabled")

    def add_folder():
        folder = filedialog.askdirectory()
        if folder and folder not in state["target_folders"]:
            state["target_folders"].append(folder)
            update_list()

    def clear_folders():
        state["target_folders"].clear()
        update_list()

    def run_scan(folders, tolerance):
        btn_start.configure(state="disabled")
        try:
            log("Сбор файлов...")
            all_files = [f for folder in folders for f in get_image_files(folder)]
            if not all_files: 
                return log("Картинки не найдены.")
                
            log(f"Собрано {len(all_files)} изображений. Поиск...")
            duplicates = find_duplicates(all_files, tolerance)
            
            if not duplicates:
                log("\n✅ Совпадений не найдено.")
            else:
                log(f"\n🚨 Найдено {len(duplicates)} групп совпадений:\n")
                for index, group in enumerate(duplicates, 1):
                    log(f"--- Группа {index} ---")
                    for path in group:
                        log(f" • {os.path.basename(path)}")
                    log("") 
        finally:
            view.after(0, lambda: btn_start.configure(state="normal"))

    def start_scan():
        if not state["target_folders"]:
            return log("⚠️ Добавьте хотя бы одну папку!")
        textbox.configure(state="normal")
        textbox.delete("1.0", "end")
        textbox.configure(state="disabled")
        threading.Thread(target=run_scan, args=(list(state["target_folders"]), app_state["tolerance"])).start()

    # Привязка логики
    btn_add.configure(command=add_folder)
    btn_clear.configure(command=clear_folders)
    btn_start.configure(command=start_scan)
    
    update_list()
    return view