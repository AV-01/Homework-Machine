# Context Document: Ender 3 Hybrid Pen Plotter G-Code Generator

## Project Overview
This project involves generating custom G-code to operate an Original Ender 3 3D printer modified into a 2D pen plotter. The system relies on a rigid, custom 3D-printed mount holding a Pilot G2 gel pen. 

## Hardware Constraints & Setup
* **Base Machine:** Original Ender 3 (Not Pro, S1, or V2 variants) running Marlin Firmware.
* **Active Tool:** Pilot G2 Gel Pen. **Crucial Note:** The pen tip sits physically lower than the hotend nozzle. The hotend is completely inactive but remains on the carriage.
* **Z-Axis Compensation:** The project uses the internal spring of the Pilot G2 pen to absorb slight bed variations. This requires a specific Z-height that applies a slight "squish" (compression) to the spring during drawing.
* **Bed Leveling:** Equipped with a CR-Touch. To avoid dragging the pen during active probing (G29), the system relies on a pre-saved bed mesh (loaded via `M420 S1`).

## Coordinate System & Verified Calibrations
The following physical coordinates and parameters have been tested and verified to work without triggering Marlin's software endstops or conflicting with internal hotend-to-probe offsets (`M851`). Do NOT use `G92` to spoof coordinates; use absolute physical machine coordinates.

* **Printable Paper Bounds (Absolute X/Y):**
    * Bottom-Left: (80, 40)
    * Top-Left: (80, 220)
    * Top-Right: (230, 220)
    * Bottom-Right: (230, 40)
* **Z-Axis Heights:**
    * **Safe Travel Height:** `Z10` (Used for moving between strokes or large travel moves).
    * **Draw Height:** `Z1.52` (Verified height that touches the paper with perfect spring compression).
* **Speeds (Feedrates):**
    * Travel Moves (Air): `F3000` (50 mm/s)
    * Draw Moves (Paper): `F2000` (33 mm/s)
    * Z-Axis Lifts/Drops: `F1000` (16 mm/s)

## G-Code Generation Rules
Any script or agent generating G-code for this machine MUST follow these structural rules:

1.  **Safety & Initialization Boilerplate:** Every file must begin with exactly this initialization block to prevent firmware conflicts:
    ```gcode
    M302 S0 ; Allow cold moves (ignore extruder minimum temp)
    M211 S1 ; SAFETY ON - Honor physical machine limits
    G21 ; Set units to millimeters
    G90 ; Set to absolute positioning
    G28 ; Home all axes
    M420 S1 ; Load pre-saved CR-Touch mesh
    ```
2.  **No Extrusion:** Never output `E` values or extruder commands.
3.  **Mandatory Z-Hopping:** The Pilot G2 pen will bleed ink if left resting on the paper. 
    * Before *any* X/Y travel move without drawing, the pen MUST be lifted (`G0 Z5` or `G0 Z10`).
    * The pen must be lifted *immediately* upon finishing a stroke.
4.  **End of Print Boilerplate:** Every file must end by safely lifting the pen and parking the carriage:
    ```gcode
    G0 Z10 F3000 ; Fast high lift to clear paper
    G0 X0 Y0 F3000 ; Return home
    M84 ; Disable motors
    ```