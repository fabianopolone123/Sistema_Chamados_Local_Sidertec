from __future__ import annotations

import threading
import tkinter as tk
from typing import Callable


class TrayController:
    def __init__(self, root: tk.Tk, app_name: str, on_exit: Callable[[], None]) -> None:
        self.root = root
        self.app_name = app_name
        self.on_exit = on_exit

        self._icon = None
        self._pystray = None
        self._image_cls = None
        self._image_draw_cls = None
        self._start_lock = threading.Lock()

        try:
            import pystray
            from PIL import Image, ImageDraw

            self._pystray = pystray
            self._image_cls = Image
            self._image_draw_cls = ImageDraw
        except Exception:
            self._pystray = None

    @property
    def available(self) -> bool:
        return self._pystray is not None

    def start(self) -> None:
        if not self.available:
            return

        with self._start_lock:
            if self._icon is not None:
                return

            menu = self._pystray.Menu(
                self._pystray.MenuItem("Abrir", self._on_open),
                self._pystray.MenuItem("Sair", self._on_exit),
            )
            self._icon = self._pystray.Icon(
                name=self.app_name,
                icon=self._build_icon(),
                title=self.app_name,
                menu=menu,
            )
            thread = threading.Thread(target=self._icon.run, daemon=True)
            thread.start()

    def hide_window(self) -> None:
        if self.available:
            self.root.withdraw()
        else:
            self.root.iconify()

    def show_window(self) -> None:
        self.root.after(0, self._show_window_on_main_thread)

    def stop(self) -> None:
        if self._icon is None:
            return

        icon = self._icon
        self._icon = None
        try:
            icon.stop()
        except Exception:
            pass

    def _show_window_on_main_thread(self) -> None:
        self.root.deiconify()
        self.root.state("normal")
        self.root.lift()
        self.root.focus_force()

    def _build_icon(self):
        image = self._image_cls.new("RGB", (64, 64), "#1f2937")
        draw = self._image_draw_cls.Draw(image)
        draw.rounded_rectangle((6, 6, 58, 58), radius=10, fill="#2563eb")
        draw.rectangle((16, 22, 48, 28), fill="#ffffff")
        draw.rectangle((16, 34, 40, 40), fill="#dbeafe")
        return image

    def _on_open(self, _icon, _item) -> None:
        self.show_window()

    def _on_exit(self, _icon, _item) -> None:
        self.stop()
        self.root.after(0, self.on_exit)

