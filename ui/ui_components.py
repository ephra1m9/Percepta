import customtkinter as ctk
import textwrap


COLORS = {
    "bg_app": "#F9FAFB",
    "bg_surface": "#FFFFFF",
    "bg_input": "#EFF3F8",
    
    "info_bg": "#DBEAFE",
    "info_text": "#1E40AF",

    "border": "#E5E7EB",
    "border_dark": "#D1D5DB",

    "text_main": "#111827",
    "text_second": "#4B5563",
    "text_light": "#FFFFFF",

    "primary": "#6366F1",
    "primary_hover": "#4F46E5",
    "primary_light": "#E0E7FF",

    "hover_gray": "#F3F4F6",

    "success": "#10B981",
    "error": "#EF4444",
    "danger": "#E87A2A",
}


FONTS = {
    "title": ("Montserrat", 28, "bold"),
    "subtitle": ("Montserrat SemiBold", 22),
    "main": ("Rubik", 16),
    "second": ("Rubik Light", 15),
    "second_btn": ("Rubik", 15)
}


BUTTON_PRIMARY = {
    "height": 40,
    "corner_radius": 25,
    "fg_color": COLORS["primary"],
    "hover_color": COLORS["primary_hover"],
    "text_color": COLORS["text_light"]
}


BUTTON_PRIMARY_MIN = {
    "height": 30,
    "corner_radius": 10,
    "fg_color": COLORS["primary"],
    "hover_color": COLORS["primary_hover"],
    "text_color": COLORS["text_light"]
}


BUTTON_SECONDARY = {
    "height": 30,
    "corner_radius": 10,
    "fg_color": "transparent",
    "hover_color": COLORS["hover_gray"],
    "text_color": COLORS["text_main"],
    "border_width": 1,
    "border_color": COLORS["border_dark"]
}


BUTTON_SECONDARY_DANGER = {
    "height": 30,
    "corner_radius": 10,
    "fg_color": "transparent",
    "hover_color": '#FDEDEC',
    "text_color": COLORS["error"],
    "border_width": 1,
    "border_color": COLORS["border_dark"]
}


class CTkAdaptiveLabel(ctk.CTkLabel):
    """Умный ярлык для label"""
    def __init__(self, *args, **kwargs):
        self._raw_text = kwargs.get("text", "")
        super().__init__(*args, **kwargs)
        self._last_width = 0
        self.bind("<Configure>", self._update_text)

    def _update_text(self, event):
        if abs(self._last_width - event.width) > 10:
            self._last_width = event.width
            
            max_chars = max(10, int(event.width / 7.5))
            paragraphs = self._raw_text.split('\n')

            wrapped_paragraphs = [textwrap.fill(p, width=max_chars) for p in paragraphs]
            
            wrapped_text = '\n'.join(wrapped_paragraphs)
            
            self.configure(text=wrapped_text)


def title(view, text: str):
    """Основной заголовок"""
    return ctk.CTkLabel(view, text=text, font=FONTS['title'], text_color=COLORS['text_main']).grid(row=0, column=0, sticky="w", pady=(0, 20))


def subtitle(view, text: str):
    """Подзаголовок (второго уровня)"""
    return ctk.CTkLabel(view, text=text, font=FONTS['subtitle'], text_color=COLORS["text_main"]).pack(anchor="w", pady=(0, 10))


def description(view, text: str):
    """Описание для функции программы"""
    desc_frame = ctk.CTkFrame(view, fg_color=COLORS["bg_input"], corner_radius=10)
    desc_frame.grid(row=1, column=0, pady=(0, 30), sticky="ew")
    
    lbl_desc = CTkAdaptiveLabel(
        desc_frame,
        text=text,
        text_color=COLORS["text_main"],
        font=FONTS['second'],
        justify="left",
        anchor="w"
    )
    lbl_desc.pack(fill="x", expand=True, padx=15, pady=15)


def result_action_card_btn(parent, title_text: str, desc_text: str, icon_name, event_handler):
    """"Карточка-кнопка для действия с результатом"""
    card = ctk.CTkFrame(parent, fg_color="transparent", border_width=1, border_color=COLORS["border"], corner_radius=10, cursor="hand2")
    card.pack(fill="x", pady=(0, 10))

    header_frame = ctk.CTkFrame(card, fg_color="transparent", cursor="hand2")
    header_frame.pack(fill="x", padx=15, pady=(15, 5))

    icon = ctk.CTkLabel(header_frame, text="", image=icon_name, cursor="hand2")
    icon.pack(side="left", padx=(0, 10))

    title = ctk.CTkLabel(header_frame, text=title_text, font=FONTS['main'], text_color=COLORS["text_main"], cursor="hand2")
    title.pack(side="left")

    description = CTkAdaptiveLabel(card, text=desc_text, font=FONTS['second'], text_color=COLORS["text_second"], justify="left", anchor="w", cursor="hand2")
    description.pack(fill="x", padx=15, pady=(0, 15))

    def on_click(event):
        event_handler()

    def on_enter(event):
        card.configure(fg_color=COLORS["primary_light"])

    def on_leave(event):
        card.configure(fg_color="transparent")

    widgets = [card, header_frame, icon, title, description]
    
    for widget in widgets:
        widget.bind("<Button-1>", on_click)
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    return card


