
reinitialize
bg_color white
load /Users/huyue/singleRMSD_v2/RPIC_all/d2trcb_.pdb, reference
load /Users/huyue/singleRMSD_v2/batch_outputs_cutoff_7.0/d1olza2_aligned_to_d2trcb__0821.pdb, mobile

color green, reference
color magenta, mobile

set ray_trace_frames, 1
set ray_shadows, off

orient

png /Users/huyue/singleRMSD_v2/pymol_images/gemini_d1olza2_vs_d2trcb_, width=800, height=600, dpi=300, ray=1
