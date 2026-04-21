import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import settings_manager
import os

class LineDrawer:
    def __init__(self, root):
        self.root = root
        self.root.title("Ender 3 Line Drawer Utility")
        self.root.resizable(False, False)
        
        self.settings = settings_manager.load_settings()
        self.SCALE = 3
        self.update_canvas_dims()
        
        self.setup_ui()
        self.update_preview()

    def update_canvas_dims(self):
        self.canvas_w = (self.settings["X_MAX"] - self.settings["X_MIN"]) * self.SCALE
        self.canvas_h = (self.settings["Y_MAX"] - self.settings["Y_MIN"]) * self.SCALE

    def setup_ui(self):
        # Settings Panel
        side_panel = tk.Frame(self.root, padx=10, pady=10, borderwidth=1, relief="sunken")
        side_panel.pack(side="left", fill="y")

        tk.Label(side_panel, text="Line Settings", font=("Arial", 10, "bold")).pack(pady=(0, 10))

        # Mode Selection
        tk.Label(side_panel, text="Tool Mode", font=("Arial", 9, "bold")).pack(anchor="w", pady=(10, 0))
        self.tool_mode_var = tk.StringVar(value=self.settings["TOOL_MODE"])
        mode_cb = ttk.Combobox(side_panel, textvariable=self.tool_mode_var, values=["Pen", "Hotend"], state="readonly")
        mode_cb.pack(fill="x", pady=5)
        mode_cb.bind("<<ComboboxSelected>>", lambda e: self.toggle_mode())

        # Fields
        self.vars = {}
        self.fields_frame = tk.Frame(side_panel)
        self.fields_frame.pack(fill="x")
        
        self.create_fields()
        
        # Checkboxes
        self.rotate_90_var = tk.BooleanVar(value=self.settings["ROTATE_90"])
        tk.Checkbutton(side_panel, text="Rotate 90\u00b0", variable=self.rotate_90_var, command=self.update_preview).pack(anchor="w", pady=2)
        
        self.flip_x_var = tk.BooleanVar(value=self.settings["FLIP_X"])
        tk.Checkbutton(side_panel, text="Flip X", variable=self.flip_x_var, command=self.update_preview).pack(anchor="w", pady=2)
        
        self.flip_y_var = tk.BooleanVar(value=self.settings["FLIP_Y"])
        tk.Checkbutton(side_panel, text="Flip Y", variable=self.flip_y_var, command=self.update_preview).pack(anchor="w", pady=2)

        tk.Button(side_panel, text="Save Settings", command=self.save_settings, bg="#FF9800", fg="white").pack(fill="x", pady=10)
        tk.Button(side_panel, text="Export G-Code", command=self.export_gcode, bg="#4CAF50", fg="white", font=("Arial", 10, "bold")).pack(fill="x", pady=5)

        # Preview Panel
        preview_panel = tk.Frame(self.root, padx=10, pady=10)
        preview_panel.pack(side="right", fill="both", expand=True)
        
        tk.Label(preview_panel, text="Preview (Machine Coordinates)", font=("Arial", 10, "bold")).pack()
        self.canvas = tk.Canvas(preview_panel, width=self.canvas_w, height=self.canvas_h, bg="#f0f0f0", highlightthickness=1)
        self.canvas.pack(pady=10)
        
        self.info_label = tk.Label(preview_panel, text="")
        self.info_label.pack()
        
        self.toggle_mode()

    def create_fields(self):
        for widget in self.fields_frame.winfo_children():
            widget.destroy()
            
        fields = [
            ("Line Spacing (mm)", "LINE_SPACING"),
            ("Top Margin (mm)", "TOP_MARGIN"),
            ("Travel Speed", "F_TRAVEL"),
            ("Trace Speed", "F_TRACE"),
            ("Z Safe", "Z_SAFE"),
            ("Z Draw", "Z_DRAW")
        ]
        
        if self.tool_mode_var.get() == "Hotend":
            fields.extend([
                ("Nozzle Temp", "NOZZLE_TEMP"),
                ("Bed Temp", "BED_TEMP"),
                ("Extrusion Ratio", "EXTRUSION_RATIO"),
                ("Hotend Z Height", "HOTEND_Z")
            ])

        for label, key in fields:
            frame = tk.Frame(self.fields_frame)
            frame.pack(fill="x", pady=2)
            tk.Label(frame, text=label, width=15, anchor="w").pack(side="left")
            var = tk.DoubleVar(value=self.settings[key])
            ent = tk.Entry(frame, textvariable=var, width=8)
            ent.pack(side="right")
            self.vars[key] = var
            var.trace_add("write", lambda *args: self.update_preview())

    def toggle_mode(self):
        self.create_fields()
        self.update_preview()

    def update_preview(self):
        try:
            # Temporarily update settings from UI for preview
            for key, var in self.vars.items():
                self.settings[key] = var.get()
            self.settings["ROTATE_90"] = self.rotate_90_var.get()
            self.settings["FLIP_X"] = self.flip_x_var.get()
            self.settings["FLIP_Y"] = self.flip_y_var.get()
            self.settings["TOOL_MODE"] = self.tool_mode_var.get()
            
            self.canvas.delete("all")
            
            # Draw boundary outline if Hotend mode
            if self.tool_mode_var.get() == "Hotend":
                self.draw_preview_outline()

            strokes = self.generate_line_strokes()
            for s in strokes:
                pts = []
                for mx, my in s:
                    cx = (mx - self.settings["X_MIN"]) * self.SCALE
                    cy = (self.settings["Y_MAX"] - my) * self.SCALE
                    pts.extend([cx, cy])
                if len(pts) >= 4:
                    self.canvas.create_line(pts, fill="blue", width=1)
            
            self.info_label.config(text=f"Total Lines: {len(strokes)}")
        except:
            pass

    def draw_preview_outline(self):
        self.canvas.create_rectangle(0, 0, self.canvas_w, self.canvas_h, outline="red", dash=(4, 4))

    def generate_line_strokes(self):
        s, tm = self.settings["LINE_SPACING"], self.settings["TOP_MARGIN"]
        is_rotated = self.settings["ROTATE_90"]
        
        strokes = []
        curr_l = 0
        
        limit = (self.settings["X_MAX"] - self.settings["X_MIN"] - tm) if is_rotated else (self.settings["Y_MAX"] - self.settings["Y_MIN"] - tm)
        line_len = (self.settings["Y_MAX"] - self.settings["Y_MIN"]) if is_rotated else (self.settings["X_MAX"] - self.settings["X_MIN"])
        
        while curr_l <= limit:
            ls = [(0, -curr_l), (line_len, -curr_l)]
            m_stroke = []
            for px, py in ls:
                if is_rotated:
                    mx = (self.settings["X_MAX"] - tm) + py
                    my = self.settings["Y_MAX"] - px
                else:
                    mx = self.settings["X_MIN"] + px
                    my = (self.settings["Y_MAX"] - tm) + py
                
                ox, oy = mx, my
                if self.settings["FLIP_X"]: ox = self.settings["X_MAX"] - (mx - self.settings["X_MIN"])
                if self.settings["FLIP_Y"]: oy = self.settings["Y_MIN"] + (self.settings["Y_MAX"] - my)
                m_stroke.append((ox, oy))
            
            strokes.append(m_stroke)
            curr_l += s
        return strokes

    def save_settings(self):
        try:
            for key, var in self.vars.items():
                self.settings[key] = var.get()
            self.settings["ROTATE_90"] = self.rotate_90_var.get()
            self.settings["FLIP_X"] = self.flip_x_var.get()
            self.settings["FLIP_Y"] = self.flip_y_var.get()
            self.settings["TOOL_MODE"] = self.tool_mode_var.get()
            
            settings_manager.save_settings(self.settings)
            messagebox.showinfo("Success", "Settings saved to settings.json")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    def export_gcode(self):
        strokes = self.generate_line_strokes()
        if not strokes:
            return messagebox.showwarning("Warning", "No lines to export!")
            
        fn = filedialog.asksaveasfilename(defaultextension=".gcode", initialfile="guide_lines.gcode")
        if not fn:
            return
            
        try:
            is_hotend = (self.tool_mode_var.get() == "Hotend")
            nt = self.settings["NOZZLE_TEMP"] if is_hotend else 0
            bt = self.settings["BED_TEMP"] if is_hotend else 0
            er = self.settings["EXTRUSION_RATIO"] if is_hotend else 0
            draw_z = self.settings["HOTEND_Z"] if is_hotend else self.settings["Z_DRAW"]

            with open(fn, 'w') as f:
                if is_hotend:
                    # Hotend Start G-code
                    f.write("; Ender 3 Hotend Print Guide Lines\n")
                    f.write("G90 ; use absolute coordinates\n")
                    f.write("M83 ; extruder relative mode\n")
                    f.write(f"M104 S{150} ; preheat nozzle\n")
                    f.write(f"M140 S{bt} ; set bed temp\n")
                    f.write("G28 ; home all axis\n")
                    f.write("M420 S1\n")
                    f.write("G1 Z50 F240\n")
                    f.write("G1 X2.0 Y10 F3000\n")
                    f.write(f"M104 S{nt} ; set nozzle temp\n")
                    f.write(f"M190 S{bt} ; wait for bed temp\n")
                    f.write(f"M109 S{nt} ; wait for nozzle temp\n")
                    f.write("G1 Z0.28 F240\n")
                    f.write("G92 E0\n")
                    f.write("G1 X2.0 Y140 E10 F1500 ; prime\n")
                    f.write("G1 X2.3 Y140 F5000\n")
                    f.write("G92 E0\n")
                    f.write("G1 X2.3 Y10 E10 F1200 ; prime\n")
                    f.write("G92 E0\n")
                else:
                    # Pen Start G-code
                    f.write("; Ender 3 Pen Draw Guide Lines\n")
                    f.write("M302 S0 ; Allow cold moves\n")
                    f.write("M211 S1 ; Safety ON\n")
                    f.write("G21 ; Units mm\n")
                    f.write("G90 ; Absolute positioning\n")
                    f.write("G28 ; Home\n")
                    f.write("M420 S1 ; Load mesh\n")
                    f.write(f"G0 Z{self.settings['Z_SAFE']} F1000\n")

                if is_hotend:
                    # Print boundary outline
                    f.write("; Boundary Outline\n")
                    xmin, xmax = self.settings["X_MIN"], self.settings["X_MAX"]
                    ymin, ymax = self.settings["Y_MIN"], self.settings["Y_MAX"]
                    outline = [(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax), (xmin, ymin)]
                    
                    f.write(f"G0 X{outline[0][0]:.2f} Y{outline[0][1]:.2f} Z{draw_z} F{self.settings['F_TRAVEL']}\n")
                    for p in outline[1:]:
                        dist = ((p[0]-outline[0][0])**2 + (p[1]-outline[0][1])**2)**0.5
                        ext = dist * er
                        f.write(f"G1 X{p[0]:.2f} Y{p[1]:.2f} E{ext:.4f} F{self.settings['F_TRACE']}\n")
                
                for s in strokes:
                    p1, p2 = s[0], s[1]
                    f.write(f"G0 X{p1[0]:.2f} Y{p1[1]:.2f} F{self.settings['F_TRAVEL']}\n")
                    f.write(f"G0 Z{draw_z} F1000\n")
                    
                    if is_hotend:
                        dist = ((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)**0.5
                        ext = dist * er
                        f.write(f"G1 X{p2[0]:.2f} Y{p2[1]:.2f} E{ext:.4f} F{self.settings['F_TRACE']}\n")
                    else:
                        f.write(f"G1 X{p2[0]:.2f} Y{p2[1]:.2f} F{self.settings['F_TRACE']}\n")
                    
                    f.write(f"G0 Z{self.settings['Z_SAFE']} F1000\n")
                
                if is_hotend:
                    # Hotend End G-code
                    f.write("; Hotend Teardown\n")
                    f.write("G1 Z2.0 F600 ; Move up\n")
                    f.write("G1 X5 Y200 F3000 ; present print\n")
                    f.write("M140 S0 ; turn off bed\n")
                    f.write("M104 S0 ; turn off nozzle\n")
                    f.write("M107 ; turn off fan\n")
                    f.write("M84 X Y E ; disable motors\n")
                else:
                    # Pen End G-code
                    f.write("G0 Z10 F3000 ; Clear paper\n")
                    f.write("G0 X0 Y0 F3000 ; Return home\n")
                    f.write("M84 ; Disable motors\n")
                
            messagebox.showinfo("Success", f"G-code exported to {os.path.basename(fn)}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = LineDrawer(root)
    root.mainloop()