def result_action_btn(parent, btn_text: str, desc_text: str, icon_name):
    """Кнопка для действия с результатом"""
    card = ctk.CTkFrame(parent, fg_color=COLORS["bg_input"], corner_radius=8)
    card.pack(fill="x", pady=(0, 10))

    btn = ctk.CTkButton(card, text=btn_text, image=icon_name, font=FONTS['main'], **BUTTON_SECONDARY)
    btn.pack(anchor="w", padx=20, pady=(15, 5))
    
    CTkAdaptiveLabel(
        card, 
        text=desc_text, 
        text_color=COLORS["text_second"],
        font=FONTS['second'],
        justify="left",
        anchor="w"
    ).pack(fill="x", padx=20, pady=(0, 15))

    return btn


def hr_grid(view, row, pady=20):
    """Горизонтальная линия (hr) в grid"""
    ctk.CTkFrame(view, height=2, fg_color=COLORS["border"]).grid(row=row, column=0, sticky="ew", pady=pady)


def hr_pack(view, pady=20):
    """Горизонтальная линия (hr) в pack"""
    ctk.CTkFrame(view, height=2, fg_color=COLORS["border"]).pack(fill="x", pady=pady)


def process_screen(parent, title: str, scan_mode: str):
    """Окно с информацией о процессе поиска"""
    found_labels = {
        "reference": "Найдено изображений:",
        "originals": "Найдено оригиналов:",
        "duplicates": "Найдено дубликатов:"
    }

    main_view = ctk.CTkFrame(parent, fg_color="transparent", border_width=1, border_color=COLORS["border"], corner_radius=10)
    main_view.grid_rowconfigure(0, weight=1)
    main_view.grid_columnconfigure(0, weight=1)

    main_container = ctk.CTkFrame(main_view, fg_color="transparent")
    main_container.pack(expand=True, fill="both", padx=20, pady=20)

    main_container.grid_columnconfigure(0, weight=1)
    main_container.grid_columnconfigure(1, weight=2)
    main_container.grid_columnconfigure(2, weight=1)

    header_frame = ctk.CTkFrame(main_container, fg_color="transparent")
    header_frame.grid(row=0, column=0, sticky="w", pady=(0, 10))

    lbl_title = ctk.CTkLabel(header_frame, text=title, font=FONTS["subtitle"], text_color=COLORS["text_main"])
    lbl_title.grid(row=0, column=0)

    progress_bar_frame = ctk.CTkFrame(main_container, fg_color="transparent", border_width=1, border_color=COLORS["border"], corner_radius=5)
    progress_bar_frame.grid(row=1, column=0, sticky="we", pady=(0, 10))

    progress_bar = ctk.CTkProgressBar(progress_bar_frame, width=400, progress_color=COLORS["primary"], fg_color=COLORS["hover_gray"])
    progress_bar.grid(row=1, column=0, sticky="we", padx=5, pady=5)

    info_frame = ctk.CTkFrame(main_container, fg_color="transparent")
    info_frame.grid(row=2, column=0, sticky="ew")

    info_frame.grid_columnconfigure(0, weight=1)
    info_frame.grid_columnconfigure(1, weight=1)

    lbl_checked_images = ctk.CTkLabel(info_frame, text="Проверено изображений:", font=FONTS["second"], text_color=COLORS["text_second"])
    lbl_checked_images.grid(row=0, column=0, sticky="w")

    lbl_images_checked_count = ctk.CTkLabel(info_frame, text="0/0", font=FONTS["second"], text_color=COLORS["text_second"])
    lbl_images_checked_count.grid(row=0, column=1, sticky="e")

    lbl_images_found = ctk.CTkLabel(info_frame, text=found_labels.get(scan_mode, "Найдено:"), font=FONTS["second"], text_color=COLORS["text_second"])
    lbl_images_found.grid(row=1, column=0, sticky="w")

    lbl_images_found_count = ctk.CTkLabel(info_frame, text="0", font=FONTS["second"], text_color=COLORS["text_second"])
    lbl_images_found_count.grid(row=1, column=1, sticky="e")

    def update_status(checked_count, find_count, progress_value=None):
        lbl_images_checked_count.configure(text=checked_count)
        lbl_images_found_count.configure(text=find_count)

        if progress_value is not None:
            progress_bar.set(progress_value)

        main_container.update_idletasks()

    return main_view, update_status