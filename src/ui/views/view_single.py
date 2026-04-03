import os
import threading
import customtkinter as ctk

from tkinter import filedialog

from src.config import COLORS
from src.utils import get_image_files
from src.scanner import find_duplicates

class SingleFolderView(ctk.CTkFrame):
    def __init__(self, master, app_state, fonts, **kwargs):
        super().__init__(master, **kwargs)
        self.app_state = app_state
        self.fonts = fonts
        self.target_folder = ""
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(self, text="Поиск дубликатов в одной папке", font=self.fonts['title']).grid(row=0, column=0, sticky="w", padx=30, pady=(30, 20))

        frame_folder = ctk.CTkFrame(self, fg_color="transparent")
        frame_folder.grid(row=1, column=0, sticky="ew", padx=30, pady=(0, 20))
        
        ctk.CTkButton(frame_folder, text="Выбрать папку", font=self.fonts['main'], height=40, command=self.select_folder).pack(side="left")
        self.lbl_folder = ctk.CTkLabel(frame_folder, text="Папка не выбрана", text_color="gray", font=self.fonts['second'])
        self.lbl_folder.pack(side="left", padx=(15, 0), fill="x", expand=True)

        self.btn_start = ctk.CTkButton(self, text="Начать поиск", font=self.fonts['main'], height=45, fg_color="#2FA572", hover_color="#108955", command=self.start_scan)
        self.btn_start.grid(row=2, column=0, sticky="ew", padx=30, pady=(0, 20))

        self.textbox = ctk.CTkTextbox(self, state="disabled", font=self.fonts['second'], fg_color="#F9F9FB", border_width=1, border_color="#E5E5EA")
        self.textbox.grid(row=3, column=0, sticky="nsew", padx=30, pady=(0, 30))

    def log(self, message):
        self.textbox.configure(state="normal")
        self.textbox.insert("end", message + "\n")
        self.textbox.see("end") 
        self.textbox.configure(state="disabled")

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.target_folder = folder
            self.lbl_folder.configure(text=folder)

    def start_scan(self):
        if not self.target_folder:
            return self.log("⚠️ Выберите папку!")
        self.textbox.configure(state="normal"); self.textbox.delete("1.0", "end"); self.textbox.configure(state="disabled")
        threading.Thread(target=self._run, args=(self.target_folder, self.app_state["tolerance"])).start()

    def _run(self, folder, tolerance):
        self.btn_start.configure(state="disabled")
        try:
            self.log("Сбор файлов...")
            files = get_image_files(folder)
            if not files: return self.log("Картинки не найдены.")
            self.log("Сравнение хешей...")
            duplicates = find_duplicates(files, tolerance)
            
            if not duplicates:
                self.log("\n✅ Совпадений не найдено. Все изображения уникальны.")
            else:
                self.log(f"\n🚨 Найдено {len(duplicates)} групп совпадений:\n")
                for index, group in enumerate(duplicates, 1):
                    self.log(f"--- Группа {index} ---")
                    for path in group:
                        self.log(f" • {os.path.basename(path)}")
                    self.log("") 
        finally:
            self.btn_start.configure(state="normal")