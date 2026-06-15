import os
import customtkinter as ctk

from PIL import Image, ImageFont, ImageDraw

import ui.ui_components as ui_component
import utils.config as cfg

from .pages.page_duplicates import create_dublicates_view
from .pages.page_originals import create_originals_view


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
    root.geometry("1000x700")
    root.minsize(800, 600)
    root.configure(fg_color="#F7FAFC")

    root.create_font_icon = create_font_icon

    app_state = {
        "tolerance": 7,
        "search_recursive": 0,
        "phash_threshold": 25,
        "quality_ratio": 1.2
    }
    icon_path = load_fonts()
    root.icon_path = icon_path

    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(0, weight=1)

    def error_callback(msg):
        show_error_modal(root, msg)

    # --- СОЗДАНИЕ КОНТЕЙНЕРОВ И ЭКРАНОВ ---
    views_containers = {}
    views = {}
    
    # Имена экранов
    screen_names = ["single", "originals"]

    for name in screen_names:
        container = ctk.CTkFrame(root, fg_color="transparent")
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)
        
        container.create_font_icon = create_font_icon
        container.icon_path = icon_path

        bg_canvas = ui_component.create_gradient_canvas(container, panel_mode="page")

        back_icon = create_font_icon("\uF12F", icon_path, size=20, color=ui_component.COLORS["text_main"])
        back_btn = ctk.CTkButton(container, text=" Назад", image=back_icon, fg_color="white", bg_color="#F7FAFC", text_color=ui_component.COLORS["text_main"], hover_color="white", border_width=1, border_color=ui_component.COLORS["border"], width=100, corner_radius=8, command=lambda: show_main_screen())
        back_btn.place(x=30, y=20)
        back_btn.bind("<Enter>", lambda e, b=back_btn: b.configure(border_color=ui_component.COLORS["primary"]))
        back_btn.bind("<Leave>", lambda e, b=back_btn: b.configure(border_color=ui_component.COLORS["border"]))

        def _update_btn_bg(event, btn=back_btn, cvs=bg_canvas):
            if hasattr(cvs, '_bg_image_rgb') and event.width > 60 and event.height > 40:
                px = min(80, event.width - 1)
                py = min(36, event.height - 1)
                r, g, b = cvs._bg_image_rgb.getpixel((px, py))
                btn.configure(bg_color=f"#{r:02x}{g:02x}{b:02x}")
        bg_canvas.bind("<Configure>", _update_btn_bg, add="+")
        
        views_containers[name] = container

    views["single"] = create_dublicates_view(views_containers["single"], app_state, error_callback)
    views["originals"] = create_originals_view(views_containers["originals"], app_state, error_callback)

    for name, view in views.items():
        view.grid(row=0, column=0, sticky="nsew", padx=50, pady=(100, 50))

    # --- MAIN SCREEN ---
    main_frame = ctk.CTkFrame(root, fg_color="transparent")
    main_frame.grid(row=0, column=0, sticky="nsew")
    main_frame.grid_columnconfigure(0, weight=1)
    main_frame.grid_rowconfigure(0, weight=1)

    # Градиентный фон с белой панелью по центру
    ui_component.create_gradient_canvas(main_frame, panel_mode="center")

    # Белый контейнер поверх Canvas-панели.
    center_panel = ctk.CTkFrame(main_frame, fg_color="#FFFFFF", corner_radius=0, width=510, height=380)
    center_panel.place(relx=0.5, rely=0.5, anchor="center")
    center_panel.grid_propagate(False)
    center_panel.grid_columnconfigure(0, weight=1)

    lbl_title = ctk.CTkLabel(center_panel, text="Найди мне...", font=("Montserrat", 24), text_color=ui_component.COLORS["text_main"])
    lbl_title.grid(row=0, column=0, pady=(25, 15))

    buttons_container = ctk.CTkFrame(center_panel, fg_color="transparent")
    buttons_container.grid(row=1, column=0, sticky="ew", padx=30)

    icon_single = create_font_icon("\uF42B", icon_path, size=28, color=ui_component.COLORS["primary"])
    ui_component.main_menu_btn(
        buttons_container, 
        "Дубликаты", 
        "Найди одинаковые изображения", 
        icon_single,
        lambda: select_view("single")
    )

    icon_originals = create_font_icon("\uF787", icon_path, size=28, color=ui_component.COLORS["primary"])
    ui_component.main_menu_btn(
        buttons_container, 
        "Оригиналы", 
        "Найди изображения в лучшем качестве", 
        icon_originals,
        lambda: select_view("originals")
    )

    def select_view(name):
        main_frame.grid_forget()
        for v in views_containers.values():
            v.grid_forget()
        views_containers[name].grid(row=0, column=0, sticky="nsew")

    def show_main_screen():
        for v in views_containers.values():
            v.grid_forget()
        main_frame.grid(row=0, column=0, sticky="nsew")

    show_main_screen()
    root.mainloop()


if __name__ == "__main__":
    main()
