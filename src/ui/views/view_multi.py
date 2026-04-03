import os
import threading
import customtkinter as ctk

from tkinter import filedialog

from src.config import COLORS
from src.utils import get_image_files
from src.scanner import find_duplicates

class MultiFolderView(ctk.CTkFrame):
    def __init__(self, master, app_state, fonts, **kwargs):
        super().__init__(master, **kwargs)
        self.app_state = app_state
        self.fonts = fonts
        self.target_folders = []
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1) 

        ctk.CTkLabel(self, text="Сравнение изображений между папками", font=self.fonts['title']).grid(row=0, column=0, sticky="w", padx=30, pady=(30, 20))

        desc_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_input"], corner_radius=8)
        desc_frame.grid(row=1, column=0, padx=30, pady=(0, 20), sticky="ew")
        description = ctk.CTkLabel(desc_frame, text="Сравнивает папки и ищет дубликаты.", text_color=COLORS["text_main"], font=self.fonts['second'], anchor="w")
        description.pack(fill="x", padx=20, pady=20)

        frame_btns = ctk.CTkFrame(self, fg_color="transparent")
        frame_btns.grid(row=2, column=0, sticky="ew", padx=30, pady=20)
        
        ctk.CTkButton(frame_btns, text="+ Добавить папку", font=self.fonts['main'], height=40, command=self.add_folder).pack(side="left", padx=(0, 15))
        ctk.CTkButton(frame_btns, text="Очистить список", font=self.fonts['main'], height=40, fg_color="#E74C3C", hover_color="#C0392B", command=self.clear_folders).pack(side="left")

        self.listbox = ctk.CTkTextbox(self, height=100, state="disabled", font=self.fonts['second'], fg_color="#F9F9FB", border_width=1, border_color="#E5E5EA")
        self.listbox.grid(row=3, column=0, sticky="ew", padx=30, pady=(0, 20))
        self.update_list()

        self.btn_start = ctk.CTkButton(self, text="Начать поиск", font=self.fonts['main'], height=45, fg_color="#2FA572", hover_color="#108955", command=self.start_scan)
        self.btn_start.grid(row=4, column=0, sticky="ew", padx=30, pady=(0, 20))

        self.textbox = ctk.CTkTextbox(self, state="disabled", font=self.fonts['second'], fg_color="#F9F9FB", border_width=1, border_color="#E5E5EA")
        self.textbox.grid(row=5, column=0, sticky="nsew", padx=30, pady=(0, 30))

    def log(self, message):
        self.textbox.configure(state="normal")
        self.textbox.insert("end", message + "\n")
        self.textbox.see("end") 
        self.textbox.configure(state="disabled")

    def add_folder(self):
        folder = filedialog.askdirectory()
        if folder and folder not in self.target_folders:
            self.target_folders.append(folder)
            self.update_list()

    def clear_folders(self):
        self.target_folders.clear()
        self.update_list()

    def update_list(self):
        self.listbox.configure(state="normal")
        self.listbox.delete("1.0", "end")
        if not self.target_folders:
            self.listbox.insert("end", "\n  Список папок пуст.\n  Нажмите «+ Добавить папку»")
        else:
            for i, folder in enumerate(self.target_folders, 1):
                self.listbox.insert("end", f"  {i}. {folder}\n")
        self.listbox.configure(state="disabled")

    def start_scan(self):
        if not self.target_folders:
            return self.log("⚠️ Добавьте хотя бы одну папку!")
        self.textbox.configure(state="normal"); self.textbox.delete("1.0", "end"); self.textbox.configure(state="disabled")
        threading.Thread(target=self._run, args=(list(self.target_folders), self.app_state["tolerance"])).start()

    def _run(self, folders, tolerance):
        self.btn_start.configure(state="disabled")
        try:
            self.log("Сбор файлов...")
            all_files = [f for folder in folders for f in get_image_files(folder)]
            if not all_files: return self.log("Картинки не найдены.")
            self.log(f"Собрано {len(all_files)} изображений. Поиск...")
            duplicates = find_duplicates(all_files, tolerance)
            
            if not duplicates:
                self.log("\n✅ Совпадений не найдено.")
            else:
                self.log(f"\n🚨 Найдено {len(duplicates)} групп совпадений:\n")
                for index, group in enumerate(duplicates, 1):
                    self.log(f"--- Группа {index} ---")
                    for path in group:
                        self.log(f" • {os.path.basename(path)}")
                    self.log("") 
        finally:
            self.btn_start.configure(state="normal")