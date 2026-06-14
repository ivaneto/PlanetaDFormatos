import customtkinter as ctk
from app.gui.theme import Theme

class PageThumbnailWidget(ctk.CTkFrame):
    def __init__(self, parent, image, page_num, on_click=None, is_selected=False, 
                 enable_controls=False, on_delete=None, on_rotate=None,
                 on_drag_start=None, on_drag_motion=None, on_drag_end=None,
                 show_page_num=True):
        super().__init__(parent, fg_color="transparent", corner_radius=5, border_width=0)
        
        self.on_click = on_click
        self.is_selected = is_selected
        self.page_num = page_num
        self.enable_controls = enable_controls
        
        # Drag callbacks
        self.on_drag_start = on_drag_start
        self.on_drag_motion = on_drag_motion
        self.on_drag_end = on_drag_end
        
        # Image Label
        self.image_label = ctk.CTkLabel(self, text="", image=image)
        self.image_label.pack(padx=2, pady=2)
        
        # Page Number Label
        self.num_label = ctk.CTkLabel(self, text=f"Página {page_num + 1}", font=(Theme.FONT_FAMILY, 10), text_color=Theme.TEXT_MUTED)
        if show_page_num:
            self.num_label.pack(pady=(0, 2))
        
        if enable_controls:
            # Controls Frame
            controls_frame = ctk.CTkFrame(self, fg_color="transparent", height=20)
            controls_frame.pack(fill="x", pady=(0, 2), padx=2)
            
            # Container to center buttons
            btn_container = ctk.CTkFrame(controls_frame, fg_color="transparent")
            btn_container.pack(expand=True)

            if on_rotate:
                # Rotate Button "⟳"
                btn_rot = ctk.CTkButton(btn_container, text="⟳", width=20, height=20, 
                                        fg_color="transparent", text_color=Theme.PRIMARY, hover_color=Theme.PRIMARY_HOVER,
                                        font=(Theme.FONT_FAMILY, 14),
                                        command=lambda: on_rotate(self))
                btn_rot.pack(side="left", padx=3)

            # Delete Button
            if on_delete:
                btn_del = ctk.CTkButton(btn_container, text="🗑", width=20, height=20, 
                                        fg_color="transparent", text_color="red", hover_color="#FFEEEE",
                                        font=(Theme.FONT_FAMILY, 10),
                                        command=lambda: on_delete(self))
                btn_del.pack(side="left", padx=2)
            
            # Bind drag events to widget and image
            self.bind("<Button-1>", self.start_drag)
            self.image_label.bind("<Button-1>", self.start_drag)
            self.num_label.bind("<Button-1>", self.start_drag)
            
            self.bind("<B1-Motion>", self.drag_motion)
            self.image_label.bind("<B1-Motion>", self.drag_motion)
            self.num_label.bind("<B1-Motion>", self.drag_motion)
            
            self.bind("<ButtonRelease-1>", self.end_drag)
            self.image_label.bind("<ButtonRelease-1>", self.end_drag)
            self.num_label.bind("<ButtonRelease-1>", self.end_drag)

        if not enable_controls:
            self.bind("<Button-1>", self.clicked)
            self.image_label.bind("<Button-1>", self.clicked)
            self.num_label.bind("<Button-1>", self.clicked)
        
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        
        if is_selected:
            self.set_selected(True)

    def start_drag(self, event):
        if self.on_drag_start:
            self.on_drag_start(event, self)

    def drag_motion(self, event):
        if self.on_drag_motion:
            self.on_drag_motion(event, self)

    def end_drag(self, event):
        if self.on_drag_end:
            self.on_drag_end(event, self)

    def clicked(self, event=None):
        if self.on_click:
            self.on_click(self)

    def set_selected(self, selected):
        self.is_selected = selected
        if selected:
            self.configure(border_width=2, border_color=Theme.PRIMARY, fg_color="#FFF0E0")
        else:
            self.configure(border_width=0, fg_color="transparent")

    def on_enter(self, event):
        if not self.is_selected:
            self.configure(fg_color="#F0F0F0")

    def on_leave(self, event):
        if not self.is_selected:
            self.configure(fg_color="transparent")
