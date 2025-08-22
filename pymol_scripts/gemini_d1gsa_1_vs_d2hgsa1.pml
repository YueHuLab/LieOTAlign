
reinitialize
bg_color white
load /Users/huyue/singleRMSD_v2/RPIC_all/d2hgsa1.pdb, reference
load /Users/huyue/singleRMSD_v2/batch_outputs_cutoff_7.0/d1gsa_1_aligned_to_d2hgsa1_0821.pdb, mobile

color green, reference
color magenta, mobile

set ray_trace_frames, 1
set ray_shadows, off

orient

png /Users/huyue/singleRMSD_v2/pymol_images/gemini_d1gsa_1_vs_d2hgsa1, width=800, height=600, dpi=300, ray=1
