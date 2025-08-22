
reinitialize
bg_color white
load /Users/huyue/singleRMSD_v2/RPIC_all/d1kxf__.pdb, reference
load /Users/huyue/singleRMSD_v2/official_tmalign_results/d1hava__vs_d1kxf__.pdb, mobile

color green, reference
color magenta, mobile

set ray_trace_frames, 1
set ray_shadows, off

orient

png /Users/huyue/singleRMSD_v2/pymol_images/official_d1hava__vs_d1kxf__, width=800, height=600, dpi=300, ray=1
