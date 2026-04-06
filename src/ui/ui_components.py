import customtkinter as ctk


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


def title(view, text: str):
    """Основной заголовок"""
    return ctk.CTkLabel(view, text=text, font=FONTS['title']).grid(row=0, column=0, sticky="w", pady=(0, 20))


def description(view, text: str):
    """Описание для функции программы"""
    desc_frame = ctk.CTkFrame(view, fg_color=COLORS["bg_input"], corner_radius=8)
    desc_frame.grid(row=1, column=0, pady=(0, 30), sticky="ew")
    description = ctk.CTkLabel(desc_frame, text=text, text_color=COLORS["text_main"], font=FONTS['second'], anchor="w")
    description.pack(fill="x", padx=14, pady=14)


def hr_grid(view, row, pady=20):
    """Горизонтальная линия (hr) в grid."""
    ctk.CTkFrame(view, height=2, fg_color=COLORS["border"]).grid(row=row, column=0, sticky="ew", pady=pady)


def hr_pack(view, pady=20):
    """Горизонтальная линия (hr) в pack."""
    ctk.CTkFrame(view, height=2, fg_color=COLORS["border"]).pack(fill="x", pady=pady)