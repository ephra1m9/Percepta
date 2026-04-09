import customtkinter as ctk

import src.ui.ui_components as ui_component


def create_settings_view(parent, app_state, show_error_callback=None):
    view = ctk.CTkFrame(parent, fg_color="#FFFFFF", corner_radius=15)

    view.grid_columnconfigure(0, weight=1)
    view.grid_rowconfigure(2, weight=1)

    content = ctk.CTkFrame(view, fg_color="transparent")
    content.pack(fill="both", expand=True, padx=40, pady=20)
    content.grid_columnconfigure(0, weight=1)

    ui_component.title(content, "Настройки программы")

    # Настройки чувствительности алгоритма    
    def update_tolerance(value):
        val = int(value)
        app_state['tolerance'] = val
        lbl_tolerance.configure(text=f"Чувствительность алгоритма: {val}")
    
    tolerance_frame = ctk.CTkFrame(content, fg_color="transparent")
    tolerance_frame.grid(row=1, column=0, sticky="ew", pady=(0, 25))
    tolerance_frame.grid_columnconfigure(0, weight=1)

    lbl_tolerance = ctk.CTkLabel(tolerance_frame, text=f"Чувствительность алгоритма: {app_state['tolerance']}", font=ui_component.FONTS['main'])
    lbl_tolerance.pack(anchor="w", pady=(0, 5))

    slider = ctk.CTkSlider(tolerance_frame, from_=0, to=15, number_of_steps=15, command=update_tolerance)
    slider.set(app_state['tolerance'])
    slider.pack(anchor="w", pady=(0, 5))

    desc_tolerance = "Определяет допустимую разницу между картинками.\n0 — только точные копии, 5-10 — находит слегка сжатые или отретушированные фото."
    desc_tolerance_frame = ui_component.CTkAdaptiveLabel(tolerance_frame, text=desc_tolerance, font=ui_component.FONTS['second'], text_color=ui_component.COLORS['text_second'], justify="left", anchor="w")
    desc_tolerance_frame.pack(fill="x")

    # Настройка поиска во вложенных папках
    def toggle_search_recursive():
        app_state['search_recursive'] = not app_state.get('search_recursive', False)
        if app_state['search_recursive']:
            switch.select()
        else:
            switch.deselect()

    search_recursive_frame = ctk.CTkFrame(content, fg_color="transparent")
    search_recursive_frame.grid(row=2, column=0, sticky="ew", pady=(0, 20))
    search_recursive_frame.grid_columnconfigure(0, weight=1)    

    switch = ctk.CTkSwitch(search_recursive_frame, text="Поиск во вложенных папках", font=ui_component.FONTS['main'], command=toggle_search_recursive, onvalue=True, offvalue=False)
    switch.pack(anchor="w", pady=(0, 5))

    if app_state.get('search_recursive', False):
        switch.select()
    else:
        switch.deselect()

    desc_recursive = "При включении будет выполняться поиск во всех подпапках выбранных директорий."
    desc_recursive_frame = ui_component.CTkAdaptiveLabel(search_recursive_frame, text=desc_recursive, text_color=ui_component.COLORS["text_second"], font=ui_component.FONTS['second'], justify="left", anchor="w")
    desc_recursive_frame.pack(fill="x")

    return view