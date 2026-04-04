VALID_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.pdf'}

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