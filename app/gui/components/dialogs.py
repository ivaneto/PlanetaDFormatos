"""Diálogos modales estilizados con CustomTkinter.

Reemplazo de ``tkinter.messagebox`` con la misma API (``showinfo``,
``showwarning``, ``showerror``, ``askyesno``, ``askokcancel``,
``askquestion``) para que las páginas no necesiten cambiar sus llamadas:

    from app.gui.components import dialogs as messagebox
    messagebox.showinfo("Título", "Mensaje")
    if messagebox.askyesno("Confirmar", "¿Seguro?"): ...

Si por algún motivo no hay una ventana raíz de Tk disponible, se delega en el
``messagebox`` nativo como salvaguarda.
"""
import tkinter as tk
import customtkinter as ctk

from app.gui.theme import Theme

_ICON = {"info": "ℹ️", "warning": "⚠️", "error": "⛔", "question": "❓"}
_ACCENT = {
    "info": Theme.PRIMARY,
    "warning": Theme.WARNING,
    "error": Theme.DANGER,
    "question": Theme.PRIMARY,
}


class _Dialog(ctk.CTkToplevel):
    def __init__(self, master, title, message, kind, buttons):
        super().__init__(master)
        self.result = None

        self.title(title or "")
        self.resizable(False, False)
        self.configure(fg_color=Theme.BACKGROUND)

        accent = _ACCENT.get(kind, Theme.PRIMARY)

        container = ctk.CTkFrame(self, fg_color=Theme.SURFACE, corner_radius=12)
        container.pack(fill="both", expand=True, padx=16, pady=16)

        head = ctk.CTkFrame(container, fg_color="transparent")
        head.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(head, text=_ICON.get(kind, "ℹ️"), font=("Arial", 28)).pack(side="left", padx=(0, 12))
        ctk.CTkLabel(head, text=title or "", font=(Theme.FONT_FAMILY, 18, "bold"),
                     text_color=accent, anchor="w").pack(side="left")

        ctk.CTkLabel(container, text=message or "", font=(Theme.FONT_FAMILY, 14),
                     text_color=Theme.TEXT_MAIN, wraplength=380, justify="left").pack(
            fill="x", padx=20, pady=(0, 20))

        btn_row = ctk.CTkFrame(container, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(0, 16))

        # El último botón es el primario (alineado a la derecha).
        for i, (text, value) in enumerate(buttons):
            primary = (i == len(buttons) - 1)
            fg = accent if primary else "transparent"
            ctk.CTkButton(
                btn_row, text=text, width=110, height=36,
                fg_color=fg if primary else "transparent",
                border_width=0 if primary else 1, border_color=Theme.BORDER,
                text_color=Theme.TEXT_WHITE if primary else Theme.TEXT_MAIN,
                hover_color=Theme.PRIMARY_HOVER if primary else Theme.ACCENT_SOFT,
                font=(Theme.FONT_FAMILY, 13, "bold"),
                command=lambda v=value: self._choose(v),
            ).pack(side="right", padx=6)

        self.protocol("WM_DELETE_WINDOW", lambda: self._choose(buttons[0][1]))
        self.bind("<Return>", lambda e: self._choose(buttons[-1][1]))
        self.bind("<Escape>", lambda e: self._choose(buttons[0][1]))

        self.transient(master)
        self.update_idletasks()
        self._center(master)
        self.grab_set()
        self.focus_force()
        self.wait_window(self)

    def _center(self, master):
        w = max(self.winfo_reqwidth(), 360)
        h = self.winfo_reqheight()
        try:
            mx = master.winfo_rootx()
            my = master.winfo_rooty()
            mw = master.winfo_width()
            mh = master.winfo_height()
            x = mx + (mw - w) // 2
            y = my + (mh - h) // 2
        except Exception:
            x = (self.winfo_screenwidth() - w) // 2
            y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{max(0, x)}+{max(0, y)}")

    def _choose(self, value):
        self.result = value
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()


def _run(title, message, kind, buttons):
    master = tk._default_root
    if master is None:
        # Salvaguarda: sin raíz de Tk, usar el messagebox nativo.
        from tkinter import messagebox as _mb
        if kind == "question":
            return _mb.askyesno(title, message)
        return _mb.showinfo(title, message)
    return _Dialog(master, title, message, kind, buttons).result


# --- API compatible con tkinter.messagebox ---
def showinfo(title="", message="", **kwargs):
    return _run(title, message, "info", [("Aceptar", "ok")])


def showwarning(title="", message="", **kwargs):
    return _run(title, message, "warning", [("Aceptar", "ok")])


def showerror(title="", message="", **kwargs):
    return _run(title, message, "error", [("Aceptar", "ok")])


def askyesno(title="", message="", **kwargs):
    return _run(title, message, "question", [("No", False), ("Sí", True)])


def askokcancel(title="", message="", **kwargs):
    return _run(title, message, "question", [("Cancelar", False), ("Aceptar", True)])


def askquestion(title="", message="", **kwargs):
    return "yes" if askyesno(title, message) else "no"
