import customtkinter as ctk
import os

from PIL import Image, ImageFont, ImageDraw

# ДОБАВИЛИ ИМПОРТ FONTS
from src.ui.ui_components import COLORS, FONTS
from src.ui.views.view_single import create_single_folder_view
from src.ui.views.view_multi import create_multi_folder_view
from src.ui.views.view_originals import create_originals_view
from src.ui.views.view_settings import create_settings_view

ctk.set_appearance_mode("Light") 
ctk.set_default_color_theme("blue")

def load_fonts():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    fonts_dir = os.path.join(current_dir, "..", "..", "assets", "fonts")

    try:
        ctk.FontManager.load_font(os.path.join(fonts_dir, "Rubik-Light.ttf"))
        ctk.FontManager.load_font(os.path.join(fonts_dir, "Rubik-Regular.ttf"))
        ctk.FontManager.load_font(os.path.join(fonts_dir, "Rubik-Bold.ttf"))
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

# Убрали аргумент fonts, так как мы импортировали FONTS глобально
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

    # Используем FONTS['main']
    lbl = ctk.CTkLabel(modal, text=message, font=FONTS['main'], text_color=COLORS.get("text_second", "gray"), wraplength=350)
    lbl.grid(row=0, column=0, padx=20, pady=(30, 10))

    btn = ctk.CTkButton(modal, text="Закрыть", fg_color=COLORS.get("error", "#E74C3C"), hover_color=COLORS.get("error", "#E74C3C"), corner_radius=10, command=modal.destroy)
    btn.grid(row=1, column=0, pady=(0, 30))

def main():
    root = ctk.CTk()
    root.title("Percepta — Поиск дубликатов")
    root.geometry("970x800")
    root.resizable(False, False) 
    root.configure(fg_color=COLORS["bg_app"])

    root.create_font_icon = create_font_icon

    app_state = {"tolerance": 5}
    icon_path = load_fonts()
    root.icon_path = icon_path

    root.grid_columnconfigure(0, minsize=240)
    root.grid_columnconfigure(1, weight=1) 
    root.grid_rowconfigure(0, weight=1)    

    # --- SIDEBAR ---
    sidebar_frame = ctk.CTkFrame(root, corner_radius=0, fg_color=COLORS["bg_surface"])
    sidebar_frame.grid(row=0, column=0, sticky="nsew")
    sidebar_frame.grid_columnconfigure(0, weight=1) 
    sidebar_frame.grid_rowconfigure(5, weight=1) 

    # Используем FONTS['title']
    ctk.CTkLabel(sidebar_frame, text="Percepta", font=FONTS['title'], text_color=COLORS["primary"]).grid(row=0, column=0, pady=(40, 40))

    icon_single = create_font_icon("\uF42A", icon_path, size=16, color="#333333")
    icon_multi = create_font_icon("\uF42B", icon_path, size=16, color="#333333")
    icon_originals = create_font_icon("\uF787", icon_path, size=16, color="#333333")
    icon_settings = create_font_icon("\uF3E5", icon_path, size=16, color="#333333")

    nav_buttons = {}
    btn_params = {
        "font": FONTS['main'], "height": 40, "fg_color": "transparent",  # Используем FONTS['main']
        "text_color": "gray20", "hover_color": COLORS["bg_app"], "anchor": "w"
    }

    nav_buttons["single"] = ctk.CTkButton(sidebar_frame, text="  Одна папка", image=icon_single, **btn_params)
    nav_buttons["single"].grid(row=1, column=0, padx=20, pady=5, sticky="ew")

    nav_buttons["multi"] = ctk.CTkButton(sidebar_frame, text="  Несколько папок", image=icon_multi, **btn_params)
    nav_buttons["multi"].grid(row=2, column=0, padx=20, pady=5, sticky="ew")

    nav_buttons["originals"] = ctk.CTkButton(sidebar_frame, text="  Поиск оригиналов", image=icon_originals, **btn_params)
    nav_buttons["originals"].grid(row=3, column=0, padx=20, pady=5, sticky="ew")

    nav_buttons["settings"] = ctk.CTkButton(sidebar_frame, text="  Настройки", image=icon_settings, **btn_params)
    nav_buttons["settings"].grid(row=6, column=0, padx=20, pady=(5, 30), sticky="ew")

    def error_callback(msg):
        show_error_modal(root, msg) # Убрали fonts из вызова

    # --- ИНИЦИАЛИЗАЦИЯ ЭКРАНОВ ---
    views = {
        "single": create_single_folder_view(root, app_state, error_callback),
        "multi": create_multi_folder_view(root, app_state, error_callback),
        "originals": create_originals_view(root, app_state, error_callback),
        "settings": create_settings_view(root, app_state, error_callback)
    }

    for view in views.values():
        view.configure(fg_color=COLORS["bg_surface"], corner_radius=15)

    def select_frame_by_name(name):
        for btn in nav_buttons.values():
            btn.configure(fg_color="transparent", text_color=COLORS["text_main"])
        for view in views.values():
            view.grid_forget()

        nav_buttons[name].configure(fg_color=COLORS.get("primary_light", "lightblue"), text_color=COLORS["primary"])
        views[name].grid(row=0, column=1, sticky="nsew", padx=30, pady=30)

    nav_buttons["single"].configure(command=lambda: select_frame_by_name("single"))
    nav_buttons["multi"].configure(command=lambda: select_frame_by_name("multi"))
    nav_buttons["originals"].configure(command=lambda: select_frame_by_name("originals"))
    nav_buttons["settings"].configure(command=lambda: select_frame_by_name("settings"))

    select_frame_by_name("single") 
    root.mainloop()

if __name__ == "__main__":
    main()