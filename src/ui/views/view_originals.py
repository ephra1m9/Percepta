import os
import threading
import shutil
import fitz
import customtkinter as ctk

from tkinter import filedialog

import src.ui.ui_components as ui_component
from src.utils import get_image_files
from src.scanner import find_originals


def create_originals_view(parent, app_state, show_error_callback):
    view = ctk.CTkFrame(parent, fg_color="#FFFFFF", corner_radius=15)
    
    content = ctk.CTkFrame(view, fg_color="transparent")
    content.pack(fill="both", expand=True, padx=40, pady=20)
    
    main_container = ctk.CTkFrame(content, fg_color="transparent")
    main_container.pack(fill="both", expand=True)
    main_container.grid_columnconfigure(0, weight=1)
    main_container.grid_rowconfigure(0, weight=1)

    state = {
        "target_low": "",
        "target_server": "",
        "found_files": []
    }

    # Иконки
    icon_folder = parent.create_font_icon("\uF3D1", parent.icon_path, size=15, color=ui_component.COLORS["text_main"])
    icon_search = parent.create_font_icon("\uF52A", parent.icon_path, size=16, color=ui_component.COLORS["text_light"])
    icon_copy_folder = parent.create_font_icon("\uF721", parent.icon_path, size=15, color=ui_component.COLORS["text_main"])
    icon_copy = parent.create_font_icon("\uF759", parent.icon_path, size=15, color=ui_component.COLORS["text_main"])
    icon_replace = parent.create_font_icon("\uF51D", parent.icon_path, size=15, color=ui_component.COLORS["text_main"])
    icon_back = parent.create_font_icon("\uF112", parent.icon_path, size=15, color=ui_component.COLORS["text_main"])

    # ================= ЭКРАН 1: НАСТРОЙКИ =================
    setup_frame = ctk.CTkFrame(main_container, fg_color="transparent")
    setup_frame.grid_columnconfigure(0, weight=1)
    
    ui_component.title(setup_frame, "Поиск оригиналов")
    ui_component.description(
        setup_frame, 
        "Сравнивает две папки и ищет во второй папке изображения, которые уже есть в первой папке, "
        "но в лучшем качестве (больше вес или больше разрешение)."
    )

    frame_low = ctk.CTkFrame(setup_frame, fg_color="transparent", border_width=1, border_color=ui_component.COLORS['border'], corner_radius=10)
    frame_low.grid(row=2, column=0, sticky="ew", pady=(20, 10))
    btn_low = ctk.CTkButton(frame_low, text="Папка на ретушь", image=icon_folder, font=ui_component.FONTS['second_btn'], **ui_component.BUTTON_SECONDARY)
    btn_low.pack(side="left", padx=10, pady=10)
    lbl_low = ctk.CTkLabel(frame_low, text="Сжатые картинки от куратора", text_color=ui_component.COLORS["text_muted"], font=ui_component.FONTS['second'], anchor="e")
    lbl_low.pack(side="left", padx=10, pady=10, fill="x", expand=True) 

    frame_server = ctk.CTkFrame(setup_frame, fg_color="transparent", border_width=1, border_color=ui_component.COLORS['border'], corner_radius=10)
    frame_server.grid(row=3, column=0, sticky="ew", pady=(0, 20))
    btn_server = ctk.CTkButton(frame_server, text="Папка с исходниками", image=icon_folder, font=ui_component.FONTS['second_btn'], **ui_component.BUTTON_SECONDARY)
    btn_server.pack(side="left", padx=10, pady=10)
    lbl_server = ctk.CTkLabel(frame_server, text="Архив / исходники сервера", text_color=ui_component.COLORS["text_muted"], font=ui_component.FONTS['second'], anchor="e")
    lbl_server.pack(side="left", padx=10, pady=10, fill="x", expand=True)

    btn_start = ctk.CTkButton(setup_frame, image=icon_search, text="Найти оригиналы", font=ui_component.FONTS['main'], **ui_component.BUTTON_PRIMARY)
    btn_start.grid(row=4, column=0, sticky="ew")

    lbl_status = ctk.CTkLabel(setup_frame, text="Выберите папки для начала", font=ui_component.FONTS['second'], text_color=ui_component.COLORS["text_muted"])
    lbl_status.grid(row=5, column=0, pady=10)


    # ================= ЭКРАН 2: ЗАГРУЗКА И СООБЩЕНИЯ =================
    message_frame = ctk.CTkFrame(main_container, fg_color="transparent")
    lbl_message_big = ctk.CTkLabel(message_frame, text="", font=ui_component.FONTS['title'], text_color=ui_component.COLORS["text_muted"])
    lbl_message_big.place(relx=0.5, rely=0.5, anchor="center")


    # ================= ЭКРАН 3: РЕЗУЛЬТАТЫ И КАРТОЧКИ =================
    results_frame = ctk.CTkFrame(main_container, fg_color="transparent")

    # 1. Шапка с навигацией
    res_top_bar = ctk.CTkFrame(results_frame, fg_color="transparent")
    res_top_bar.pack(side="top", fill="x", pady=(0, 10))
    
    btn_back = ctk.CTkButton(res_top_bar, text="Назад", image=icon_back, font=ui_component.FONTS['second_btn'], **ui_component.BUTTON_SECONDARY)
    btn_back.pack(side="left")
    lbl_results_header = ctk.CTkLabel(res_top_bar, text="", font=ui_component.FONTS['main'], text_color=ui_component.COLORS["text_main"])
    lbl_results_header.pack(side="right", padx=10)

    # 2. Карточки действий
    actions_grid = ctk.CTkFrame(results_frame, fg_color="transparent")
    actions_grid.pack(side="bottom", fill="x", pady=(10, 0))

    btn_replace = ui_component.result_action_btn(
        actions_grid, 
        "Заменить на оригиналы", 
        "Удаляет сжатые превью и автоматически подставляет на их место найденные оригиналы", 
        icon_replace
    )

    btn_copy = ui_component.result_action_btn(
        actions_grid, 
        "Скопировать оригиналы", 
        "Копирует найденные оригиналы и переименовывает их", 
        icon_copy
    )

    btn_copy_report = ui_component.result_action_btn(
        actions_grid, 
        "Скопировать оригиналы в отдельную папку", 
        "Копирует оригиналы в новую папку 'Found_Originals' и создает текстовый отчет", 
        icon_copy_folder
    )

    # 3. Список результатов
    results_scroll = ctk.CTkScrollableFrame(results_frame, fg_color="transparent", border_width=1, border_color=ui_component.COLORS["border"], corner_radius=8)
    results_scroll.pack(side="top", fill="both", expand=True, pady=(0, 5))


    # --- ЛОГИКА ИНТЕРФЕЙСА ---
    def switch_view(view_name):
        setup_frame.grid_remove()
        message_frame.grid_remove()
        results_frame.grid_remove()

        if view_name == "setup":
            setup_frame.grid(row=0, column=0, sticky="nsew")
        elif view_name == "message":
            message_frame.grid(row=0, column=0, sticky="nsew")
        elif view_name == "results":
            results_frame.grid(row=0, column=0, sticky="nsew")

    def show_message(text):
        lbl_message_big.configure(text=text)
        switch_view("message")

    switch_view("setup")


    # --- ЛОГИКА РАБОТЫ ---
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
            lbl_status.configure(text="Готово к сканированию", text_color=ui_component.COLORS["primary"])
        else:
            lbl_status.configure(text="Выберите папки для начала", text_color=ui_component.COLORS["text_muted"])


    def render_results(results, total_low):
        for widget in results_scroll.winfo_children():
            widget.destroy()

        found_count = len(results['found'])
        not_found_count = len(results['not_found'])

        lbl_results_header.configure(text=f"Найдено: {found_count}   |   Не найдено: {not_found_count}")

        # Вывод НАЙДЕННЫХ
        if found_count > 0:
            for low_path, high_path, page_num in results['found']:
                group_frame = ctk.CTkFrame(results_scroll, fg_color=ui_component.COLORS["bg_surface"], border_width=1, border_color=ui_component.COLORS["border"], corner_radius=6)
                group_frame.pack(fill="x", pady=(0, 10), padx=5)

                low_name = os.path.basename(low_path)
                high_name = os.path.basename(high_path)
                high_dir = os.path.basename(os.path.dirname(high_path))

                page_info = f" (Стр. {page_num})" if page_num else ""

                ctk.CTkLabel(group_frame, text=f"Превью: {low_name}", font=ui_component.FONTS['main'], text_color=ui_component.COLORS["text_main"]).pack(anchor="w", padx=15, pady=(10, 5))
                ctk.CTkLabel(group_frame, text=f"↳ Оригинал: [{high_dir}] {high_name}{page_info}", font=ui_component.FONTS['second'], text_color=ui_component.COLORS["success"]).pack(anchor="w", padx=15, pady=(0, 10))

        # Вывод НЕ НАЙДЕННЫХ
        if not_found_count > 0:
            for nf_path in results['not_found']:
                group_frame = ctk.CTkFrame(results_scroll, fg_color="#FDEDEC", corner_radius=6)
                group_frame.pack(fill="x", pady=(0, 10), padx=5)
                
                nf_name = os.path.basename(nf_path)
                ctk.CTkLabel(group_frame, text=f"❌ {nf_name} (Не найден)", font=ui_component.FONTS['main'], text_color=ui_component.COLORS["error"]).pack(anchor="w", padx=15, pady=(10, 10))

        switch_view("results")


    def process_replace():
        if not state["found_files"]: return
        
        try:
            count = 0
            
            for low_path, high_path, page_num in state["found_files"]:
                low_dir = os.path.dirname(low_path)
                low_name_no_ext, _ = os.path.splitext(os.path.basename(low_path))
                
                if page_num:
                    new_target_path = os.path.join(low_dir, low_name_no_ext + ".png")
                    if os.path.exists(low_path): os.remove(low_path)
                    
                    doc = fitz.open(high_path)
                    page = doc.load_page(page_num - 1)
                    pix = page.get_pixmap(dpi=300)
                    pix.save(new_target_path)
                    doc.close()
                else:
                    _, high_ext = os.path.splitext(high_path)
                    new_target_path = os.path.join(low_dir, low_name_no_ext + high_ext)
                    if os.path.exists(low_path): os.remove(low_path)
                    shutil.copy2(high_path, new_target_path)
                    
                count += 1
            
            show_message(f"Успешно заменено: {count}")
            state["found_files"] = []
            view.after(2500, lambda: switch_view("setup"))
            
        except Exception as e:
            show_error_callback(f"Ошибка при замене:\n{e}")


    def process_copy():
        """Копирует найденные оригиналы"""
        if not state["found_files"]: return
        
        try:
            count = 0
            import fitz
            
            for low_path, high_path, page_num in state["found_files"]:
                low_dir = os.path.dirname(low_path)
                low_name_no_ext, _ = os.path.splitext(os.path.basename(low_path))
                
                if page_num:
                    new_name = f"{low_name_no_ext}_original.png"
                    dest_path = os.path.join(low_dir, new_name)
                    
                    doc = fitz.open(high_path)
                    page = doc.load_page(page_num - 1)
                    pix = page.get_pixmap(dpi=300)
                    pix.save(dest_path)
                    doc.close()
                else:
                    _, high_ext = os.path.splitext(high_path)
                    new_name = f"{low_name_no_ext}_original{high_ext}"
                    dest_path = os.path.join(low_dir, new_name)
                    shutil.copy2(high_path, dest_path)
                    
                count += 1
            
            show_message(f"Скопировано: {count}")
            state["found_files"] = []
            view.after(2500, lambda: switch_view("setup"))
            
        except Exception as e:
            show_error_callback(f"Ошибка при копировании:\n{e}")


    def process_copy_report():
        """Копирует найденные оригиналы в отдельную папку и создает текстовый отчет"""
        if not state["found_files"]: return
        
        try:
            save_dir = os.path.join(state["target_low"], "Found_Originals")
            os.makedirs(save_dir, exist_ok=True)
            
            report_lines = ["Отчет о найденных оригиналах\n", "="*50 + "\n\n"]
            count = 0
            import fitz
            
            for low_path, high_path, page_num in state["found_files"]:
                low_name = os.path.basename(low_path)
                high_name = os.path.basename(high_path)
                
                if page_num:
                    high_name_no_ext, _ = os.path.splitext(high_name)
                    new_high_name = f"{high_name_no_ext}_page_{page_num}.png"
                    dest_path = os.path.join(save_dir, new_high_name)
                    
                    doc = fitz.open(high_path)
                    page = doc.load_page(page_num - 1)
                    pix = page.get_pixmap(dpi=300)
                    pix.save(dest_path)
                    doc.close()
                    
                    report_lines.append(f"Изображение: {low_name}  --->  Оригинал: {high_name} (Стр. {page_num})\n")
                else:
                    shutil.copy2(high_path, os.path.join(save_dir, high_name))
                    report_lines.append(f"Изображение: {low_name}  --->  Оригинал: {high_name}\n")
                    
                count += 1
            
            report_path = os.path.join(save_dir, "_report.txt")
            with open(report_path, "w", encoding="utf-8") as f:
                f.writelines(report_lines)
            
            show_message(f"Сохранено в 'Found_Originals': {count}")
            state["found_files"] = []
            view.after(2500, lambda: switch_view("setup"))
            
        except Exception as e:
            show_error_callback(f"Ошибка при копировании:\n{e}")


    def run_scan(low_folder, server_folder, tolerance):
        """Запускает поиск оригиналов"""
        try:
            low_files = get_image_files(low_folder)
            if not low_files:
                view.after(0, lambda: show_message("В папке с превью пусто"))
                return view.after(2000, lambda: switch_view("setup"))

            server_files = get_image_files(server_folder)
            if not server_files:
                view.after(0, lambda: show_message("В папке сервера пусто"))
                return view.after(2000, lambda: switch_view("setup"))

            results = find_originals(low_files, server_files, tolerance)
            
            state["found_files"] = results['found']
            view.after(0, lambda: render_results(results, len(low_files)))

        except Exception:
            view.after(0, lambda: show_message("Ошибка сканирования"))
            view.after(2000, lambda: switch_view("setup"))
        finally:
            view.after(0, lambda: btn_start.configure(state="normal"))

    # Привязки
    btn_low.configure(command=select_low)
    btn_server.configure(command=select_server)
    btn_back.configure(command=lambda: switch_view("setup"))
    btn_start.configure(command=lambda: (btn_start.configure(state="disabled"), show_message("Сравнение файлов..."), threading.Thread(target=run_scan, args=(state["target_low"], state["target_server"], app_state["tolerance"])).start()))
    btn_replace.configure(command=process_replace)
    btn_copy.configure(command=process_copy)
    btn_copy_report.configure(command=process_copy_report)

    return view