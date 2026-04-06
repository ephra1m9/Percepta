import customtkinter as ctk

import src.ui.ui_components as ui_component

def create_settings_view(parent, app_state, show_error_callback=None):
    view = ctk.CTkFrame(parent)

    view.grid_columnconfigure(0, weight=1)
    view.grid_rowconfigure(2, weight=1)

    ctk.CTkLabel(view, text="Настройки программы", font=ui_component.FONTS['title']).grid(row=0, column=0, sticky="w", padx=30, pady=(30, 30))

    card = ctk.CTkFrame(view, fg_color="#F9F9FB", corner_radius=10, border_width=1, border_color="#E5E5EA")
    card.grid(row=1, column=0, sticky="ew", padx=30, pady=(0, 20))
    card.grid_columnconfigure(0, weight=1)

    lbl_tolerance = ctk.CTkLabel(card, text=f"Чувствительность алгоритма: {app_state['tolerance']}", font=ui_component.FONTS['main'])
    lbl_tolerance.grid(row=0, column=0, sticky="w", padx=25, pady=(25, 5))

    desc = "Определяет допустимую разницу между картинками.\n0 — только точные копии, 5-10 — находит слегка сжатые или отретушированные фото."
    ctk.CTkLabel(card, text=desc, font=ui_component.FONTS['second'], text_color="gray", justify="left").grid(row=1, column=0, sticky="w", padx=25, pady=(0, 20))

    def update_tolerance(value):
        val = int(value)
        app_state['tolerance'] = val
        lbl_tolerance.configure(text=f"Чувствительность алгоритма: {val}")

    slider = ctk.CTkSlider(card, from_=0, to=15, number_of_steps=15, command=update_tolerance)
    slider.set(app_state['tolerance'])
    slider.grid(row=2, column=0, sticky="ew", padx=25, pady=(0, 30))

    return view