import customtkinter as ctk
from app.gui.theme import Theme
from tkinterdnd2 import DND_FILES
import re

class BasePage(ctk.CTkFrame):
    def __init__(self, parent, controller, show_back_button=False):
        super().__init__(parent, fg_color="transparent") 
        self.controller = controller
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True)
            
        self.create_widgets()

    def create_header(self):
        pass

    def create_widgets(self):
        pass

    def enable_dnd(self):
        try:
            self.drop_target_register(DND_FILES)
            self.dnd_bind('<<Drop>>', self.on_drop)
        except Exception as e:
            print(f"El registro de Arrastrar y Soltar falló: {e}")

    def on_drop(self, event):
        files = self.parse_dropped_files(event.data)
        handled = self.handle_dropped_files(files)
        if not handled:
            self.controller.route_files(files)

    def handle_dropped_files(self, files):
        """Override this to handle dropped files. Return True if handled."""
        return False

    def parse_dropped_files(self, data):
        files = []
        pattern = r'\{(?P<path>.*?)\}|(?P<path2>\S+)'
        for match in re.finditer(pattern, data):
            path = match.group('path') or match.group('path2')
            if path:
                files.append(path)
        return files
