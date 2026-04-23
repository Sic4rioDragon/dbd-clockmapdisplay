import ctypes
import threading


MOD_NONE = 0x0000
WM_HOTKEY = 0x0312

VK_MAP = {
    "F8": 0x77,
    "F9": 0x78,
    "F10": 0x79,
}


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", ctypes.c_void_p),
        ("message", ctypes.c_uint),
        ("wParam", ctypes.c_size_t),
        ("lParam", ctypes.c_size_t),
        ("time", ctypes.c_uint),
        ("pt", POINT),
    ]


def start_global_hotkey(hotkey_name: str, event: threading.Event):
    user32 = ctypes.windll.user32
    vk = VK_MAP.get(hotkey_name.upper())

    if not vk:
        print(f"[HOTKEY] Unsupported hotkey: {hotkey_name}")
        return None

    hotkey_id = 1

    def hotkey_loop():
        if not user32.RegisterHotKey(None, hotkey_id, MOD_NONE, vk):
            print(f"[HOTKEY] Failed to register global hotkey {hotkey_name}")
            return

        print(f"[HOTKEY] Global hotkey registered: {hotkey_name}")

        msg = MSG()
        try:
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
                if msg.message == WM_HOTKEY and msg.wParam == hotkey_id:
                    event.set()
        finally:
            user32.UnregisterHotKey(None, hotkey_id)

    thread = threading.Thread(target=hotkey_loop, daemon=True)
    thread.start()
    return thread