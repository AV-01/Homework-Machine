EVERYTHING IS COPY PASTED FROM PRUSA SLICER
FOR ENDER 3 PRINTER

START G-CODE:
G90 ; use absolute coordinates
M83 ; extruder relative mode
M104 S{is_nil(idle_temperature[0]) ? 150 : idle_temperature[0]} ; set temporary nozzle temp to prevent oozing during homing
M140 S{first_layer_bed_temperature[0]} ; set final bed temp
G4 S30 ; allow partial nozzle warmup
G28 ; home all axis
M420 S1
G1 Z50 F240
G1 X2.0 Y10 F3000
M104 S{first_layer_temperature[0]} ; set final nozzle temp
M190 S{first_layer_bed_temperature[0]} ; wait for bed temp to stabilize
M109 S{first_layer_temperature[0]} ; wait for nozzle temp to stabilize
G1 Z0.28 F240
G92 E0
G1 X2.0 Y140 E10 F1500 ; prime the nozzle
G1 X2.3 Y140 F5000
G92 E0
G1 X2.3 Y10 E10 F1200 ; prime the nozzle
G92 E0

Option to emit all temperature commands automatically: enabled

END G-CODE:
{if max_layer_z < max_print_height}G1 Z{z_offset+min(max_layer_z+2, max_print_height)} F600 ; Move print head up{endif}
G1 X5 Y{print_bed_max[1]*0.85} F{travel_speed*60} ; present print
{if max_layer_z < max_print_height-10}G1 Z{z_offset+min(max_layer_z+70, max_print_height-10)} F600 ; Move print head further up{endif}
{if max_layer_z < max_print_height*0.6}G1 Z{max_print_height*0.6} F600 ; Move print head further up{endif}
M140 S0 ; turn off heatbed
M104 S0 ; turn off temperature
M107 ; turn off fan
M84 X Y E ; disable motors

BEFORE LAYER CHANGE:
;BEFORE_LAYER_CHANGE
G92 E0
;{layer_z}

AFTER LAYER CHANGE:
;AFTER_LAYER_CHANGE
;{layer_z}