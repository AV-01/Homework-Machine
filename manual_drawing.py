import tkinter as tk
from tkinter import filedialog, messagebox

# Machine Constants from CONTEXT.md
X_MIN, X_MAX = 80, 230
Y_MIN, Y_MAX = 40, 220
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
        self.root.title("Ender 3 Pen Plotter - G-Code Creator")
        self.root.resizable(False, False)
        
        self.strokes = [] # List of list of (x, y) coordinates
        self.current_stroke = []

        # Info Label
        self.info = tk.Label(root, text=f"Printable Area: {X_MAX-X_MIN}mm x {Y_MAX-Y_MIN}mm", font=("Arial", 10, "bold"))
        self.info.pack(pady=5)

        # UI Setup
        self.canvas = tk.Canvas(root, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg="white", highlightthickness=1, highlightbackground="gray")
        self.canvas.pack(padx=20, pady=10)
        
        self.btn_frame = tk.Frame(root)
        self.btn_frame.pack(fill="x", side="bottom", pady=15)
        
        self.btn_export = tk.Button(self.btn_frame, text="Generate & Export G-Code", command=self.export_gcode, bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), padx=10)
        self.btn_export.pack(side="right", padx=20)
        
        self.btn_clear = tk.Button(self.btn_frame, text="Clear Canvas", command=self.clear_canvas, font=("Arial", 10))
        self.btn_clear.pack(side="right", padx=10)

        # Drawing Events
        self.canvas.bind("<Button-1>", self.start_stroke)
        self.canvas.bind("<B1-Motion>", self.draw_stroke)
        self.canvas.bind("<ButtonRelease-1>", self.end_stroke)

    def start_stroke(self, event):
        self.current_stroke = [(event.x, event.y)]

    def draw_stroke(self, event):
        if self.current_stroke:
            x1, y1 = self.current_stroke[-1]
            x2, y2 = event.x, event.y
            # Limit drawing to canvas bounds
            if 0 <= x2 <= CANVAS_WIDTH and 0 <= y2 <= CANVAS_HEIGHT:
                self.canvas.create_line(x1, y1, x2, y2, fill="black", width=2, capstyle=tk.ROUND, smooth=tk.TRUE)
                self.current_stroke.append((x2, y2))

    def end_stroke(self, event):
        if len(self.current_stroke) > 1:
            self.strokes.append(self.current_stroke)
        self.current_stroke = []

    def clear_canvas(self):
        self.canvas.delete("all")
        self.strokes = []

    def canvas_to_machine(self, cx, cy):
        """Convert pixels to absolute physical machine coordinates."""
        # cx=0 -> X80, cx=CANVAS_WIDTH -> X230
        mx = X_MIN + (cx / SCALE)
        # cy=0 -> Y220, cy=CANVAS_HEIGHT -> Y40 (Flipped Y axis)
        my = Y_MAX - (cy / SCALE)
        return mx, my

    def export_gcode(self):
        if not self.strokes:
            messagebox.showwarning("Warning", "The canvas is empty! Please draw something first.")
            return
            
        filename = filedialog.asksaveasfilename(
            title="Save G-Code",
            defaultextension=".gcode", 
            filetypes=[("G-code Files", "*.gcode"), ("All Files", "*.*")]
        )
        if not filename:
            return

        try:
            with open(filename, 'w') as f:
                # Initialization (From CONTEXT.md)
                f.write("; --- INITIALIZATION ---\n")
                f.write("M302 S0 ; Allow cold moves (ignore extruder minimum temp)\n")
                f.write("M211 S1 ; SAFETY ON - Honor physical machine limits\n")
                f.write("G21 ; Set units to millimeters\n")
                f.write("G90 ; Set to absolute positioning\n")
                f.write("G28 ; Home all axes\n")
                f.write("M420 S1 ; Load pre-saved CR-Touch mesh\n")
                f.write(f"G0 Z{Z_SAFE} F{F_Z} ; Initial lift\n\n")
                
                f.write("; --- DRAWING STROKES ---\n")
                for i, stroke in enumerate(self.strokes):
                    f.write(f"; Stroke {i+1}\n")
                    # Move to start of stroke aloft
                    start_x, start_y = self.canvas_to_machine(*stroke[0])
                    f.write(f"G0 X{start_x:.2f} Y{start_y:.2f} F{F_TRAVEL}\n")
                    
                    # Drop pen
                    f.write(f"G0 Z{Z_DRAW} F{F_Z} ; Pen Down\n")
                    
                    # Draw points
                    for point in stroke[1:]:
                        x, y = self.canvas_to_machine(*point)
                        f.write(f"G1 X{x:.2f} Y{y:.2f} F{F_DRAW}\n")
                    
                    # Lift pen immediately
                    f.write(f"G0 Z{Z_SAFE} F{F_Z} ; Pen Up\n\n")
                
                # Shutdown (From CONTEXT.md)
                f.write("; --- SHUTDOWN ---\n")
                f.write("G0 Z10 F3000 ; Fast high lift to clear paper\n")
                f.write("G0 X0 Y0 F3000 ; Return home\n")
                f.write("M84 ; Disable motors\n")
            
            messagebox.showinfo("Success", f"G-code successfully exported to:\n{filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = GCodeDrawer(root)
    root.mainloop()
