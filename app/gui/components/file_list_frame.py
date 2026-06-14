import customtkinter as ctk
import os
from app.gui.theme import Theme

class FileListFrame(ctk.CTkFrame):
    def __init__(self, parent, title="Archivos seleccionados", on_remove=None):
        super().__init__(parent, fg_color="transparent")
        self.on_remove = on_remove
        self.files = []
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 10))
        
        self.title_label = ctk.CTkLabel(self.header_frame, text=title, font=(Theme.FONT_FAMILY, 16, "bold"), text_color=Theme.TEXT_MAIN)
        self.title_label.pack(side="left")
        
        self.count_label = ctk.CTkLabel(self.header_frame, text="0 archivos", text_color="gray", font=(Theme.FONT_FAMILY, 12))
        self.count_label.pack(side="right")
        
        # Scrollable list
        self.scroll_frame = ctk.CTkScrollableFrame(self, corner_radius=10, fg_color="white") # White background for list
        self.scroll_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        
        # Placeholder
        self.placeholder_label = ctk.CTkLabel(self.scroll_frame, text="Ningún archivo seleccionado.\nUsa el botón 'Añadir archivos' para comenzar.",
                                            text_color="gray", font=(Theme.FONT_FAMILY, 14))
        self.placeholder_label.pack(pady=80, expand=True)
        
    def add_file(self, filepath):
        if filepath in self.files:
            return
            
        self.files.append(filepath)
        self.refresh_list()
        
    def remove_file(self, filepath):
        if filepath in self.files:
            self.files.remove(filepath)
            self.refresh_list()
            if self.on_remove:
                self.on_remove(filepath)
                
    def clear_files(self):
        self.files = []
        self.refresh_list()
        
    def get_files(self):
        return self.files
        
    def refresh_list(self):
        # Clear current widgets
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
            
        # Update counter
        self.count_label.configure(text=f"{len(self.files)} archivos")
        
        if not self.files:
            self.placeholder_label = ctk.CTkLabel(self.scroll_frame, text="Ningún archivo seleccionado.\nUsa el botón 'Añadir archivos' para comenzar.",
                                                text_color="gray", font=(Theme.FONT_FAMILY, 14))
            self.placeholder_label.pack(pady=80, expand=True)
            return
            return
        
        # Add items
        for filepath in self.files:
            self._create_file_item(filepath)
            
    def move_file_up(self, filepath):
        if filepath in self.files:
            idx = self.files.index(filepath)
            if idx > 0:
                self.files[idx], self.files[idx - 1] = self.files[idx - 1], self.files[idx]
                self.refresh_list()
                
    def move_file_down(self, filepath):
        if filepath in self.files:
            idx = self.files.index(filepath)
            if idx < len(self.files) - 1:
                self.files[idx], self.files[idx + 1] = self.files[idx + 1], self.files[idx]
                self.refresh_list()

    def _create_file_item(self, filepath):
        filename = os.path.basename(filepath)
        
        item_frame = ctk.CTkFrame(self.scroll_frame, fg_color=Theme.BACKGROUND, corner_radius=8)
        item_frame.pack(fill="x", pady=4, padx=5)
        
        # Icon
        ctk.CTkLabel(item_frame, text="📄", font=("Arial", 24), text_color=Theme.PRIMARY).pack(side="left", padx=(15, 10), pady=10)
        
        # Info frame
        info_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True, pady=5)
        
        name_label = ctk.CTkLabel(info_frame, text=filename, anchor="w", font=(Theme.FONT_FAMILY, 13, "bold"), text_color=Theme.TEXT_MAIN)
        name_label.pack(fill="x")
        
        path_label = ctk.CTkLabel(info_frame, text=filepath, anchor="w", text_color="gray", font=(Theme.FONT_FAMILY, 11))
        path_label.pack(fill="x")
        
        # Button to remove
        remove_btn = ctk.CTkButton(
            item_frame, 
            text="×", 
            width=30, 
            height=30,
            fg_color="transparent", 
            text_color=("gray50", "gray70"),
            hover_color=("gray80", "gray30"),
            font=("Arial", 20),
            command=lambda f=filepath: self.remove_file(f)
        )
        remove_btn.pack(side="right", padx=5)

        # Button to move down
        down_btn = ctk.CTkButton(
            item_frame, 
            text="↓", 
            width=30, 
            height=30,
            fg_color="transparent", 
            text_color=("gray50", "gray70"),
            hover_color=("gray80", "gray30"),
            font=("Arial", 16),
            command=lambda f=filepath: self.move_file_down(f)
        )
        down_btn.pack(side="right", padx=2)

        # Button to move up
        up_btn = ctk.CTkButton(
            item_frame, 
            text="↑", 
            width=30, 
            height=30,
            fg_color="transparent", 
            text_color=("gray50", "gray70"),
            hover_color=("gray80", "gray30"),
            font=("Arial", 16),
            command=lambda f=filepath: self.move_file_up(f)
        )
        up_btn.pack(side="right", padx=2)

        # Bind drag events to frame and children (except buttons)
        for widget in [item_frame, item_frame.master, info_frame, name_label, path_label]:
           if widget == item_frame.master: continue
           
           widget.bind("<Button-1>", lambda e, f=filepath: self._start_drag(e, f))
           widget.bind("<B1-Motion>", self._on_drag)
           widget.bind("<ButtonRelease-1>", self._stop_drag)

    def _start_drag(self, event, filepath):
        self._drag_data = {"filepath": filepath, "start_y": event.y_root}
        self.configure(cursor="hand2")

    def _on_drag(self, event):
        pass

    def _stop_drag(self, event):
        self.configure(cursor="")
        if not hasattr(self, '_drag_data'):
            return

        source_filepath = self._drag_data["filepath"]
        
        # Find widget under mouse
        x, y = event.x_root, event.y_root
        target_widget = self.winfo_containing(x, y)
        scroll_frame_y = self.scroll_frame.winfo_rooty()
        
        # If we are outside the list, do nothing
        if not (self.scroll_frame.winfo_rootx() < x < self.scroll_frame.winfo_rootx() + self.scroll_frame.winfo_width()):
             del self._drag_data
             return

        target_index = -1
        
        children = self.scroll_frame.winfo_children()
        if not self.files: 
             del self._drag_data
             return

        mouse_y_rel = y - scroll_frame_y + self.scroll_frame._parent_canvas.yview()[0] * self.scroll_frame.winfo_height() 

        found = False
        for i, child in enumerate(children):
            if not isinstance(child, ctk.CTkFrame): continue # Skip non-item frames if any
            
            child_y = child.winfo_rooty()
            child_h = child.winfo_height()
            
            if child_y <= y <= child_y + child_h:
                target_index = i
                found = True
                break
        
        if not found:
             # If below the last item
             last_child = children[-1]
             if y > last_child.winfo_rooty() + last_child.winfo_height():
                 target_index = len(self.files) - 1
             elif y < children[0].winfo_rooty():
                 target_index = 0
        
        if target_index != -1 and target_index < len(self.files):
            source_index = self.files.index(source_filepath)
            
            if source_index != target_index:
                # Move item
                self.files.pop(source_index)
                self.files.insert(target_index, source_filepath)
                self.refresh_list()
        
        if hasattr(self, '_drag_data'):
            del self._drag_data
