import ctypes

from src.ui.app import App

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

if __name__ == '__main__':
    app = App()
    app.mainloop()