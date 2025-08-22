
reinitialize
bg_color white
load /Users/huyue/singleRMSD_v2/RPIC_all/d1mup__.pdb, reference
load /Users/huyue/singleRMSD_v2/batch_outputs_cutoff_7.0/d1adl___aligned_to_d1mup___0821.pdb, mobile

color green, reference
color magenta, mobile

set ray_trace_frames, 1
set ray_shadows, off

orient

png /Users/huyue/singleRMSD_v2/pymol_images/gemini_d1adl___vs_d1mup__, width=800, height=600, dpi=300, ray=1
