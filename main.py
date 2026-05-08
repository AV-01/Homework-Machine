import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext
import font_data
import settings_manager

class GCodeDrawer:
    def __init__(self, root):
        self.root = root
        self.root.title("Ender 3 Pen Plotter - Homework Machine")
        self.root.resizable(False, False)
        
        # Load persistent settings
        self.settings = settings_manager.load_settings()
        
        # UI Scaling constants
        self.SCALE = 3
        self.update_canvas_dims()

        # Data storage
        self.manual_strokes = []
        self.text_strokes = []
        self.current_stroke = []

        # UI Setup
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(padx=10, pady=10, expand=True, fill="both")
        
        self.draw_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.draw_tab, text=" Manual Drawing ")
        self.setup_draw_tab()

        self.text_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.text_tab, text=" Text to G-Code ")
        self.setup_text_tab()
        
        self.settings_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_tab, text=" Settings & Calib ")
        self.setup_settings_tab()
        
        self.on_toggle_lined_mode()

    def update_canvas_dims(self):
        self.canvas_w = (self.settings["X_MAX"] - self.settings["X_MIN"]) * self.SCALE
        self.canvas_h = (self.settings["Y_MAX"] - self.settings["Y_MIN"]) * self.SCALE

    def setup_draw_tab(self):
        self.draw_info = tk.Label(self.draw_tab, text=f"Printable: {self.settings['X_MIN']}-{self.settings['X_MAX']} x {self.settings['Y_MIN']}-{self.settings['Y_MAX']}")
        self.draw_info.pack(pady=5)
        self.canvas = tk.Canvas(self.draw_tab, width=self.canvas_w, height=self.canvas_h, bg="white", highlightthickness=1)
        self.canvas.pack(padx=20, pady=5)
        bf = tk.Frame(self.draw_tab)
        bf.pack(fill="x", pady=10)
        tk.Button(bf, text="Clear", command=self.clear_canvas).pack(side="left", padx=20)
        tk.Button(bf, text="Export G-Code", command=lambda: self.export_gcode("draw"), bg="#4CAF50", fg="white").pack(side="right", padx=20)
        self.canvas.bind("<Button-1>", self.start_stroke)
        self.canvas.bind("<B1-Motion>", self.draw_stroke)
        self.canvas.bind("<ButtonRelease-1>", self.end_stroke)

    def setup_text_tab(self):
        tk.Label(self.text_tab, text="Enter Homework Text:", font=("Arial", 9, "bold")).pack(anchor="w", padx=20, pady=(5,0))
        self.text_entry = scrolledtext.ScrolledText(self.text_tab, height=2)
        self.text_entry.pack(padx=20, pady=2, fill="x")
        
        ff = tk.Frame(self.text_tab)
        ff.pack(fill="x", padx=20, pady=2)
        tk.Label(ff, text="Fonts (Ctrl+Click):").pack(side="left")
        
        self.font_list_frame = tk.Frame(ff)
        self.font_list_frame.pack(side="left", padx=5)
        self.font_listbox = tk.Listbox(self.font_list_frame, selectmode="multiple", height=3, exportselection=False, width=25)
        self.font_listbox.pack(side="left", fill="y")
        self.font_scrollbar = tk.Scrollbar(self.font_list_frame, orient="vertical", command=self.font_listbox.yview)
        self.font_scrollbar.pack(side="right", fill="y")
        self.font_listbox.config(yscrollcommand=self.font_scrollbar.set)
        self.font_listbox.bind("<<ListboxSelect>>", lambda e: self.preview_text())
        
        tk.Button(ff, text="Refresh Fonts", command=self.update_font_list).pack(side="left", padx=5)
        
        # Humanize Control
        hf = tk.Frame(ff)
        hf.pack(side="left", padx=15)
        tk.Label(hf, text="Humanize Chaos:").pack(side="top")
        self.humanize_var = tk.DoubleVar(value=0.0)
        self.humanize_scale = tk.Scale(hf, from_=0.0, to_=1.0, resolution=0.1, orient="horizontal", variable=self.humanize_var, length=100, command=lambda x: self.preview_text())
        self.humanize_scale.pack(side="top")

        # Action Buttons (Moved to top to prevent falling off screen)
        tb_frame = tk.Frame(ff)
        tb_frame.pack(side="right", padx=10)
        tk.Button(tb_frame, text="Export Text G-Code", command=lambda: self.export_gcode("text"), bg="#2196F3", fg="white", font=("Arial", 9, "bold"), width=18).pack(side="top", pady=2)
        tk.Button(tb_frame, text="Refresh Preview \u21bb", command=self.preview_text, width=18).pack(side="bottom", pady=2)

        cf = tk.Frame(self.text_tab)
        cf.pack(fill="x", padx=20, pady=2)
        tk.Label(cf, text="Size (mm):").pack(side="left")
        self.font_size_val = tk.DoubleVar(value=round(self.settings["LINE_SPACING"] * self.settings["LINE_RATIO"], 2))
        self.fs_scale = tk.Scale(cf, from_=3, to_=30, resolution=0.1, orient="horizontal", variable=self.font_size_val, length=120, command=lambda x: self.preview_text())
        self.fs_scale.pack(side="left", padx=5)
        self.lined_mode_var = tk.BooleanVar(value=self.settings["LINED_PAPER_MODE"])
        tk.Checkbutton(cf, text="Lined mode", variable=self.lined_mode_var, command=self.on_toggle_lined_mode).pack(side="left", padx=5)
        self.draw_lines_var = tk.BooleanVar(value=False)
        tk.Checkbutton(cf, text="Draw guides", variable=self.draw_lines_var).pack(side="left", padx=5)
        
        self.preview_canvas = tk.Canvas(self.text_tab, width=self.canvas_w, height=self.canvas_h, bg="#f9f9f9", highlightthickness=1)
        self.preview_canvas.pack(padx=20, pady=5)

    def setup_settings_tab(self):
        container = tk.Frame(self.settings_tab)
        container.pack(padx=20, pady=20, fill="both")
        tk.Label(container, text="Machine Constants", font=("Arial", 10, "bold")).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0,10))
        self.entries = {}
        fields = [("X Min", "X_MIN"), ("X Max", "X_MAX"), ("Y Min", "Y_MIN"), ("Y Max", "Y_MAX"),
                  ("Z Safe", "Z_SAFE"), ("Z Draw", "Z_DRAW"), ("Travel F", "F_TRAVEL"), ("Draw F", "F_DRAW"), ("Trace F", "F_TRACE")]
        for i, (label, key) in enumerate(fields):
            r, c = divmod(i, 2)
            tk.Label(container, text=label).grid(row=r+1, column=c*2, sticky="e", padx=5, pady=2)
            ent = tk.Entry(container, width=10)
            ent.insert(0, str(self.settings[key]))
            ent.grid(row=r+1, column=c*2+1, sticky="w", padx=5, pady=2)
            self.entries[key] = ent
        tk.Label(container, text="Preferences & Rotation", font=("Arial", 10, "bold")).grid(row=6, column=0, columnspan=4, sticky="w", pady=(15,10))
        self.flip_x_var = tk.BooleanVar(value=self.settings["FLIP_X"])
        tk.Checkbutton(container, text="Reverse X", variable=self.flip_x_var).grid(row=7, column=0, sticky="w")
        self.flip_y_var = tk.BooleanVar(value=self.settings["FLIP_Y"])
        tk.Checkbutton(container, text="Reverse Y", variable=self.flip_y_var).grid(row=7, column=1, sticky="w")
        self.rotate_90_var = tk.BooleanVar(value=self.settings["ROTATE_90"])
        tk.Checkbutton(container, text="Rotate 90\u00b0 (Clockwise)", variable=self.rotate_90_var).grid(row=7, column=2, sticky="w")
        tk.Label(container, text="Line Spacing (mm):").grid(row=8, column=0, sticky="e", pady=2)
        self.line_space_ent = tk.Entry(container, width=10)
        self.line_space_ent.insert(0, str(self.settings["LINE_SPACING"]))
        self.line_space_ent.grid(row=8, column=1, sticky="w", pady=2)
        tk.Label(container, text="First Line Offset (mm):").grid(row=9, column=0, sticky="e", pady=2)
        self.top_margin_ent = tk.Entry(container, width=10)
        self.top_margin_ent.insert(0, str(self.settings["TOP_MARGIN"]))
        self.top_margin_ent.grid(row=9, column=1, sticky="w", pady=2)
        tk.Label(container, text="Auto-Fit Ratio (0-1):").grid(row=8, column=2, sticky="e", pady=2)
        self.line_ratio_ent = tk.Entry(container, width=10)
        self.line_ratio_ent.insert(0, str(self.settings["LINE_RATIO"]))
        self.line_ratio_ent.grid(row=8, column=3, sticky="w", pady=2)
        tk.Label(container, text="Float Offset (mm):").grid(row=9, column=2, sticky="e", pady=2)
        self.float_offset_ent = tk.Entry(container, width=10)
        self.float_offset_ent.insert(0, str(self.settings["FLOAT_OFFSET"]))
        self.float_offset_ent.grid(row=9, column=3, sticky="w", pady=2)
        tk.Label(container, text="Left Margin (mm):").grid(row=10, column=2, sticky="e", pady=2)
        self.left_margin_ent = tk.Entry(container, width=10)
        self.left_margin_ent.insert(0, str(self.settings["LEFT_MARGIN"]))
        self.left_margin_ent.grid(row=10, column=3, sticky="w", pady=2)
        
        tk.Label(container, text="Chaos Settings (Requires Save & Apply)", font=("Arial", 10, "bold")).grid(row=11, column=0, columnspan=4, sticky="w", pady=(15,10))
        chaos_fields = [("Scale Var", "CHAOS_SCALE"), ("Bounce Var", "CHAOS_BOUNCE"), 
                        ("Base Tilt", "CHAOS_BASE_TILT"), ("Rot Var", "CHAOS_ROT"), 
                        ("Drift Var", "CHAOS_DRIFT"), ("Kerning Var", "CHAOS_KERNING"), 
                        ("Space Var", "CHAOS_SPACE")]
        for i, (label, key) in enumerate(chaos_fields):
            r, c = divmod(i, 2)
            tk.Label(container, text=label).grid(row=r+12, column=c*2, sticky="e", padx=5, pady=2)
            ent = tk.Entry(container, width=10)
            ent.insert(0, str(self.settings.get(key, 0.0)))
            ent.grid(row=r+12, column=c*2+1, sticky="w", padx=5, pady=2)
            self.entries[key] = ent
            
        bg = tk.Frame(container)
        bg.grid(row=20, column=0, columnspan=4, pady=20)
        tk.Button(bg, text="Save & Apply All", command=self.save_and_apply, bg="#FF9800", fg="white").pack(side="left", padx=10)
        tk.Button(bg, text="Move Pen to Origin (X/Y)", command=self.move_to_origin).pack(side="left", padx=10)

    def on_toggle_lined_mode(self):
        if self.lined_mode_var.get():
            self.fs_scale.configure(state="disabled")
            auto_size = self.settings["LINE_SPACING"] * self.settings["LINE_RATIO"]
            self.font_size_val.set(round(auto_size, 2))
        else:
            self.fs_scale.configure(state="normal")
        self.preview_text()

    def save_and_apply(self):
        try:
            for key, ent in self.entries.items(): self.settings[key] = float(ent.get())
            self.settings["FLIP_X"], self.settings["FLIP_Y"] = self.flip_x_var.get(), self.flip_y_var.get()
            self.settings["ROTATE_90"] = self.rotate_90_var.get()
            self.settings["LINE_SPACING"] = float(self.line_space_ent.get())
            self.settings["TOP_MARGIN"] = float(self.top_margin_ent.get())
            self.settings["LINE_RATIO"] = float(self.line_ratio_ent.get())
            self.settings["FLOAT_OFFSET"] = float(self.float_offset_ent.get())
            self.settings["LEFT_MARGIN"] = float(self.left_margin_ent.get())
            self.settings["LINED_PAPER_MODE"] = self.lined_mode_var.get()
            self.settings["DRAW_GUIDE_LINES"] = self.draw_lines_var.get()
            settings_manager.save_settings(self.settings)
            self.update_canvas_dims()
            self.on_toggle_lined_mode()
            messagebox.showinfo("Saved", "Settings saved!")
        except Exception as e: messagebox.showerror("Error", str(e))

    def move_to_origin(self):
        fn = filedialog.asksaveasfilename(defaultextension=".gcode", initialfile="calibrate_origin.gcode")
        if fn:
            with open(fn, 'w') as f:
                f.write(f"G28\nM420 S1\nG0 Z{self.settings['Z_SAFE']} F1000\nG0 X{self.settings['X_MIN']} Y{self.settings['Y_MAX']} F3000\n")
            messagebox.showinfo("Done", "Calibration file saved.")

    def update_font_list(self):
        sel = [self.font_listbox.get(i) for i in self.font_listbox.curselection()]
        fonts = font_data.list_available_fonts()
        self.font_listbox.delete(0, tk.END)
        for i, f in enumerate(fonts):
            self.font_listbox.insert(tk.END, f)
            if f in sel or (not sel and f == "Hershey Simplex"):
                self.font_listbox.selection_set(i)
        self.preview_text()

    def preview_text(self):
        content = self.text_entry.get("1.0", tk.END).strip()
        self.preview_canvas.delete("all")
        is_rotated = self.rotate_90_var.get()
        if self.lined_mode_var.get():
            s, tm = self.settings["LINE_SPACING"], self.settings["TOP_MARGIN"]
            if is_rotated:
                curr_x = 0
                while curr_x <= (self.settings["X_MAX"] - self.settings["X_MIN"] - tm):
                    mx, _ = self.transform_paper_to_machine(0, -curr_x)
                    cx = (mx - self.settings["X_MIN"]) * self.SCALE
                    self.preview_canvas.create_line(cx, 0, cx, self.canvas_h, fill="#e0e0e0")
                    curr_x += s
            else:
                curr_y = 0
                while curr_y <= (self.settings["Y_MAX"] - self.settings["Y_MIN"] - tm):
                    _, my = self.transform_paper_to_machine(0, -curr_y)
                    cy = (self.settings["Y_MAX"] - my) * self.SCALE
                    self.preview_canvas.create_line(0, cy, self.canvas_w, cy, fill="#e0e0e0")
                    curr_y += s
        if not content: return
        fs = self.font_size_val.get()
        s, tm, fo, lm = self.settings["LINE_SPACING"], self.settings["TOP_MARGIN"], self.settings["FLOAT_OFFSET"], self.settings["LEFT_MARGIN"]
        lh = s if self.lined_mode_var.get() else fs * 1.5
        max_w = (self.settings["Y_MAX"] - self.settings["Y_MIN"] - lm) if is_rotated else (self.settings["X_MAX"] - self.settings["X_MIN"] - lm)
        # Start on second line (skewed by -s) and float up by float_offset
        start_y = (-s + fo) if self.lined_mode_var.get() else fo
        
        # Load fonts
        sel_indices = self.font_listbox.curselection()
        if not sel_indices:
            font_dicts = [font_data.HERSHEY_SIMPLEX]
        else:
            font_dicts = [font_data.load_font(self.font_listbox.get(i)) for i in sel_indices]
            
        humanize_val = self.humanize_var.get()
        
        self.text_strokes = font_data.get_text_strokes(content, font_dicts=font_dicts, font_size=fs, start_x=lm, start_y=start_y, max_width=max_w, line_height=lh, humanize=humanize_val, chaos_settings=self.settings)
        for stroke in self.text_strokes:
            pts = []
            for px, py in stroke:
                mx, my = self.transform_paper_to_machine(px, py)
                cx, cy = (mx - self.settings["X_MIN"]) * self.SCALE, (self.settings["Y_MAX"] - my) * self.SCALE
                pts.extend([cx, cy])
            if len(pts) >= 4: self.preview_canvas.create_line(pts, fill="blue", width=1)

    def transform_paper_to_machine(self, px, py):
        tm = self.settings["TOP_MARGIN"] if self.lined_mode_var.get() else 0
        fs = self.font_size_val.get()
        # Paper (px, py) is relative to top-left of paper. py decreases for new lines.
        # Hershey py=0 is baseline.
        if self.rotate_90_var.get():
            # Rotated 90 CW: Xp -> -Ym (Front), Yp -> +Xm (Right)
            mx = (self.settings["X_MAX"] - tm) + py
            my = self.settings["Y_MAX"] - px
        else:
            # Standard: Xp -> +Xm (Right), Yp -> +Ym (Back)
            mx = self.settings["X_MIN"] + px
            my = (self.settings["Y_MAX"] - tm) + py
        return self.apply_mirror_flip(mx, my)

    def apply_mirror_flip(self, mx, my):
        ox, oy = mx, my
        if self.settings["FLIP_X"]: ox = self.settings["X_MAX"] - (mx - self.settings["X_MIN"])
        if self.settings["FLIP_Y"]: oy = self.settings["Y_MIN"] + (self.settings["Y_MAX"] - my)
        return ox, oy

    def canvas_to_machine(self, cx, cy):
        mx = self.settings["X_MIN"] + (cx / self.SCALE)
        my = self.settings["Y_MAX"] - (cy / self.SCALE)
        return self.apply_mirror_flip(mx, my)

    def export_gcode(self, mode):
        strokes, speeds = [], []
        if mode == "text":
            self.preview_text() 
            is_rotated = self.rotate_90_var.get()
            if self.draw_lines_var.get():
                s, tm = self.settings["LINE_SPACING"], self.settings["TOP_MARGIN"]
                curr_l = 0
                limit = (self.settings["X_MAX"]-self.settings["X_MIN"]-tm) if is_rotated else (self.settings["Y_MAX"]-self.settings["Y_MIN"]-tm)
                while curr_l <= limit:
                    ls = [(curr_l, 0), (curr_l, (self.settings["Y_MAX"]-self.settings["Y_MIN"]) if is_rotated else (self.settings["X_MAX"]-self.settings["X_MIN"]))]
                    strokes.append([self.transform_paper_to_machine(p[1], -p[0]) for p in ls]) # Swap for guide lines
                    speeds.append(self.settings["F_TRACE"])
                    curr_l += s
            for s in self.text_strokes:
                strokes.append([self.transform_paper_to_machine(p[0], p[1]) for p in s])
                speeds.append(self.settings["F_DRAW"])
        else:
            for s in self.manual_strokes:
                strokes.append([self.canvas_to_machine(p[0], p[1]) for p in s])
                speeds.append(self.settings["F_DRAW"])
        if not strokes: return messagebox.showwarning("Warning", "Empty!")
        fn = filedialog.asksaveasfilename(defaultextension=".gcode")
        if not fn: return
        try:
            with open(fn, 'w') as f:
                f.write("M302 S0\nM211 S1\nG21\nG90\nG28\nM420 S1\n")
                f.write(f"G0 Z{self.settings['Z_SAFE']} F{self.settings['F_Z']}\n")
                for i, s in enumerate(strokes):
                    st = s[0]
                    if not (self.settings["X_MIN"]-0.5 <= st[0] <= self.settings["X_MAX"]+0.5 and self.settings["Y_MIN"]-0.5 <= st[1] <= self.settings["Y_MAX"]+0.5): continue
                    f.write(f"G0 X{st[0]:.2f} Y{st[1]:.2f} F{self.settings['F_TRAVEL']}\n")
                    f.write(f"G0 Z{self.settings['Z_DRAW']} F{self.settings['F_Z']}\n")
                    for p in s[1:]: f.write(f"G1 X{p[0]:.2f} Y{p[1]:.2f} F{speeds[i]}\n")
                    f.write(f"G0 Z{self.settings['Z_SAFE']} F{self.settings['F_Z']}\n")
                f.write("G0 Z10 F3000\nG0 X0 Y0 F3000\nM84\n")
            messagebox.showinfo("Success", "G-code exported!")
        except Exception as e: messagebox.showerror("Error", str(e))

    def start_stroke(self, e): self.current_stroke = [(e.x, e.y)]
    def draw_stroke(self, e):
        if self.current_stroke:
            x1, y1 = self.current_stroke[-1]
            if 0 <= e.x <= self.canvas_w and 0 <= e.y <= self.canvas_h:
                self.canvas.create_line(x1, y1, e.x, e.y, fill="black", width=2)
                self.current_stroke.append((e.x, e.y))
    def end_stroke(self, e):
        if len(self.current_stroke) > 1: self.manual_strokes.append(self.current_stroke)
        self.current_stroke = []
    def clear_canvas(self):
        self.canvas.delete("all"); self.manual_strokes = []

if __name__ == "__main__":
    root = tk.Tk(); app = GCodeDrawer(root); root.mainloop()
