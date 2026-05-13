import customtkinter as ctk

import ui.ui_components as ui_component


def create_settings_view(parent, app_state, show_error_callback=None):
    view = ctk.CTkScrollableFrame(parent, fg_color="#FFFFFF", corner_radius=15)

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
        lbl_tolerance.configure(text=f"Уровень строгости (совпадающие точки): {val}")
    
    tolerance_frame = ctk.CTkFrame(content, fg_color="transparent")
    tolerance_frame.grid(row=1, column=0, sticky="ew", pady=(0, 25))
    tolerance_frame.grid_columnconfigure(0, weight=1)

    current_tolerance = app_state.get('tolerance', 15)

    lbl_tolerance = ctk.CTkLabel(tolerance_frame, text=f"Уровень строгости (совпадающие точки): {current_tolerance}", font=ui_component.FONTS['main'])
    lbl_tolerance.pack(anchor="w", pady=(0, 5))

    # Меняем диапазон: от 5 (минимальное совпадение) до 35 (очень строгое совпадение)
    slider = ctk.CTkSlider(tolerance_frame, from_=5, to=35, number_of_steps=30, command=update_tolerance)
    slider.set(current_tolerance)
    slider.pack(anchor="w", pady=(0, 5))

    desc_tolerance = (
        "Определяет, сколько общих уникальных деталей должны иметь фотографии.\n"
        "• 10-12 — находит кадры даже после жесткого кропа и сильной пластики.\n"
        "• 15 — стандартный баланс (рекомендуется).\n"
        "• 25-35 — строгий поиск (почти идентичные кадры)."
    )
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
    
    # Настройки для поиска оригиналов
    originals_frame = ctk.CTkFrame(content, fg_color="transparent")
    originals_frame.grid(row=3, column=0, sticky="ew", pady=(0, 20))
    originals_frame.grid_columnconfigure(0, weight=1)
    
    ui_component.subtitle(originals_frame, "Настройки поиска оригиналов")
    
    # Порог pHash
    def update_phash_threshold(value):
        val = int(value)
        app_state['phash_threshold'] = val
        lbl_phash.configure(text=f"Порог pHash (строгость): {val}")
    
    phash_frame = ctk.CTkFrame(originals_frame, fg_color="transparent")
    phash_frame.pack(fill="x", pady=(10, 5))
    
    current_phash = app_state.get('phash_threshold', 25)
    lbl_phash = ctk.CTkLabel(phash_frame, text=f"Порог pHash (строгость): {current_phash}", font=ui_component.FONTS['main'])
    lbl_phash.pack(anchor="w", pady=(0, 5))
    
    phash_slider = ctk.CTkSlider(phash_frame, from_=5, to=35, number_of_steps=30, command=update_phash_threshold)
    phash_slider.set(current_phash)
    phash_slider.pack(anchor="w", pady=(0, 5))
    
    phash_desc = "Определяет чувствительность сравнения по хэшам (меньше = строже).\n• 10-15 — строгий поиск (почти идентичные изображения).\n• 20-25 — стандартный баланс (рекомендуется).\n• 30-35 — мягкий поиск (находит повёрнутые и обрезанные сканы)."
    phash_desc_frame = ui_component.CTkAdaptiveLabel(phash_frame, text=phash_desc, font=ui_component.FONTS['second'], text_color=ui_component.COLORS['text_second'], justify="left", anchor="w")
    phash_desc_frame.pack(fill="x")
    
    # Минимальное улучшение качества
    def update_quality_ratio(value):
        val = float(value)
        app_state['quality_ratio'] = val
        lbl_quality.configure(text=f"Минимальное улучшение качества: {val:.1f}×")
    
    quality_frame = ctk.CTkFrame(originals_frame, fg_color="transparent")
    quality_frame.pack(fill="x", pady=(10, 5))
    
    current_quality = app_state.get('quality_ratio', 1.2)
    lbl_quality = ctk.CTkLabel(quality_frame, text=f"Минимальное улучшение качества: {current_quality:.1f}×", font=ui_component.FONTS['main'])
    lbl_quality.pack(anchor="w", pady=(0, 5))
    
    quality_slider = ctk.CTkSlider(quality_frame, from_=1.0, to=2.0, number_of_steps=20, command=update_quality_ratio)
    quality_slider.set(current_quality)
    quality_slider.pack(anchor="w", pady=(0, 5))
    
    quality_desc = "Во сколько раз оригинал должен быть лучше превью (по размеру файла или разрешению).\n1.0 = любой размер, 1.5 = оригинал на 50% лучше."
    quality_desc_frame = ui_component.CTkAdaptiveLabel(quality_frame, text=quality_desc, font=ui_component.FONTS['second'], text_color=ui_component.COLORS['text_second'], justify="left", anchor="w")
    quality_desc_frame.pack(fill="x")

    desc_recursive = "При включении будет выполняться поиск во всех подпапках выбранных директорий."
    desc_recursive_frame = ui_component.CTkAdaptiveLabel(search_recursive_frame, text=desc_recursive, text_color=ui_component.COLORS["text_second"], font=ui_component.FONTS['second'], justify="left", anchor="w")
    desc_recursive_frame.pack(fill="x")

    return view