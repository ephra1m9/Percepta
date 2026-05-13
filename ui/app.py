import os
import customtkinter as ctk

from PIL import Image, ImageFont, ImageDraw

import ui.ui_components as ui_component
import utils.config as cfg

from .pages.page_duplicates import create_dublicates_view
from .pages.page_reference import create_reference_view
from .pages.page_originals import create_originals_view
from .pages.page_settings import create_settings_view


ctk.set_appearance_mode("Light") 
ctk.set_default_color_theme("blue")


def load_fonts():
    """Загружает шрифты"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    fonts_dir = os.path.join(current_dir, "..", "assets", "fonts")

    try:
        ctk.FontManager.load_font(os.path.join(fonts_dir, "Rubik-Light.ttf"))
        ctk.FontManager.load_font(os.path.join(fonts_dir, "Rubik-Regular.ttf"))
        ctk.FontManager.load_font(os.path.join(fonts_dir, "Rubik-Bold.ttf"))
        ctk.FontManager.load_font(os.path.join(fonts_dir, "Montserrat-SemiBold.ttf"))
        ctk.FontManager.load_font(os.path.join(fonts_dir, "Montserrat-Bold.ttf"))
    except Exception as e:
        print(f"Ошибка загрузки шрифтов: {e}")

    return os.path.join(fonts_dir, "bootstrap-icons.ttf")


def create_font_icon(char_code, font_path, size=24, color="gray20"):
    """Рисует векторную иконку на прозрачном фоне"""
    image = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype(font_path, size)
        draw.text((size/2, size/2), char_code, font=font, fill=color, anchor="mm")
    except Exception as e:
        print(f"❌ Ошибка иконки: {e} | Путь: {font_path}") 
        
    return ctk.CTkImage(light_image=image, size=(size, size))


def show_error_modal(root, message):
    """Создает и показывает модальное окно с ошибкой"""
    modal = ctk.CTkToplevel(root)
    modal.title("Ошибка")
    modal_width = 400
    modal_height = 200

    root.update_idletasks()
    main_x, main_y = root.winfo_x(), root.winfo_y()
    main_width, main_height = root.winfo_width(), root.winfo_height()

    pos_x = main_x + (main_width // 2) - (modal_width // 2)
    pos_y = main_y + (main_height // 2) - (modal_height // 2)

    modal.geometry(f"{modal_width}x{modal_height}+{pos_x}+{pos_y}")
    modal.resizable(False, False)
    modal.transient(root)
    modal.grab_set()

    modal.grid_columnconfigure(0, weight=1)
    modal.grid_rowconfigure(0, weight=1)

    lbl = ctk.CTkLabel(modal, text=message, font=ui_component.FONTS['main'], text_color=ui_component.COLORS.get("text_second", "gray"), wraplength=350)
    lbl.grid(row=0, column=0, padx=20, pady=(30, 10))

    btn = ctk.CTkButton(modal, text="Закрыть", fg_color=ui_component.COLORS.get("error", "#E74C3C"), hover_color=ui_component.COLORS.get("error", "#E74C3C"), corner_radius=10, command=modal.destroy)
    btn.grid(row=1, column=0, pady=(0, 30))


def main():
    root = ctk.CTk()
    root.title(cfg.APP_TITLE)
    root.geometry(cfg.APP_SIZE)
    root.minsize(800, 500)
    root.configure(fg_color=ui_component.COLORS["bg_app"])

    root.create_font_icon = create_font_icon

    app_state = {
        "tolerance": 7,
        "search_recursive": 0,
        "phash_threshold": 25,
        "quality_ratio": 1.2
    }
    icon_path = load_fonts()
    root.icon_path = icon_path

    root.grid_columnconfigure(0, minsize=240)
    root.grid_columnconfigure(1, weight=1) 
    root.grid_rowconfigure(0, weight=1)    

    # --- SIDEBAR ---
    sidebar_frame = ctk.CTkFrame(root, corner_radius=0, fg_color=ui_component.COLORS["bg_surface"])
    sidebar_frame.grid(row=0, column=0, sticky="nsew")
    sidebar_frame.grid_columnconfigure(0, weight=1) 
    sidebar_frame.grid_rowconfigure(6, weight=1) 

    ctk.CTkLabel(sidebar_frame, text="Percepta", font=ui_component.FONTS['title'], text_color=ui_component.COLORS["primary"]).grid(row=0, column=0, pady=(40, 40))

    # Иконки
    icon_single = create_font_icon("\uF42B", icon_path, size=16, color=ui_component.COLORS["text_main"])
    icon_multi = create_font_icon("\uF5A9", icon_path, size=16, color=ui_component.COLORS["text_main"])
    icon_originals = create_font_icon("\uF787", icon_path, size=16, color=ui_component.COLORS["text_main"])
    icon_settings = create_font_icon("\uF3E5", icon_path, size=16, color=ui_component.COLORS["text_main"])

    # Кнопки
    nav_buttons = {}

    nav_buttons["single"] = ctk.CTkButton(sidebar_frame, text="  Поиск дубликатов", image=icon_single, **ui_component.BUTTON_SIDEBAR)
    nav_buttons["single"].grid(row=1, column=0, padx=20, pady=5, sticky="ew")

    nav_buttons["multi"] = ctk.CTkButton(sidebar_frame, text="  Поиск по эталону", image=icon_multi, **ui_component.BUTTON_SIDEBAR)
    nav_buttons["multi"].grid(row=2, column=0, padx=20, pady=5, sticky="ew")

    nav_buttons["originals"] = ctk.CTkButton(sidebar_frame, text="  Поиск оригиналов", image=icon_originals, **ui_component.BUTTON_SIDEBAR)
    nav_buttons["originals"].grid(row=3, column=0, padx=20, pady=5, sticky="ew")

    nav_buttons["settings"] = ctk.CTkButton(sidebar_frame, text="  Настройки", image=icon_settings, **ui_component.BUTTON_SIDEBAR)
    nav_buttons["settings"].grid(row=7, column=0, padx=20, sticky="ew")

    ui_component.hr_grid(sidebar_frame, row=8, pady=20)

    ctk.CTkLabel(sidebar_frame, text=f"v. {cfg.VERSION}", font=ui_component.FONTS['second'], text_color=ui_component.COLORS['text_second']).grid(row=9, column=0, padx=20, pady=(0, 30))

    def error_callback(msg):
        show_error_modal(root, msg)

    # --- ИНИЦИАЛИЗАЦИЯ ЭКРАНОВ ---
    views = {
        "single": create_dublicates_view(root, app_state, error_callback),
        "multi": create_reference_view(root, app_state, error_callback),
        "originals": create_originals_view(root, app_state, error_callback),
        "settings": create_settings_view(root, app_state, error_callback)
    }

    # for view in views.values():
    #     view.configure(fg_color=ui_component.COLORS["bg_surface"], corner_radius=15)

    def select_frame_by_name(name):
        for btn in nav_buttons.values():
            btn.configure(fg_color="transparent", text_color=ui_component.COLORS["text_main"])
        for view in views.values():
            view.grid_forget()

        nav_buttons[name].configure(fg_color=ui_component.COLORS.get("primary_light", "lightblue"))
        views[name].grid(row=0, column=1, sticky="nsew", padx=30, pady=30)

    # Прявязка событий к кнопкам
    nav_buttons["single"].configure(command=lambda: select_frame_by_name("single"))
    nav_buttons["multi"].configure(command=lambda: select_frame_by_name("multi"))
    nav_buttons["originals"].configure(command=lambda: select_frame_by_name("originals"))
    nav_buttons["settings"].configure(command=lambda: select_frame_by_name("settings"))

    select_frame_by_name("single") 
    root.mainloop()


if __name__ == "__main__":
    main()