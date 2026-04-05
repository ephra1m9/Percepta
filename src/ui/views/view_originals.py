import os
import shutil
import threading
import customtkinter as ctk

from tkinter import filedialog

import src.ui.ui_components as ui_component
from src.utils import get_image_files
from src.scanner import find_originals

def create_originals_view(parent, app_state, show_error_callback):
    view = ctk.CTkFrame(parent)
    state = {"target_low": "", "target_server": ""}

    view.grid_columnconfigure(0, weight=1)
    view.grid_rowconfigure(4, weight=1)

    icon_folder = parent.create_font_icon("\uF3D1", parent.icon_path, size=18, color="#FFFFFF") if hasattr(parent, 'create_font_icon') else None

    ctk.CTkLabel(view, text="Поиск оригиналов", font=ui_component.FONTS['title']).grid(row=0, column=0, sticky="w", padx=30, pady=(30, 20))

    desc_frame = ctk.CTkFrame(view, fg_color=ui_component.COLORS["bg_input"], corner_radius=8)
    desc_frame.grid(row=1, column=0, padx=30, pady=(0, 20), sticky="ew")
    description = ctk.CTkLabel(desc_frame, text="Поиск изображений в хорошем (исходном) качестве.", text_color=ui_component.COLORS["text_main"], font=ui_component.FONTS['second'], anchor="w")
    description.pack(fill="x", padx=14, pady=14)

    frame_low = ctk.CTkFrame(view, fg_color="transparent")
    frame_low.grid(row=2, column=0, sticky="ew", padx=30, pady=(0, 10))
    btn_low = ctk.CTkButton(frame_low, text="Папка на ретушь", image=icon_folder, font=ui_component.FONTS['main'], height=40)
    btn_low.pack(side="left")
    lbl_low = ctk.CTkLabel(frame_low, text="Сжатые картинки от куратора", text_color="gray", font=ui_component.FONTS['second'])
    lbl_low.pack(side="left", padx=(15, 0), fill="x", expand=True) 

    frame_server = ctk.CTkFrame(view, fg_color="transparent")
    frame_server.grid(row=3, column=0, sticky="ew", padx=30, pady=(0, 20))
    btn_server = ctk.CTkButton(frame_server, text="Папка с исходниками", image=icon_folder, font=ui_component.FONTS['main'], height=40)
    btn_server.pack(side="left")
    lbl_server = ctk.CTkLabel(frame_server, text="Папка с архивом/исходниками", text_color="gray", font=ui_component.FONTS['second'])
    lbl_server.pack(side="left", padx=(15, 0), fill="x", expand=True)

    btn_start = ctk.CTkButton(view, text="Найти и скопировать оригиналы", font=ui_component.FONTS['main'], height=45, fg_color="#2980B9", hover_color="#1F618D")
    btn_start.grid(row=4, column=0, sticky="ew", padx=30, pady=(0, 20))

    textbox = ctk.CTkTextbox(view, state="disabled", font=ui_component.FONTS['second'], fg_color="#F9F9FB", border_width=1, border_color="#E5E5EA")
    textbox.grid(row=5, column=0, sticky="nsew", padx=30, pady=(0, 30))

    def log(message):
        textbox.configure(state="normal")
        textbox.insert("end", message + "\n")
        textbox.see("end") 
        textbox.configure(state="disabled")

    def select_low():
        folder = filedialog.askdirectory()
        if folder:
            state["target_low"] = folder
            lbl_low.configure(text=folder)

    def select_server():
        folder = filedialog.askdirectory()
        if folder:
            state["target_server"] = folder
            lbl_server.configure(text=folder)

    def run_scan(low_folder, server_folder, tolerance):
        btn_start.configure(state="disabled")
        try:
            log("1. Сбор файлов с превью...")
            low_files = get_image_files(low_folder)
            if not low_files: return log("❌ В папке с превью нет картинок.")

            log("2. Сбор файлов с сервера...")
            server_files = get_image_files(server_folder)
            if not server_files: return log("❌ В серверной папке нет картинок.")

            log(f"\nИщем оригиналы для {len(low_files)} файлов...")
            results = find_originals(low_files, server_files, tolerance)

            found_count = len(results['found'])
            not_found_count = len(results['not_found'])
            
            log(f"\n✅ Найдено оригиналов: {found_count}")
            log(f"❌ Не удалось найти: {not_found_count}\n")

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
                    log(f"Сохранено: {new_filename}")

                if not_found_count > 0:
                    report_lines.append("\n--- НЕ НАЙДЕНО ---")
                    for nf_path in results['not_found']: report_lines.append(os.path.basename(nf_path))

                with open(os.path.join(save_dir, "report.txt"), "w", encoding="utf-8") as f:
                    f.write("\n".join(report_lines))

                log(f"\n🎉 Готово! Сохранено в: {save_dir}")
            else:
                log("К сожалению, ни один оригинал не найден.")

        except Exception as e:
            log(f"\n❌ Ошибка: {e}")
        finally:
            view.after(0, lambda: btn_start.configure(state="normal"))

    def start_scan():
        if not state["target_low"] or not state["target_server"]:
            return log("⚠️ Выберите обе папки!")
        textbox.configure(state="normal")
        textbox.delete("1.0", "end")
        textbox.configure(state="disabled")
        threading.Thread(target=run_scan, args=(state["target_low"], state["target_server"], app_state["tolerance"])).start()

    btn_low.configure(command=select_low)
    btn_server.configure(command=select_server)
    btn_start.configure(command=start_scan)

    return view