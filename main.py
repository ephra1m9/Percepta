import ctypes
import multiprocessing

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

from ui.app import main as run_app


if __name__ == '__main__':
    multiprocessing.freeze_support()
    run_app()