import customtkinter as ctk
import os

from PIL import Image, ImageFont, ImageDraw

from src.config import COLORS
from src.ui.views.view_single import SingleFolderView
from src.ui.views.view_multi import MultiFolderView
from src.ui.views.view_originals import OriginalsView
from src.ui.views.view_settings import SettingsView

ctk.set_appearance_mode("Light") 
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Percepta — Поиск дубликатов")
        self.geometry("950x700")
        self.resizable(False, False) 
        self.configure(fg_color=COLORS["bg_app"])

        # Глобальное состояние (будет доступно во всех экранах)
        self.app_state = {"tolerance": 5}
        self.fonts = self._load_fonts()

        self.grid_columnconfigure(0, minsize=240)
        self.grid_columnconfigure(1, weight=1) 
        self.grid_rowconfigure(0, weight=1)    

        self._build_sidebar()

        # Инициализируем все экраны (они создаются, но пока скрыты)
        view_params = {"fg_color": COLORS["bg_surface"], "corner_radius": 15}
        self.views = {
            "single": SingleFolderView(self, self.app_state, self.fonts, **view_params),
            "multi": MultiFolderView(self, self.app_state, self.fonts, **view_params),
            "originals": OriginalsView(self, self.app_state, self.fonts, **view_params),
            "settings": SettingsView(self, self.app_state, self.fonts, **view_params)
        }

        # Запускаем с экрана поиска оригиналов по умолчанию
        self.select_frame_by_name("single") 

    def _load_fonts(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        fonts_dir = os.path.join(current_dir, "..", "..", "assets", "fonts")
        fonts = {}

        try:
            ctk.FontManager.load_font(os.path.join(fonts_dir, "Rubik-Light.ttf"))
            ctk.FontManager.load_font(os.path.join(fonts_dir, "Rubik-Regular.ttf"))
            ctk.FontManager.load_font(os.path.join(fonts_dir, "Rubik-Bold.ttf"))
            ctk.FontManager.load_font(os.path.join(fonts_dir, "Montserrat-Bold.ttf"))
            
            fonts['main'] = ctk.CTkFont(family='Rubik', size=16)
            fonts['second'] = ctk.CTkFont(family='Rubik Light', size=15)
            fonts['title'] = ctk.CTkFont(family='Montserrat', size=26, weight='bold')
            fonts['subtitle'] = ctk.CTkFont(family='Rubik', size=18, weight='bold')
        except Exception:
            fonts['main'] = fonts['second'] = fonts['title'] = fonts['subtitle'] = None

        fonts['icon_path'] = os.path.join(fonts_dir, "bootstrap-icons.ttf")
            
        return fonts

    def _build_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, corner_radius=0, fg_color=COLORS["bg_surface"])
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_columnconfigure(0, weight=1) 
        self.sidebar_frame.grid_rowconfigure(5, weight=1) 

        ctk.CTkLabel(self.sidebar_frame, text="Percepta", font=self.fonts['title'], text_color=COLORS["primary"]).grid(row=0, column=0, pady=(40, 40))

        # --- Генерация иконок ---
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Коды иконок Bootstrap (папка, папки, поиск, шестеренка)
        icon_single = self.create_font_icon("\uF42A", self.fonts['icon_path'], size=16, color="#333333")
        icon_multi = self.create_font_icon("\uF42B", self.fonts['icon_path'], size=16, color="#333333")
        icon_originals = self.create_font_icon("\uF787", self.fonts['icon_path'], size=16, color="#333333")
        icon_settings = self.create_font_icon("\uF3E5", self.fonts['icon_path'], size=16, color="#333333")

        self.nav_buttons = {}
        
        btn_params = {
            "font": self.fonts['main'], "height": 40, "fg_color": "transparent", 
            "text_color": "gray20", "hover_color": COLORS["bg_app"], "anchor": "w"
        }

        # Добавили image= и по два пробела перед текстом для аккуратного отступа
        self.nav_buttons["single"] = ctk.CTkButton(self.sidebar_frame, text="  Одна папка", image=icon_single, command=lambda: self.select_frame_by_name("single"), **btn_params)
        self.nav_buttons["single"].grid(row=1, column=0, padx=20, pady=5, sticky="ew")

        self.nav_buttons["multi"] = ctk.CTkButton(self.sidebar_frame, text="  Несколько папок", image=icon_multi, command=lambda: self.select_frame_by_name("multi"), **btn_params)
        self.nav_buttons["multi"].grid(row=2, column=0, padx=20, pady=5, sticky="ew")

        self.nav_buttons["originals"] = ctk.CTkButton(self.sidebar_frame, text="  Поиск оригиналов", image=icon_originals, command=lambda: self.select_frame_by_name("originals"), **btn_params)
        self.nav_buttons["originals"].grid(row=3, column=0, padx=20, pady=5, sticky="ew")

        # Настройки на 6 строке (под пружиной)
        self.nav_buttons["settings"] = ctk.CTkButton(self.sidebar_frame, text="  Настройки", image=icon_settings, command=lambda: self.select_frame_by_name("settings"), **btn_params)
        self.nav_buttons["settings"].grid(row=6, column=0, padx=20, pady=(5, 30), sticky="ew")


    def create_font_icon(self, char_code, font_path, size=24, color="gray20"):
        """Рисует векторную иконку на прозрачном фоне"""
        image = Image.new("RGBA", (size, size), (255, 255, 255, 0))
        draw = ImageDraw.Draw(image)
        try:
            font = ImageFont.truetype(font_path, size)
            draw.text((size/2, size/2), char_code, font=font, fill=color, anchor="mm")
        except Exception as e:
            # Теперь мы увидим реальную причину в консоли
            print(f"❌ Ошибка иконки: {e} | Путь: {font_path}") 
            
        return ctk.CTkImage(light_image=image, size=(size, size))


    def select_frame_by_name(self, name):
        # 1. Сбрасываем цвета всех кнопок
        for btn in self.nav_buttons.values():
            btn.configure(fg_color="transparent", text_color=COLORS["text_main"])

        # 2. Скрываем все экраны
        for view in self.views.values():
            view.grid_forget()

        # 3. Подсвечиваем нужную кнопку
        if name == "originals":
            self.nav_buttons[name].configure(fg_color="#EBF5FB", text_color="#2980B9")
        else:
            self.nav_buttons[name].configure(fg_color=COLORS["primary_light"], text_color=COLORS["primary"])

        # 4. Показываем нужный экран
        self.views[name].grid(row=0, column=1, sticky="nsew", padx=30, pady=30)