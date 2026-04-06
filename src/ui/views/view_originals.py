import os
import threading
import shutil
import customtkinter as ctk

from tkinter import filedialog

import src.ui.ui_components as ui_component
from src.utils import get_image_files
from src.scanner import find_originals

def create_originals_view(parent, app_state, show_error_callback):
    
    # --- 1. ГЛАВНЫЙ ФОН И ОБЕРТКА ---
    view = ctk.CTkFrame(parent, fg_color="#FFFFFF", corner_radius=15)
    
    content = ctk.CTkFrame(view, fg_color="transparent")
    content.pack(fill="both", expand=True, padx=40, pady=40)
    
    content.grid_columnconfigure(0, weight=1)
    content.grid_rowconfigure(5, weight=1)

    state = {
        "target_low": "",
        "target_server": "",
        "found_files": []
    }

    # Иконки
    icon_folder = parent.create_font_icon("\uF3D1", parent.icon_path, size=15, color=ui_component.COLORS["text_main"])
    icon_search = parent.create_font_icon("\uF52A", parent.icon_path, size=16, color=ui_component.COLORS["text_light"])
    icon_copy = parent.create_font_icon("\uF721", parent.icon_path, size=15, color=ui_component.COLORS["text_main"])
    icon_replace = parent.create_font_icon("\uF51D", parent.icon_path, size=15, color=ui_component.COLORS["text_main"])
    icon_cancel = parent.create_font_icon("\uF622", parent.icon_path, size=15, color=ui_component.COLORS["error"])

    # 0. Заголовок
    ui_component.title(content, "Поиск оригиналов")
    ui_component.description(content, "Ищет исходники в хорошем качестве на сервере для выбранных превью.")

    # 1. Выбор папок
    frame_low = ctk.CTkFrame(content, fg_color="transparent", border_width=1, border_color=ui_component.COLORS['border'], corner_radius=10)
    frame_low.grid(row=2, column=0, sticky="ew", pady=(0, 10))
    
    btn_low = ctk.CTkButton(frame_low, text="Папка на ретушь", image=icon_folder, font=ui_component.FONTS['second_btn'], **ui_component.BUTTON_SECONDARY)
    btn_low.pack(side="left", padx=10, pady=10)
    lbl_low = ctk.CTkLabel(frame_low, text="Сжатые картинки от куратора", text_color=ui_component.COLORS["text_muted"], font=ui_component.FONTS['second'], anchor="e")
    lbl_low.pack(side="left", padx=10, pady=10, fill="x", expand=True) 

    frame_server = ctk.CTkFrame(content, fg_color="transparent", border_width=1, border_color=ui_component.COLORS['border'], corner_radius=10)
    frame_server.grid(row=3, column=0, sticky="ew", pady=(0, 20))
    
    btn_server = ctk.CTkButton(frame_server, text="Папка с исходниками", image=icon_folder, font=ui_component.FONTS['second_btn'], **ui_component.BUTTON_SECONDARY)
    btn_server.pack(side="left", padx=10, pady=10)
    lbl_server = ctk.CTkLabel(frame_server, text="Архив / исходники сервера", text_color=ui_component.COLORS["text_muted"], font=ui_component.FONTS['second'], anchor="e")
    lbl_server.pack(side="left", padx=10, pady=10, fill="x", expand=True)

    # 2. Кнопка поиска
    btn_start = ctk.CTkButton(content, image=icon_search, text="Найти оригиналы", font=ui_component.FONTS['main'], **ui_component.BUTTON_PRIMARY)
    btn_start.grid(row=4, column=0, sticky="ew", pady=(0, 20))

    # 3. ЦЕНТРАЛЬНАЯ ЗОНА
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

    btn_replace = ctk.CTkButton(btn_box, image=icon_replace, text="Заменить на оригиналы", font=ui_component.FONTS['second_btn'], **ui_component.BUTTON_SECONDARY)
    btn_replace.pack(side="left", padx=5)
    btn_copy = ctk.CTkButton(btn_box, image=icon_copy, text="Собрать в папку", font=ui_component.FONTS['second_btn'], **ui_component.BUTTON_SECONDARY)
    btn_copy.pack(side="left", padx=5)
    btn_cancel = ctk.CTkButton(btn_box, image=icon_cancel, text="Отмена", font=ui_component.FONTS['second_btn'], **ui_component.BUTTON_SECONDARY_DANGER)
    btn_cancel.pack(side="left", padx=5)


    # --- 4. ЛОГИКА ---
    def show_message_state(text, color, font):
        results_container.grid_remove()
        action_frame.grid_remove()
        lbl_message.configure(text=text, text_color=color, font=font)
        message_frame.grid(row=5, column=0, sticky="nsew", pady=(10, 10))

    def show_results_state():
        message_frame.grid_remove()
        results_container.grid(row=5, column=0, sticky="nsew", pady=(10, 10))
        action_frame.grid(row=6, column=0, sticky="ew", pady=(0, 10))

    def select_low():
        folder = filedialog.askdirectory()
        if folder:
            state["target_low"] = folder
            lbl_low.configure(text=os.path.basename(folder) or folder, text_color=ui_component.COLORS['text_main'])
            check_ready()

    def select_server():
        folder = filedialog.askdirectory()
        if folder:
            state["target_server"] = folder
            lbl_server.configure(text=os.path.basename(folder) or folder, text_color=ui_component.COLORS['text_main'])
            check_ready()

    def check_ready():
        if state["target_low"] and state["target_server"]:
            show_message_state("Готово к сканированию", ui_component.COLORS["text_muted"], ui_component.FONTS['main'])

    def render_results(results, total_low):
        for widget in results_frame.winfo_children():
            widget.destroy()

        found_count = len(results['found'])
        not_found_count = len(results['not_found'])

        # Шапка со статистикой
        header_text = f"Проверено: {total_low}   |   Найдено оригиналов: {found_count}   |   Не найдено: {not_found_count}"
        lbl_results_header.configure(text=header_text)

        # Вывод НАЙДЕННЫХ оригиналов
        if found_count > 0:
            for low_path, high_path in results['found']:
                group_frame = ctk.CTkFrame(results_frame, fg_color=ui_component.COLORS["bg_input"], corner_radius=6)
                group_frame.pack(fill="x", pady=(0, 10), padx=5)

                low_name = os.path.basename(low_path)
                high_name = os.path.basename(high_path)
                high_dir = os.path.basename(os.path.dirname(high_path))

                ctk.CTkLabel(group_frame, text=f"Превью: {low_name}", font=ui_component.FONTS['main'], text_color=ui_component.COLORS["text_main"]).pack(anchor="w", padx=15, pady=(10, 5))
                # Выделяем успешное нахождение зелёным цветом
                ctk.CTkLabel(group_frame, text=f"↳ Оригинал: [{high_dir}] {high_name}", font=ui_component.FONTS['second'], text_color=ui_component.COLORS["success"]).pack(anchor="w", padx=15, pady=(0, 10))

        # Вывод НЕ НАЙДЕННЫХ превью
        if not_found_count > 0:
            for nf_path in results['not_found']:
                # Красный фон для ненайденных
                group_frame = ctk.CTkFrame(results_frame, fg_color="#FDEDEC", corner_radius=6)
                group_frame.pack(fill="x", pady=(0, 10), padx=5)
                
                nf_name = os.path.basename(nf_path)
                ctk.CTkLabel(group_frame, text=f"❌ {nf_name} (Оригинал не найден)", font=ui_component.FONTS['main'], text_color=ui_component.COLORS["error"]).pack(anchor="w", padx=15, pady=(10, 10))

        show_results_state()

    def process_replace():
        if not state["found_files"]:
            return
        
        try:
            count = 0
            for low_path, high_path in state["found_files"]:
                # Получаем директорию и имя превью (без расширения)
                low_dir = os.path.dirname(low_path)
                low_name_no_ext, _ = os.path.splitext(os.path.basename(low_path))
                
                # Получаем расширение оригинала
                _, high_ext = os.path.splitext(high_path)
                
                # Формируем новый путь: папка от превью + имя от превью + расширение от оригинала
                new_target_path = os.path.join(low_dir, low_name_no_ext + high_ext)
                
                # 1. Удаляем шакальное превью
                if os.path.exists(low_path):
                    os.remove(low_path)
                    
                # 2. Копируем оригинал на место превью с новым именем
                shutil.copy2(high_path, new_target_path)
                
                count += 1
            
            show_message_state(f"✅ Успешно заменено файлов: {count}\n\nОригиналы подставлены на место превью.", ui_component.COLORS["text_main"], ui_component.FONTS['main'])
            state["found_files"] = []
            
        except Exception as e:
            show_error_callback(f"Ошибка при замене файлов:\n{e}")


    def process_copy_report():
        if not state["found_files"]:
            return
        
        try:
            # Создаем папку Found_Originals внутри папки с превью
            save_dir = os.path.join(state["target_low"], "Found_Originals")
            os.makedirs(save_dir, exist_ok=True)
            
            # Подготавливаем "шапку" для нашего отчета
            report_lines = ["Отчет о найденных оригиналах\n", "="*50 + "\n\n"]
            count = 0
            
            for low_path, high_path in state["found_files"]:
                low_name = os.path.basename(low_path)
                high_name = os.path.basename(high_path)
                
                # 1. Копируем оригинал в новую папку (сохраняя его родное имя)
                shutil.copy2(high_path, os.path.join(save_dir, high_name))
                
                # 2. Добавляем строчку в отчет
                report_lines.append(f"Изображение: {low_name}  --->  Оригинал: {high_name}\n")
                count += 1
            
            # 3. Сохраняем текстовый файл с отчетом
            report_path = os.path.join(save_dir, "_report.txt")
            with open(report_path, "w", encoding="utf-8") as f:
                f.writelines(report_lines)
            
            show_message_state(f"✅ Успешно скопировано файлов: {count}\n\nОригиналы и 'report.txt' сохранены в папку 'Found_Originals'.", ui_component.COLORS["text_main"], ui_component.FONTS['main'])
            state["found_files"] = []
            
        except Exception as e:
            show_error_callback(f"Ошибка при копировании:\n{e}")


    def run_scan(low_folder, server_folder, tolerance):
        try:
            low_files = get_image_files(low_folder)
            if not low_files:
                return view.after(0, lambda: show_message_state("В папке с превью нет изображений", ui_component.COLORS["text_muted"], ui_component.FONTS['main']))

            server_files = get_image_files(server_folder)
            if not server_files:
                return view.after(0, lambda: show_message_state("В папке сервера нет изображений", ui_component.COLORS["text_muted"], ui_component.FONTS['main']))

            total_low = len(low_files)
            view.after(0, lambda: show_message_state("Поиск оригиналов...", ui_component.COLORS["text_muted"], ui_component.FONTS['main']))
            
            results = find_originals(low_files, server_files, tolerance)
            
            state["found_files"] = results['found']
            view.after(0, lambda: render_results(results, total_low))

        except Exception as e:
            view.after(0, lambda: show_message_state("Произошла ошибка при сканировании", "#E74C3C", ui_component.FONTS['main']))
        finally:
            view.after(0, lambda: btn_start.configure(state="normal"))

    def start_scan():
        if not state["target_low"] or not state["target_server"]:
            return show_error_callback("Выберите обе папки!")
        
        btn_start.configure(state="disabled")
        show_message_state("Сбор файлов...", ui_component.COLORS["text_muted"], ui_component.FONTS['main'])
        
        threading.Thread(target=run_scan, args=(state["target_low"], state["target_server"], app_state["tolerance"])).start()

    # --- 5. ПРИВЯЗКА СОБЫТИЙ ---
    btn_low.configure(command=select_low)
    btn_server.configure(command=select_server)
    btn_start.configure(command=start_scan)
    btn_replace.configure(command=process_replace)
    btn_copy.configure(command=process_copy_report)
    btn_cancel.configure(command=lambda: show_message_state("Действие отменено", ui_component.COLORS["text_muted"], ui_component.FONTS['main']))

    show_message_state("Папки не выбраны", ui_component.COLORS["text_muted"], ui_component.FONTS['second'])

    return view