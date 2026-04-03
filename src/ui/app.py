import os
import threading

import customtkinter as ctk
from tkinter import filedialog

from src.utils import get_image_files
from src.scanner import find_duplicates


ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Percepta")
        self.geometry("650x550")
        self.minsize(600, 500)

        self.target_folder = ""

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # --- Блок выбора папки ---
        self.frame_top = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_top.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        
        self.btn_select_folder = ctk.CTkButton(self.frame_top, text="Выбрать папку для сканирования", command=self.select_folder)
        self.btn_select_folder.pack(side="left", padx=(0, 10))

        self.lbl_folder_path = ctk.CTkLabel(self.frame_top, text="Папка не выбрана", text_color="gray")
        self.lbl_folder_path.pack(side="left", fill="x", expand=True)

        # --- Блок настройки чувствительности ---
        self.frame_settings = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_settings.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        self.lbl_tolerance = ctk.CTkLabel(self.frame_settings, text="Чувствительность: 5 (погрешность)")
        self.lbl_tolerance.pack(anchor="w")

        self.slider_tolerance = ctk.CTkSlider(self.frame_settings, from_=0, to=15, number_of_steps=15, command=self.update_tolerance_label)
        self.slider_tolerance.set(5) # Значение по умолчанию
        self.slider_tolerance.pack(fill="x", pady=(5, 0))

        # --- Кнопка старта ---
        self.btn_start = ctk.CTkButton(self, text="Начать поиск", command=self.start_scan_thread, fg_color="#2FA572", hover_color="#108955")
        self.btn_start.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        # --- Текстовое поле для результатов ---
        self.textbox_results = ctk.CTkTextbox(self, state="disabled")
        self.textbox_results.grid(row=3, column=0, padx=20, pady=(10, 20), sticky="nsew")

    def select_folder(self):
        folder = filedialog.askdirectory(title="Выберите папку с изображениями")
        if folder:
            self.target_folder = folder
            self.lbl_folder_path.configure(text=self.target_folder)

    def update_tolerance_label(self, value):
        self.lbl_tolerance.configure(text=f"Чувствительность: {int(value)} (погрешность)")

    def log_message(self, message):
        """Выводит сообщение в текстовое поле"""
        self.textbox_results.configure(state="normal")
        self.textbox_results.insert("end", message + "\n")
        self.textbox_results.see("end") # Автоскролл вниз
        self.textbox_results.configure(state="disabled")

    def start_scan_thread(self):
        """Запускает сканирование в отдельном потоке, чтобы не заморозить интерфейс"""
        if not self.target_folder:
            self.log_message("⚠️ Ошибка: Сначала выберите папку!")
            return

        self.btn_start.configure(state="disabled", text="Идет сканирование...")
        self.textbox_results.configure(state="normal")
        self.textbox_results.delete("1.0", "end") # Очищаем старые результаты
        self.textbox_results.configure(state="disabled")
        
        self.log_message(f"Начинаем сканирование папки: {self.target_folder}")
        tolerance = int(self.slider_tolerance.get())

        # Запускаем функцию run_scan в фоне
        thread = threading.Thread(target=self.run_scan, args=(self.target_folder, tolerance))
        thread.start()

    def run_scan(self, folder, tolerance):
        """Сама логика сканирования (работает в фоне)"""
        try:
            # 1. Собираем файлы
            self.log_message("Сбор файлов...")
            files = get_image_files(folder)
            self.log_message(f"Найдено изображений: {len(files)}")

            if not files:
                self.log_message("Поиск завершен. Картинки не найдены.")
                return

            # 2. Ищем дубликаты
            self.log_message("Сравнение хешей (это может занять время)...")
            duplicates = find_duplicates(files, tolerance=tolerance)

            # 3. Выводим результат
            if not duplicates:
                self.log_message("✅ Дубликаты не найдены. Все изображения уникальны.")
            else:
                self.log_message(f"🚨 Найдено {len(duplicates)} групп дубликатов:\n")
                for index, group in enumerate(duplicates, 1):
                    self.log_message(f"--- Группа {index} ---")
                    for path in group:
                        # Выводим только имя файла и имя родительской папки, чтобы не загромождать экран длинными путями
                        short_path = os.path.join(os.path.basename(os.path.dirname(path)), os.path.basename(path))
                        self.log_message(f" • {short_path}")
                    self.log_message("") # Пустая строка для отступа
                    
        except Exception as e:
            self.log_message(f"❌ Произошла ошибка: {e}")
            
        finally:
            # Возвращаем кнопку в исходное состояние
            self.btn_start.configure(state="normal", text="Начать поиск")