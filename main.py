import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext
import font_data

# Machine Constants from CONTEXT.md
# X_MIN, X_MAX = 80, 230
# Y_MIN, Y_MAX = 40, 220
X_MIN, X_MAX = 66, 235
Y_MIN, Y_MAX = 50, 235
Z_SAFE = 10
Z_DRAW = 1.52
F_TRAVEL = 3000
F_DRAW = 2000
F_Z = 1000

# UI Scaling (3 pixels per mm)
SCALE = 3
CANVAS_WIDTH = (X_MAX - X_MIN) * SCALE
CANVAS_HEIGHT = (Y_MAX - Y_MIN) * SCALE

class GCodeDrawer:
    def __init__(self, root):
        self.root = root
        self.root.title("Ender 3 Pen Plotter - G-Code Machine")
        self.root.resizable(False, False)
        
        # Data storage
        self.manual_strokes = [] # List of list of (x, y) coordinates
        self.text_strokes = []
        self.current_stroke = []

        # UI Setup - Notebook for Tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(padx=10, pady=10, expand=True, fill="both")
        
        # --- TAB 1: MANUAL DRAWING ---
        self.draw_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.draw_tab, text=" Manual Drawing ")
        
        self.draw_info = tk.Label(self.draw_tab, text=f"Printable Area: {X_MAX-X_MIN}mm x {Y_MAX-Y_MIN}mm", font=("Arial", 10))
        self.draw_info.pack(pady=5)
        
        self.canvas = tk.Canvas(self.draw_tab, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg="white", highlightthickness=1, highlightbackground="gray")
        self.canvas.pack(padx=20, pady=5)
        
        self.draw_btn_frame = tk.Frame(self.draw_tab)
        self.draw_btn_frame.pack(fill="x", pady=10)
        
        self.btn_clear = tk.Button(self.draw_btn_frame, text="Clear Canvas", command=self.clear_canvas)
        self.btn_clear.pack(side="left", padx=20)
        
        self.btn_export_draw = tk.Button(self.draw_btn_frame, text="Export Manual G-Code", command=lambda: self.export_gcode("draw"), bg="#4CAF50", fg="white", font=("Arial", 10, "bold"))
        self.btn_export_draw.pack(side="right", padx=20)

        # Draw Events
        self.canvas.bind("<Button-1>", self.start_stroke)
        self.canvas.bind("<B1-Motion>", self.draw_stroke)
        self.canvas.bind("<ButtonRelease-1>", self.end_stroke)

        # --- TAB 2: TEXT AUTO-GENERATION ---
        self.text_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.text_tab, text=" Text to G-Code ")
        
        self.text_input_label = tk.Label(self.text_tab, text="Enter Text to Plot:", font=("Arial", 10, "bold"))
        self.text_input_label.pack(anchor="w", padx=20, pady=(10, 0))
        
        self.text_entry = scrolledtext.ScrolledText(self.text_tab, height=5, font=("Arial", 10))
        self.text_entry.pack(padx=20, pady=5, fill="both")
        
        # Tools frame
        self.tools_frame = tk.Frame(self.text_tab)
        self.tools_frame.pack(fill="x", padx=20, pady=5)
        
        tk.Label(self.tools_frame, text="Font Size (mm):").pack(side="left")
        self.font_size_val = tk.DoubleVar(value=10.0)
        self.font_size_scale = tk.Scale(self.tools_frame, from_=5, to_=40, resolution=0.5, orient="horizontal", variable=self.font_size_val, length=200)
        self.font_size_scale.pack(side="left", padx=10)
        
        # Text Preview Canvas (Smaller visualization)
        self.preview_canvas = tk.Canvas(self.text_tab, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg="#f0f0f0", highlightthickness=1)
        self.preview_canvas.pack(padx=20, pady=10)
        
        self.text_btn_frame = tk.Frame(self.text_tab)
        self.text_btn_frame.pack(fill="x", pady=10)
        
        self.btn_preview_text = tk.Button(self.text_btn_frame, text="Preview Layout", command=self.preview_text)
        self.btn_preview_text.pack(side="left", padx=20)
        
        self.btn_export_text = tk.Button(self.text_btn_frame, text="Export Text G-Code", command=lambda: self.export_gcode("text"), bg="#2196F3", fg="white", font=("Arial", 10, "bold"))
        self.btn_export_text.pack(side="right", padx=20)

    # --- DRAWING METHODS ---
    def start_stroke(self, event):
        self.current_stroke = [(event.x, event.y)]

    def draw_stroke(self, event):
        if self.current_stroke:
            x1, y1 = self.current_stroke[-1]
            x2, y2 = event.x, event.y
            if 0 <= x2 <= CANVAS_WIDTH and 0 <= y2 <= CANVAS_HEIGHT:
                self.canvas.create_line(x1, y1, x2, y2, fill="black", width=2, capstyle=tk.ROUND, smooth=tk.TRUE)
                self.current_stroke.append((x2, y2))

    def end_stroke(self, event):
        if len(self.current_stroke) > 1:
            self.manual_strokes.append(self.current_stroke)
        self.current_stroke = []

    def clear_canvas(self):
        self.canvas.delete("all")
        self.manual_strokes = []

    # --- TEXT METHODS ---
    def preview_text(self):
        content = self.text_entry.get("1.0", tk.END).strip()
        if not content:
            return
        
        self.preview_canvas.delete("all")
        # Draw dotted bounds
        self.preview_canvas.create_rectangle(2, 2, CANVAS_WIDTH-2, CANVAS_HEIGHT-2, outline="gray", dash=(2, 4))
        
        fontSize = self.font_size_val.get()
        # Generate strokes for machine space (80..230, 40..220)
        self.text_strokes = font_data.get_text_strokes(content, font_size=fontSize)
        
        # Draw on preview canvas (needs machine -> canvas conversion)
        for stroke in self.text_strokes:
            points = []
            for mx, my in stroke:
                cx = (mx - X_MIN) * SCALE
                cy = (Y_MAX - my) * SCALE
                points.extend([cx, cy])
            if len(points) >= 4:
                self.preview_canvas.create_line(points, fill="blue", width=1)

    # --- COORDINATE CONVERSION ---
    def canvas_to_machine(self, cx, cy):
        mx = X_MIN + (cx / SCALE)
        my = Y_MAX - (cy / SCALE)
        return mx, my

    # --- G-CODE GENERATION ---
    def export_gcode(self, mode):
        if mode == "draw":
            strokes_to_export = self.manual_strokes
            # Convert screen pixels to machine coords
            process_strokes = []
            for s in strokes_to_export:
                process_strokes.append([self.canvas_to_machine(p[0], p[1]) for p in s])
        else:
            self.preview_text() # Ensure latest text is processed
            process_strokes = self.text_strokes # Already in machine space

        if not process_strokes:
            messagebox.showwarning("Warning", "Nothing to export! Draw something or enter text.")
            return
            
        filename = filedialog.asksaveasfilename(
            title="Save G-Code",
            defaultextension=".gcode", 
            filetypes=[("G-code Files", "*.gcode")]
        )
        if not filename:
            return

        try:
            with open(filename, 'w') as f:
                # Initialization (From CONTEXT.md)
                f.write("; --- INITIALIZATION ---\n")
                f.write("M302 S0 ; Allow cold moves\n")
                f.write("M211 S1 ; SAFETY ON\n")
                f.write("G21 ; Units mm\n")
                f.write("G90 ; Absolute positioning\n")
                f.write("G28 ; Home\n")
                f.write("M420 S1 ; Load mesh\n")
                f.write(f"G0 Z{Z_SAFE} F{F_Z}\n\n")
                
                f.write(f"; --- {mode.upper()} CONTENT ---\n")
                for stroke in process_strokes:
                    # Move to start of stroke
                    f.write(f"G0 X{stroke[0][0]:.2f} Y{stroke[0][1]:.2f} F{F_TRAVEL}\n")
                    f.write(f"G0 Z{Z_DRAW} F{F_Z} ; Down\n")
                    
                    for pt in stroke[1:]:
                        f.write(f"G1 X{pt[0]:.2f} Y{pt[1]:.2f} F{F_DRAW}\n")
                    
                    f.write(f"G0 Z{Z_SAFE} F{F_Z} ; Up\n\n")
                
                # Shutdown (From CONTEXT.md)
                f.write("; --- SHUTDOWN ---\n")
                f.write("G0 Z10 F3000 ; Fast high lift\n")
                f.write("G0 X0 Y0 F3000 ; Return home\n")
                f.write("M84 ; Disable motors\n")
            
            messagebox.showinfo("Success", f"Exported successfully to:\n{filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = GCodeDrawer(root)
    root.mainloop()
