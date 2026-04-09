import ctypes

from src.ui.app import main as run_app


try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

if __name__ == '__main__':
    run_app()