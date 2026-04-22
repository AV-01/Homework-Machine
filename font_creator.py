import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import os
import json
import font_data

SCALE = 20
CX = 400
CYBaseline = 220  # Adjusted so Y=-4 is centered

def h2s_x(hx): return CX + (hx * SCALE)
def h2s_y(hy): return CYBaseline - (hy * SCALE)
def s2h_x(px): return (px - CX) / SCALE
def s2h_y(py): return (CYBaseline - py) / SCALE


class FontCreatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tkinter Handwriting Font Creator")
        self.root.geometry("1100x700")

        self.fonts_dir = font_data.get_fonts_dir()
        os.makedirs(self.fonts_dir, exist_ok=True)

        self.current_font = None
        self.font_dict = {}
        self.current_char = "A"
        
        self.bounds = [-10.0, 10.0] # Left, Right
        self.strokes = []
        self.current_stroke = []

        self.dragging_bound = None

        self.setup_ui()
        self.refresh_font_list()
        
    def setup_ui(self):
        # Sidebar
        sidebar = tk.Frame(self.root, width=250, bg="#f0f0f0")
        sidebar.pack(side="left", fill="y", padx=10, pady=10)

        tk.Label(sidebar, text="Font Management", font=("Arial", 12, "bold"), bg="#f0f0f0").pack(pady=(0, 10))
        
        self.font_listbox = tk.Listbox(sidebar, height=10)
        self.font_listbox.pack(fill="x", pady=5)
        self.font_listbox.bind("<<ListboxSelect>>", self.on_font_select)

        new_font_btn = tk.Button(sidebar, text="Create New Font", command=self.create_new_font)
        new_font_btn.pack(fill="x", pady=5)

        tk.Label(sidebar, text="Characters in Font:", font=("Arial", 10, "bold"), bg="#f0f0f0").pack(pady=(20, 5))
        self.char_listbox = tk.Listbox(sidebar)
        self.char_listbox.pack(fill="both", expand=True, pady=5)
        self.char_listbox.bind("<<ListboxSelect>>", self.on_char_select)

        # Main Area
        main_area = tk.Frame(self.root)
        main_area.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        # Toolbar
        toolbar = tk.Frame(main_area)
        toolbar.pack(fill="x", pady=5)

        tk.Label(toolbar, text="Current Character:", font=("Arial", 11)).pack(side="left")
        self.char_entry = tk.Entry(toolbar, width=5, font=("Arial", 14), justify="center")
        self.char_entry.insert(0, "A")
        self.char_entry.pack(side="left", padx=10)
        self.char_entry.bind("<KeyRelease>", self.on_char_entry_change)

        tk.Button(toolbar, text="Auto-Fit All", command=self.auto_fit_all, bg="#00BCD4", fg="white").pack(side="right", padx=5)
        tk.Button(toolbar, text="Auto-Fit Bounds", command=self.auto_fit_bounds, bg="#2196F3", fg="white").pack(side="right", padx=5)
        tk.Button(toolbar, text="Clear Canvas", command=self.clear_canvas).pack(side="right", padx=5)
        tk.Button(toolbar, text="Undo \u238c", command=self.undo_stroke).pack(side="right", padx=5)
        tk.Button(toolbar, text="Delete Character", command=self.delete_char, fg="red").pack(side="right", padx=20)
        tk.Button(toolbar, text="Save Character", command=self.save_char, bg="#4CAF50", fg="white", font=("Arial", 10, "bold")).pack(side="right", padx=5)

        # Canvas
        self.canvas = tk.Canvas(main_area, width=800, height=600, bg="#1e1e1e", cursor="crosshair")
        self.canvas.pack(pady=10)

        self.canvas.bind("<Button-1>", self.on_pointer_down)
        self.canvas.bind("<B1-Motion>", self.on_pointer_move)
        self.canvas.bind("<ButtonRelease-1>", self.on_pointer_up)

        self.status_var = tk.StringVar(value="Ready")
        tk.Label(main_area, textvariable=self.status_var, anchor="w", fg="gray").pack(fill="x")

        self.render()

    def refresh_font_list(self):
        self.font_listbox.delete(0, tk.END)
        fonts = []
        for f in os.listdir(self.fonts_dir):
            if f.endswith(".json"):
                fonts.append(f[:-5])
        for f in sorted(fonts):
            self.font_listbox.insert(tk.END, f)
            
    def create_new_font(self):
        name = simpledialog.askstring("New Font", "Enter new font name:")
        if name:
            path = os.path.join(self.fonts_dir, f"{name}.json")
            if not os.path.exists(path):
                with open(path, "w") as f: json.dump({}, f)
                self.refresh_font_list()
                self.status_var.set(f"Created font '{name}'")
            else:
                messagebox.showerror("Error", "Font already exists.")

    def on_font_select(self, event):
        sel = self.font_listbox.curselection()
        if not sel: return
        self.current_font = self.font_listbox.get(sel[0])
        path = os.path.join(self.fonts_dir, f"{self.current_font}.json")
        try:
            with open(path, "r") as f:
                self.font_dict = json.load(f)
        except Exception:
            self.font_dict = {}
        
        self.status_var.set(f"Loaded font '{self.current_font}'")
        self.refresh_char_list()
        self.load_character(self.char_entry.get())

    def refresh_char_list(self):
        self.char_listbox.delete(0, tk.END)
        for char in sorted(self.font_dict.keys()):
            self.char_listbox.insert(tk.END, char)

    def on_char_select(self, event):
        sel = self.char_listbox.curselection()
        if not sel: return
        char = self.char_listbox.get(sel[0])
        self.char_entry.delete(0, tk.END)
        self.char_entry.insert(0, char)
        self.load_character(char)

    def on_char_entry_change(self, event):
        char = self.char_entry.get()
        if len(char) == 1:
            self.load_character(char)

    def load_character(self, char):
        self.current_char = char
        if char in self.font_dict:
            data = self.font_dict[char]
            self.bounds = [data[0], data[1]]
            self.strokes = data[2:]
        else:
            self.bounds = [-10.0, 10.0]
            self.strokes = []
        self.render()

    def save_char(self):
        if not self.current_font:
            return messagebox.showwarning("Warning", "Select a font first!")
        char = self.char_entry.get()
        if not char: return

        # Format: [left, right, stroke1, stroke2, ...]
        data = [round(self.bounds[0], 2), round(self.bounds[1], 2)] + self.strokes
        self.font_dict[char] = data
        
        path = os.path.join(self.fonts_dir, f"{self.current_font}.json")
        with open(path, "w") as f:
            json.dump(self.font_dict, f, indent=2)
            
        self.status_var.set(f"Saved character '{char}'")
        self.refresh_char_list()

    def delete_char(self):
        char = self.char_entry.get()
        if char in self.font_dict:
            del self.font_dict[char]
            path = os.path.join(self.fonts_dir, f"{self.current_font}.json")
            with open(path, "w") as f:
                json.dump(self.font_dict, f, indent=2)
            self.refresh_char_list()
            self.load_character(char)
            self.status_var.set(f"Deleted character '{char}'")

    def undo_stroke(self):
        if self.strokes:
            self.strokes.pop()
            self.render()

    def clear_canvas(self):
        self.strokes = []
        self.render()
        
    def auto_fit_bounds(self):
        """Automatically set left/right boundaries based on stroke extents plus margin."""
        if not self.strokes:
            return
        min_x = float('inf')
        max_x = float('-inf')
        for stroke in self.strokes:
            for hx, hy in stroke:
                if hx < min_x: min_x = hx
                if hx > max_x: max_x = hx
                
        if min_x != float('inf'):
            # Standard Hershey padding is generally 2 units on each side
            self.bounds[0] = round(min_x - 2.0, 1)
            self.bounds[1] = round(max_x + 2.0, 1)
            self.render()
            self.status_var.set("Automatically fitted boundary lines.")

    def auto_fit_all(self):
        """Automatically set left/right boundaries for EVERY character in the current font."""
        if not self.current_font or not self.font_dict:
            return messagebox.showwarning("Warning", "Select a font with characters first!")
        
        updated_count = 0
        for char, data in self.font_dict.items():
            strokes = data[2:]
            if not strokes: continue
            
            min_x = float('inf')
            max_x = float('-inf')
            for stroke in strokes:
                for hx, hy in stroke:
                    if hx < min_x: min_x = hx
                    if hx > max_x: max_x = hx
                    
            if min_x != float('inf'):
                data[0] = round(min_x - 2.0, 1)
                data[1] = round(max_x + 2.0, 1)
                updated_count += 1
                
        if updated_count > 0:
            path = os.path.join(self.fonts_dir, f"{self.current_font}.json")
            with open(path, "w") as f:
                json.dump(self.font_dict, f, indent=2)
            self.load_character(self.current_char) # Refresh current view constraints
            messagebox.showinfo("Success", f"Auto-fitted bounds for {updated_count} characters in '{self.current_font}'!")
        else:
            messagebox.showinfo("Done", "No characters found with strokes to fit.")

    # Drawing Logic
    def on_pointer_down(self, e):
        hx = s2h_x(e.x)
        hy = s2h_y(e.y)
        
        # Check boundary drag
        if abs(hx - self.bounds[0]) < 1.0:
            self.dragging_bound = 0
            return
        if abs(hx - self.bounds[1]) < 1.0:
            self.dragging_bound = 1
            return
            
        # Start drawing points
        pt = [round(hx, 1), round(hy, 1)]
        self.current_stroke = [pt]
        self.strokes.append(self.current_stroke)
        self.render()

    def on_pointer_move(self, e):
        hx = s2h_x(e.x)
        hy = s2h_y(e.y)

        if self.dragging_bound is not None:
            self.bounds[self.dragging_bound] = hx
            self.render()
            return
            
        if self.current_stroke is not None:
            pt = [round(hx, 1), round(hy, 1)]
            last_pt = self.current_stroke[-1]
            dist = ((pt[0] - last_pt[0])**2 + (pt[1] - last_pt[1])**2)**0.5
            if dist > 0.5:
                self.current_stroke.append(pt)
                self.render()
                # Partial draw optimization instead of full wipe and render
                idx = len(self.current_stroke) - 1
                p1 = self.current_stroke[idx-1]
                p2 = self.current_stroke[idx]
                self.canvas.create_line(h2s_x(p1[0]), h2s_y(p1[1]), h2s_x(p2[0]), h2s_y(p2[1]), fill="white", width=3, capstyle=tk.ROUND)

    def on_pointer_up(self, e):
        self.current_stroke = None
        self.dragging_bound = None
        self.render()

    def render(self):
        self.canvas.delete("all")
        
        # Guidelines (Based on Hershey Simplex actual bounds)
        guides = [
            (10, "Cap Height", "#4a4a4a"),
            (2, "Mean Line", "#3a3a3a"),
            (0, "Center Y", "#333333"),
            (-10, "Baseline (py = -10)", "#7a7a5a"), 
            (-18, "Descender", "#4a4a4a")
        ]
        
        for hy, label, color in guides:
            sy = h2s_y(hy)
            dash_pattern = (2,2) if hy == 0 else (4, 4)
            self.canvas.create_line(0, sy, 800, sy, fill=color, dash=dash_pattern)
            self.canvas.create_text(10, sy - 10, text=label, fill="gray", anchor="w")
            
        # Center X-axis
        self.canvas.create_line(CX, 0, CX, 600, fill="#2a2a2a")

        # Reference Hershey Character (Outline)
        ref_data = font_data.HERSHEY_SIMPLEX.get(self.current_char)
        if ref_data:
            ref_strokes = ref_data[2:]
            for stroke in ref_strokes:
                if len(stroke) < 2: continue
                pts = []
                for hx, hy in stroke:
                    pts.extend([h2s_x(hx), h2s_y(hy)])
                self.canvas.create_line(pts, fill="#3a4a5a", width=2, capstyle=tk.ROUND, joinstyle=tk.ROUND)


        # Bounds
        b_left = h2s_x(self.bounds[0])
        self.canvas.create_line(b_left, 0, b_left, 600, fill="#2196F3", width=2, dash=(6, 6))
        self.canvas.create_polygon(b_left, 10, b_left-8, 0, b_left+8, 0, fill="#2196F3") # Drag handle
        
        b_right = h2s_x(self.bounds[1])
        self.canvas.create_line(b_right, 0, b_right, 600, fill="#2196F3", width=2, dash=(6, 6))
        self.canvas.create_polygon(b_right, 10, b_right-8, 0, b_right+8, 0, fill="#2196F3") # Drag handle

        # Strokes
        for stroke in self.strokes:
            if len(stroke) < 2: continue
            pts = []
            for hx, hy in stroke:
                pts.extend([h2s_x(hx), h2s_y(hy)])
            self.canvas.create_line(pts, fill="white", width=3, capstyle=tk.ROUND, joinstyle=tk.ROUND)

if __name__ == "__main__":
    root = tk.Tk()
    app = FontCreatorApp(root)
    root.mainloop()
