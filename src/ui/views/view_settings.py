import customtkinter as ctk

from src.config import COLORS

class SettingsView(ctk.CTkFrame):
    def __init__(self, master, app_state, fonts, **kwargs):
        super().__init__(master, **kwargs)
        self.app_state = app_state
        self.fonts = fonts
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(self, text="Настройки программы", font=self.fonts['title']).grid(row=0, column=0, sticky="w", padx=30, pady=(30, 30))

        card = ctk.CTkFrame(self, fg_color="#F9F9FB", corner_radius=10, border_width=1, border_color="#E5E5EA")
        card.grid(row=1, column=0, sticky="ew", padx=30, pady=(0, 20))
        card.grid_columnconfigure(0, weight=1)

        self.lbl_tolerance = ctk.CTkLabel(card, text=f"Чувствительность алгоритма: {self.app_state['tolerance']}", font=self.fonts['subtitle'])
        self.lbl_tolerance.grid(row=0, column=0, sticky="w", padx=25, pady=(25, 5))

        desc = "Определяет допустимую разницу между картинками.\n0 — только точные копии, 5-10 — находит слегка сжатые или отретушированные фото."
        ctk.CTkLabel(card, text=desc, font=self.fonts['second'], text_color="gray", justify="left").grid(row=1, column=0, sticky="w", padx=25, pady=(0, 20))

        slider = ctk.CTkSlider(card, from_=0, to=15, number_of_steps=15, command=self.update_tolerance)
        slider.set(self.app_state['tolerance'])
        slider.grid(row=2, column=0, sticky="ew", padx=25, pady=(0, 30))

    def update_tolerance(self, value):
        val = int(value)
        self.app_state['tolerance'] = val
        self.lbl_tolerance.configure(text=f"Чувствительность алгоритма: {val}")