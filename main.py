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
        
        # Initialize UI state
        self.on_toggle_lined_mode()

    def update_canvas_dims(self):
        self.canvas_w = (self.settings["X_MAX"] - self.settings["X_MIN"]) * self.SCALE
        self.canvas_h = (self.settings["Y_MAX"] - self.settings["Y_MIN"]) * self.SCALE

    def setup_draw_tab(self):
        self.draw_info = tk.Label(self.draw_tab, text=f"Printable: {self.settings['X_MIN']}-{self.settings['X_MAX']} x {self.settings['Y_MIN']}-{self.settings['Y_MAX']}")
        self.draw_info.pack(pady=5)
        
        self.canvas = tk.Canvas(self.draw_tab, width=self.canvas_w, height=self.canvas_h, bg="white", highlightthickness=1)
        self.canvas.pack(padx=20, pady=5)
        
        btn_frame = tk.Frame(self.draw_tab)
        btn_frame.pack(fill="x", pady=10)
        tk.Button(btn_frame, text="Clear", command=self.clear_canvas).pack(side="left", padx=20)
        tk.Button(btn_frame, text="Export G-Code", command=lambda: self.export_gcode("draw"), bg="#4CAF50", fg="white").pack(side="right", padx=20)

        self.canvas.bind("<Button-1>", self.start_stroke)
        self.canvas.bind("<B1-Motion>", self.draw_stroke)
        self.canvas.bind("<ButtonRelease-1>", self.end_stroke)

    def setup_text_tab(self):
        tk.Label(self.text_tab, text="Enter Homework Text:", font=("Arial", 9, "bold")).pack(anchor="w", padx=20, pady=(5,0))
        self.text_entry = scrolledtext.ScrolledText(self.text_tab, height=4)
        self.text_entry.pack(padx=20, pady=5, fill="x")
        
        ctrl_frame = tk.Frame(self.text_tab)
        ctrl_frame.pack(fill="x", padx=20)
        
        tk.Label(ctrl_frame, text="Font Size (mm):").pack(side="left")
        self.font_size_val = tk.DoubleVar(value=round(self.settings["LINE_SPACING"] * self.settings["LINE_RATIO"], 2))
        self.font_size_scale = tk.Scale(ctrl_frame, from_=3, to_=30, resolution=0.1, orient="horizontal", variable=self.font_size_val, length=120, command=lambda x: self.preview_text())
        self.font_size_scale.pack(side="left", padx=5)
        
        self.lined_mode_var = tk.BooleanVar(value=self.settings["LINED_PAPER_MODE"])
        self.lined_cb = tk.Checkbutton(ctrl_frame, text="Lined Paper Mode", variable=self.lined_mode_var, command=self.on_toggle_lined_mode)
        self.lined_cb.pack(side="left", padx=5)

        self.draw_lines_var = tk.BooleanVar(value=self.settings["DRAW_GUIDE_LINES"])
        self.draw_lines_cb = tk.Checkbutton(ctrl_frame, text="Draw Guide Lines", variable=self.draw_lines_var)
        self.draw_lines_cb.pack(side="left", padx=5)

        self.preview_canvas = tk.Canvas(self.text_tab, width=self.canvas_w, height=self.canvas_h, bg="#f9f9f9", highlightthickness=1)
        self.preview_canvas.pack(padx=20, pady=10)
        
        btn_frame = tk.Frame(self.text_tab)
        btn_frame.pack(fill="x", pady=5)
        tk.Button(btn_frame, text="Refresh Preview", command=self.preview_text).pack(side="left", padx=20)
        tk.Button(btn_frame, text="Export G-Code", command=lambda: self.export_gcode("text"), bg="#2196F3", fg="white").pack(side="right", padx=20)

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

        tk.Label(container, text="Preferences & Lined Paper", font=("Arial", 10, "bold")).grid(row=6, column=0, columnspan=4, sticky="w", pady=(15,10))
        self.flip_x_var = tk.BooleanVar(value=self.settings["FLIP_X"])
        tk.Checkbutton(container, text="Reverse X Axis", variable=self.flip_x_var).grid(row=7, column=0, sticky="w")
        self.flip_y_var = tk.BooleanVar(value=self.settings["FLIP_Y"])
        tk.Checkbutton(container, text="Reverse Y Axis", variable=self.flip_y_var).grid(row=7, column=1, sticky="w")

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

        btn_frame = tk.Frame(container)
        btn_frame.grid(row=10, column=0, columnspan=4, pady=20)
        tk.Button(btn_frame, text="Save & Apply All", command=self.save_and_apply, bg="#FF9800", fg="white").pack(side="left", padx=10)
        tk.Button(btn_frame, text="Move Pen to Origin (X/Y)", command=self.move_to_origin).pack(side="left", padx=10)

    # --- LOGIC ---
    def on_toggle_lined_mode(self):
        if self.lined_mode_var.get():
            self.font_size_scale.configure(state="disabled")
            auto_size = self.settings["LINE_SPACING"] * self.settings["LINE_RATIO"]
            self.font_size_val.set(round(auto_size, 2))
        else:
            self.font_size_scale.configure(state="normal")
        self.preview_text()

    def save_and_apply(self):
        try:
            for key, ent in self.entries.items(): self.settings[key] = float(ent.get())
            self.settings["FLIP_X"] = self.flip_x_var.get()
            self.settings["FLIP_Y"] = self.flip_y_var.get()
            self.settings["LINE_SPACING"] = float(self.line_space_ent.get())
            self.settings["TOP_MARGIN"] = float(self.top_margin_ent.get())
            self.settings["LINE_RATIO"] = float(self.line_ratio_ent.get())
            self.settings["LINED_PAPER_MODE"] = self.lined_mode_var.get()
            self.settings["DRAW_GUIDE_LINES"] = self.draw_lines_var.get()
            
            settings_manager.save_settings(self.settings)
            self.update_canvas_dims()
            self.on_toggle_lined_mode() # Re-apply auto-sizing logic
            messagebox.showinfo("Saved", "Settings saved and applied!")
        except Exception as e:
            messagebox.showerror("Error", f"Invalid input: {e}")

    def move_to_origin(self):
        filename = filedialog.asksaveasfilename(defaultextension=".gcode", initialfile="calibrate_origin.gcode")
        if filename:
            with open(filename, 'w') as f:
                f.write("G28\nM420 S1\n")
                f.write(f"G0 Z{self.settings['Z_SAFE']} F1000\n")
                f.write(f"G0 X{self.settings['X_MIN']} Y{self.settings['Y_MAX']} F3000\n")
            messagebox.showinfo("Done", "Calibration file saved.")

    def preview_text(self):
        content = self.text_entry.get("1.0", tk.END).strip()
        self.preview_canvas.delete("all")
        
        if self.lined_mode_var.get():
            spacing = self.settings["LINE_SPACING"]
            top_m = self.settings["TOP_MARGIN"]
            curr_y_mm = self.settings["Y_MAX"] - top_m
            while curr_y_mm >= self.settings["Y_MIN"]:
                cy = (self.settings["Y_MAX"] - curr_y_mm) * self.SCALE
                self.preview_canvas.create_line(0, cy, self.canvas_w, cy, fill="#e0e0e0")
                curr_y_mm -= spacing

        if not content: return
        
        fontSize = self.font_size_val.get()
        is_lined = self.lined_mode_var.get()
        lineHeight = self.settings["LINE_SPACING"] if is_lined else fontSize * 1.5
        startY = (self.settings["Y_MAX"] - self.settings["TOP_MARGIN"]) if is_lined else self.settings["Y_MAX"]
        
        self.text_strokes = font_data.get_text_strokes(
            content, font_size=fontSize, 
            start_x=self.settings["X_MIN"], start_y=startY,
            max_width=self.settings["X_MAX"]-self.settings["X_MIN"],
            line_height=lineHeight
        )
        
        for stroke in self.text_strokes:
            points = []
            for mx, my in stroke:
                cx = (mx - self.settings["X_MIN"]) * self.SCALE
                cy = (self.settings["Y_MAX"] - my) * self.SCALE
                points.extend([cx, cy])
            if len(points) >= 4: self.preview_canvas.create_line(points, fill="blue", width=1)

    def transform_point(self, mx, my):
        out_x, out_y = mx, my
        if self.settings["FLIP_X"]: out_x = self.settings["X_MAX"] - (mx - self.settings["X_MIN"])
        if self.settings["FLIP_Y"]: out_y = self.settings["Y_MIN"] + (self.settings["Y_MAX"] - my)
        return out_x, out_y

    def canvas_to_machine(self, cx, cy):
        mx = self.settings["X_MIN"] + (cx / self.SCALE)
        my = self.settings["Y_MAX"] - (cy / self.SCALE)
        return self.transform_point(mx, my)

    def export_gcode(self, mode):
        process_strokes = []
        stroke_speeds = [] # Track which speed to use for each stroke

        # Handle guide lines if mode is text and setting is enabled
        if mode == "text" and self.draw_lines_var.get():
            spacing = self.settings["LINE_SPACING"]
            top_m = self.settings["TOP_MARGIN"]
            curr_y_mm = self.settings["Y_MAX"] - top_m
            while curr_y_mm >= self.settings["Y_MIN"]:
                # Full width line
                line_stroke = [(self.settings["X_MIN"], curr_y_mm), (self.settings["X_MAX"], curr_y_mm)]
                transformed_stroke = [self.transform_point(p[0], p[1]) for p in line_stroke]
                process_strokes.append(transformed_stroke)
                stroke_speeds.append(self.settings["F_TRACE"])
                curr_y_mm -= spacing

        if mode == "draw":
            for s in self.manual_strokes:
                process_strokes.append([self.canvas_to_machine(p[0], p[1]) for p in s])
                stroke_speeds.append(self.settings["F_DRAW"])
        else: # mode == "text"
            self.preview_text()
            for s in self.text_strokes:
                process_strokes.append([self.transform_point(p[0], p[1]) for p in s])
                stroke_speeds.append(self.settings["F_DRAW"])

        if not process_strokes:
            messagebox.showwarning("Warning", "No content!")
            return
            
        filename = filedialog.asksaveasfilename(defaultextension=".gcode")
        if not filename: return

        try:
            with open(filename, 'w') as f:
                f.write("; Generated G-Code\n")
                f.write("M302 S0\nM211 S1\nG21\nG90\nG28\nM420 S1\n")
                f.write(f"G0 Z{self.settings['Z_SAFE']} F{self.settings['F_Z']}\n")
                
                for idx, stroke in enumerate(process_strokes):
                    current_speed = stroke_speeds[idx]
                    
                    # Truncation check
                    start_pt = stroke[0]
                    if not (self.settings["X_MIN"]-0.5 <= start_pt[0] <= self.settings["X_MAX"]+0.5 and 
                            self.settings["Y_MIN"]-0.5 <= start_pt[1] <= self.settings["Y_MAX"]+0.5):
                        continue
                        
                    f.write(f"G0 X{start_pt[0]:.2f} Y{start_pt[1]:.2f} F{self.settings['F_TRAVEL']}\n")
                    f.write(f"G0 Z{self.settings['Z_DRAW']} F{self.settings['F_Z']}\n")
                    for pt in stroke[1:]:
                        f.write(f"G1 X{pt[0]:.2f} Y{pt[1]:.2f} F{current_speed}\n")
                    f.write(f"G0 Z{self.settings['Z_SAFE']} F{self.settings['F_Z']}\n")
                
                f.write(f"G0 Z10 F3000\nG0 X0 Y0 F3000\nM84\n")
            messagebox.showinfo("Success", "G-code exported!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = GCodeDrawer(root)
    root.mainloop()
