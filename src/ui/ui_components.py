import customtkinter as ctk
import textwrap


COLORS = {
    "bg_app": "#F1F4F9",
    "bg_surface": "#FFFFFF",
    "bg_input": "#EFF3F8",

    "border": "#E2E8F0",
    "border_dark": "#CDD6E4",

    "text_main": "#1E2A3A",
    "text_second": "#5A6C7E",
    "text_muted": "#8C9AA8",
    "text_light": "#FFFFFF",

    "primary": "#2C6B9E",
    "primary_hover": "#1E4A6E",
    "primary_light": "#EBF5FB",

    "primary_btn": "#000000",
    "primary_btn_hover": "#1A1A1A",

    "success": "#1B7B4B",
    "error": "#C23D3D",
    "danger": "#E87A2A",
}


FONTS = {
    "title": ("Montserrat", 26, "bold"),
    "main": ("Rubik", 16),
    "second": ("Rubik Light", 15),
    "second_btn": ("Rubik", 15)
}


BUTTON_PRIMARY = {
    "height": 40,
    "corner_radius": 25,
    "fg_color": COLORS["primary_btn"],
    "hover_color": COLORS["primary_btn_hover"],
    "text_color": COLORS["text_light"]
}


BUTTON_PRIMARY_MIN = {
    "height": 30,
    "corner_radius": 10,
    "fg_color": COLORS["primary_btn"],
    "hover_color": COLORS["primary_btn_hover"],
    "text_color": COLORS["text_light"]
}


BUTTON_SECONDARY = {
    "height": 30,
    "corner_radius": 10,
    "fg_color": "transparent",
    "hover_color": COLORS["primary_light"],
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
    return ctk.CTkLabel(view, text=text, font=FONTS['title']).grid(row=0, column=0, sticky="w", pady=(0, 20))


def subtitle(view, text: str):
    """Подзаголовок (второго уровня)"""
    return ctk.CTkLabel(view, text=text, font=FONTS['main'], text_color=COLORS["text_main"]).pack(anchor="w", pady=(0, 10))


def description(view, text: str):
    """Описание для функции программы"""
    desc_frame = ctk.CTkFrame(view, fg_color=COLORS["bg_input"], corner_radius=8)
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
        text_color=COLORS["text_muted"],
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