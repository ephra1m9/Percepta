import os
import shutil
import threading
import customtkinter as ctk

from tkinter import filedialog

from src.config import COLORS
from src.utils import get_image_files
from src.scanner import find_originals

class OriginalsView(ctk.CTkFrame):
    def __init__(self, master, app_state, fonts, **kwargs):
        super().__init__(master, **kwargs)
        self.app_state = app_state
        self.fonts = fonts
        self.target_low = ""
        self.target_server = ""
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

        icon_folder = self.master.create_font_icon("\uF3D1", self.fonts['icon_path'], size=18, color="#FFFFFF")

        ctk.CTkLabel(self, text="Поиск оригиналов", font=self.fonts['title']).grid(row=0, column=0, sticky="w", padx=30, pady=(30, 20))

        desc_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_input"], corner_radius=8)
        desc_frame.grid(row=1, column=0, padx=30, pady=(0, 20), sticky="ew")
        description = ctk.CTkLabel(desc_frame, text="Поиск изображений в хорошем (исходном) качестве.", text_color=COLORS["text_main"], font=self.fonts['second'], anchor="w")
        description.pack(fill="x", padx=20, pady=20)

        frame_low = ctk.CTkFrame(self, fg_color="transparent")
        frame_low.grid(row=2, column=0, sticky="ew", padx=30, pady=(0, 10))
        ctk.CTkButton(frame_low, text="Папка на ретушь", image=icon_folder, font=self.fonts['main'], height=40, command=self.select_low).pack(side="left")
        self.lbl_low = ctk.CTkLabel(frame_low, text="Сжатые картинки от куратора", text_color="gray", font=self.fonts['second'])
        self.lbl_low.pack(side="left", padx=(15, 0), fill="x", expand=True) 

        frame_server = ctk.CTkFrame(self, fg_color="transparent")
        frame_server.grid(row=3, column=0, sticky="ew", padx=30, pady=(0, 20))
        ctk.CTkButton(frame_server, text="Папка с исходниками", image=icon_folder, font=self.fonts['main'], height=40, command=self.select_server).pack(side="left")
        self.lbl_server = ctk.CTkLabel(frame_server, text="Папка с архивом/исходниками", text_color="gray", font=self.fonts['second'])
        self.lbl_server.pack(side="left", padx=(15, 0), fill="x", expand=True)

        self.btn_start = ctk.CTkButton(self, text="Найти и скопировать оригиналы", font=self.fonts['main'], height=45, fg_color="#2980B9", hover_color="#1F618D", command=self.start_scan)
        self.btn_start.grid(row=4, column=0, sticky="ew", padx=30, pady=(0, 20))

        self.textbox = ctk.CTkTextbox(self, state="disabled", font=self.fonts['second'], fg_color="#F9F9FB", border_width=1, border_color="#E5E5EA")
        self.textbox.grid(row=5, column=0, sticky="nsew", padx=30, pady=(0, 30))

    def log(self, message):
        self.textbox.configure(state="normal")
        self.textbox.insert("end", message + "\n")
        self.textbox.see("end") 
        self.textbox.configure(state="disabled")

    def select_low(self):
        folder = filedialog.askdirectory()
        if folder:
            self.target_low = folder
            self.lbl_low.configure(text=folder)

    def select_server(self):
        folder = filedialog.askdirectory()
        if folder:
            self.target_server = folder
            self.lbl_server.configure(text=folder)

    def start_scan(self):
        if not self.target_low or not self.target_server:
            return self.log("⚠️ Выберите обе папки!")
        self.textbox.configure(state="normal"); self.textbox.delete("1.0", "end"); self.textbox.configure(state="disabled")
        threading.Thread(target=self._run, args=(self.target_low, self.target_server, self.app_state["tolerance"])).start()

    def _run(self, low_folder, server_folder, tolerance):
        self.btn_start.configure(state="disabled")
        try:
            self.log("1. Сбор файлов с превью...")
            low_files = get_image_files(low_folder)
            if not low_files: return self.log("❌ В папке с превью нет картинок.")

            self.log("2. Сбор файлов с сервера...")
            server_files = get_image_files(server_folder)
            if not server_files: return self.log("❌ В серверной папке нет картинок.")

            self.log(f"\nИщем оригиналы для {len(low_files)} файлов...")
            results = find_originals(low_files, server_files, tolerance)

            found_count = len(results['found'])
            not_found_count = len(results['not_found'])
            
            self.log(f"\n✅ Найдено оригиналов: {found_count}")
            self.log(f"❌ Не удалось найти: {not_found_count}\n")

            if found_count > 0:
                save_dir = os.path.join(low_folder, "Originals_Found")
                os.makedirs(save_dir, exist_ok=True)
                report_lines = ["--- Отчет о поиске ---", f"Найдено: {found_count}", f"Не найдено: {not_found_count}\n", "--- ДЕТАЛИЗАЦИЯ ---"]

                for low_path, high_path in results['found']:
                    low_name, _ = os.path.splitext(os.path.basename(low_path))
                    _, high_ext = os.path.splitext(high_path)
                    
                    new_filename = f"{low_name}_HQ{high_ext}"
                    shutil.copy2(high_path, os.path.join(save_dir, new_filename))
                    
                    report_lines.append(f"Превью: {os.path.basename(low_path)} --> Оригинал: {os.path.basename(high_path)}")
                    self.log(f"Сохранено: {new_filename}")

                if not_found_count > 0:
                    report_lines.append("\n--- НЕ НАЙДЕНО ---")
                    for nf_path in results['not_found']: report_lines.append(os.path.basename(nf_path))

                with open(os.path.join(save_dir, "report.txt"), "w", encoding="utf-8") as f:
                    f.write("\n".join(report_lines))

                self.log(f"\n🎉 Готово! Сохранено в: {save_dir}")
            else:
                self.log("К сожалению, ни один оригинал не найден.")

        except Exception as e:
            self.log(f"\n❌ Ошибка: {e}")
        finally:
            self.btn_start.configure(state="normal")