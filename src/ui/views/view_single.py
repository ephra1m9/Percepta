import os
import threading
import shutil
import customtkinter as ctk

from tkinter import filedialog

from src.config import COLORS, BUTTON_PRIMARY, BUTTON_SECONDARY
from src.utils import get_image_files, update_status
from src.scanner import find_duplicates

class SingleFolderView(ctk.CTkFrame):
    def __init__(self, master, app_state, fonts, **kwargs):
        super().__init__(master, **kwargs)
        self.app_state = app_state
        self.fonts = fonts
        self.target_folder = ""
        self.pending_files = [] 
        
        self._build_ui()
        # Аккуратное пустое состояние при запуске (обычный шрифт, серый цвет)
        self.show_message_state("Папка не выбрана", COLORS["text_muted"], self.fonts['second'])

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1) 

        icon_folder = self.master.create_font_icon("\uF3D1", self.fonts['icon_path'], size=16, color=COLORS["text_main"])
        icon_search = self.master.create_font_icon("\uF52A", self.fonts['icon_path'], size=16, color=COLORS["text_light"])

        # 0. Заголовок
        ctk.CTkLabel(self, text="Одна папка", font=self.fonts['title']).grid(row=0, column=0, sticky="w", padx=30, pady=(30, 20))

        # 1. Описание
        desc_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_input"], corner_radius=8)
        desc_frame.grid(row=1, column=0, padx=30, pady=(0, 30), sticky="ew")
        description = ctk.CTkLabel(desc_frame, text="Поиск дубликатов в одной папке.", text_color=COLORS["text_main"], font=self.fonts['second'], anchor="w")
        description.pack(fill="x", padx=14, pady=14)

        # 2. Выбор папки
        frame_folder = ctk.CTkFrame(self, fg_color="transparent")
        frame_folder.grid(row=2, column=0, sticky="ew", padx=30, pady=(0, 20))
        
        ctk.CTkButton(frame_folder, command=self.select_folder, text="Выбрать папку", font=self.fonts['main'], image=icon_folder, **BUTTON_SECONDARY).pack(side="left")
        self.lbl_folder = ctk.CTkLabel(frame_folder, text="Не выбрано", text_color=COLORS["text_muted"], font=self.fonts['second'])
        self.lbl_folder.pack(side="left", padx=(15, 0), fill="x", expand=True)

        # 3. Кнопка поиска
        self.btn_start = ctk.CTkButton(self, command=self.start_scan, image=icon_search, text="Начать поиск", font=self.fonts['main'], **BUTTON_PRIMARY)
        self.btn_start.grid(row=3, column=0, sticky="ew", padx=30, pady=(0, 20))

        # ==========================================
        # 4. ЦЕНТРАЛЬНАЯ ЗОНА
        # ==========================================
        
        # 4.1 Фрейм для аккуратных системных сообщений (пусто, успех, нет дубликатов)
        self.message_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.lbl_message = ctk.CTkLabel(self.message_frame, text="", justify="center")
        self.lbl_message.place(relx=0.5, rely=0.5, anchor="center") 

        # 4.2 Фрейм со списком результатов
        self.results_frame = ctk.CTkScrollableFrame(self, fg_color="transparent", border_width=1, border_color=COLORS["border"], corner_radius=8)

        # 4.3 Блок кнопок действий
        self.action_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_box = ctk.CTkFrame(self.action_frame, fg_color="transparent")
        btn_box.pack(pady=(10, 20))

        ctk.CTkButton(btn_box, text="Переместить в 'duplicates'", font=self.fonts['main'], **BUTTON_PRIMARY,
                      command=lambda: self.process_duplicates("move")).pack(side="left", padx=5)
        # Красный цвет оставляем только для кнопки деструктивного действия (Apple HIG)
        ctk.CTkButton(btn_box, text="Удалить дубликаты", font=self.fonts['main'], height=45, corner_radius=8, fg_color="#E74C3C", hover_color="#C0392B", text_color="white",
                      command=lambda: self.process_duplicates("delete")).pack(side="left", padx=5)
        ctk.CTkButton(btn_box, text="Отмена", font=self.fonts['main'], **BUTTON_SECONDARY,
                      command=lambda: self.show_message_state("Действие отменено", COLORS["text_muted"], self.fonts['main'])).pack(side="left", padx=5)

        # ==========================================
        
        # 5. ТЕХНИЧЕСКИЙ СТАТУС-БАР
        self.status_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_input"], corner_radius=8, height=40)
        self.status_frame.grid(row=6, column=0, sticky="ew", padx=30, pady=(0, 30))
        self.status_frame.grid_propagate(False) 
        self.lbl_status = ctk.CTkLabel(self.status_frame, text=" Готово к работе", text_color=COLORS["text_muted"], font=self.fonts['second'], anchor="w")
        self.lbl_status.pack(side="left", fill="x", padx=15, pady=10)

    # --- УПРАВЛЕНИЕ ЭКРАНАМИ ---

    def show_message_state(self, text, color, font):
        """Аккуратный текст по центру без визуального шума"""
        self.results_frame.grid_remove()
        self.action_frame.grid_remove()
        
        self.lbl_message.configure(text=text, text_color=color, font=font)
        self.message_frame.grid(row=4, column=0, sticky="nsew", padx=30, pady=(10, 10))

    def show_results_state(self):
        """Отображение списка дубликатов"""
        self.message_frame.grid_remove()
        
        self.results_frame.grid(row=4, column=0, sticky="nsew", padx=30, pady=(10, 10))
        self.action_frame.grid(row=5, column=0, sticky="ew", padx=30, pady=(0, 10))

    # --- ЛОГИКА ПРОГРАММЫ ---

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.target_folder = folder
            folder_name = os.path.basename(folder) or folder
            self.lbl_folder.configure(text=folder_name)
            update_status(self.lbl_status, " Папка обновлена") 
            self.show_message_state("Готово к сканированию", COLORS["text_muted"], self.fonts['main'])

    def start_scan(self):
        if not self.target_folder:
            return self.master.show_error("Папка не выбрана.")
        
        self.btn_start.configure(state="disabled")
        # Спокойное сообщение о процессе
        self.show_message_state("Идет поиск дубликатов...", COLORS["text_main"], self.fonts['main'])
        update_status(self.lbl_status, " Анализ файлов...")
        
        threading.Thread(target=self._run, args=(self.target_folder, self.app_state["tolerance"])).start()

    def _run(self, folder, tolerance):
        try:
            files = get_image_files(folder, recursive=False)
            if not files: 
                self.after(0, lambda: self.show_message_state("Изображения не найдены", COLORS["text_muted"], self.fonts['main']))
                return update_status(self.lbl_status, " Поиск остановлен")
            
            update_status(self.lbl_status, " Сравнение хешей...")
            duplicates = find_duplicates(files, tolerance)
            
            if not duplicates:
                self.after(0, lambda: self.show_message_state("Дубликатов не найдено", COLORS["text_main"], self.fonts['main']))
                update_status(self.lbl_status, " Сканирование завершено")
            else:
                self.pending_files = []
                for group in duplicates:
                    self.pending_files.extend(group[1:])
                
                self.after(0, lambda: self.render_results(duplicates))
                update_status(self.lbl_status, " Ожидание действий пользователя")

        except Exception as e:
            self.after(0, lambda: self.show_message_state("Произошла ошибка при сканировании", "#E74C3C", self.fonts['main']))
            update_status(self.lbl_status, f" Ошибка: {e}")
        finally:
            self.after(0, lambda: self.btn_start.configure(state="normal"))

    def render_results(self, duplicates):
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        for group in duplicates:
            group_frame = ctk.CTkFrame(self.results_frame, fg_color=COLORS["bg_input"], corner_radius=6)
            group_frame.pack(fill="x", pady=(0, 10), padx=5)

            orig_name = os.path.basename(group[0])
            ctk.CTkLabel(group_frame, text=f"{orig_name}", font=self.fonts['main'], text_color=COLORS["text_main"]).pack(anchor="w", padx=15, pady=(10, 5))

            for dup_path in group[1:]:
                dup_name = os.path.basename(dup_path)
                ctk.CTkLabel(group_frame, text=f"↳ {dup_name}", font=self.fonts['second'], text_color=COLORS["text_muted"]).pack(anchor="w", padx=15, pady=(0, 10))

        self.show_results_state()

    def process_duplicates(self, action):
        if not self.pending_files:
            return
            
        count = len(self.pending_files)
        
        try:
            if action == "move":
                dup_folder = os.path.join(self.target_folder, "duplicates")
                os.makedirs(dup_folder, exist_ok=True)
                for file_path in self.pending_files:
                    shutil.move(file_path, os.path.join(dup_folder, os.path.basename(file_path)))
                
                # Спокойное подтверждение базовым шрифтом и темным цветом
                self.show_message_state(f"✅ Перемещено файлов: {count}", COLORS["text_main"], self.fonts['main'])

            elif action == "delete":
                for file_path in self.pending_files:
                    os.remove(file_path)
                    
                # Подтверждение удаления - это успех операции, поэтому цвет обычный, а не красный (алертный)
                self.show_message_state(f"✅ Удалено файлов: {count}", COLORS["text_main"], self.fonts['main'])
                
            self.pending_files = [] 
            update_status(self.lbl_status, " Операция завершена")
                
        except Exception as e:
            self.master.show_error(f"Не удалось обработать файлы:\n{e}")