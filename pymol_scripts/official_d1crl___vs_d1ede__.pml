
reinitialize
bg_color white
load /Users/huyue/singleRMSD_v2/RPIC_all/d1ede__.pdb, reference
load /Users/huyue/singleRMSD_v2/official_tmalign_results/d1crl___vs_d1ede__.pdb, mobile

color green, reference
color magenta, mobile

set ray_trace_frames, 1
set ray_shadows, off

orient

png /Users/huyue/singleRMSD_v2/pymol_images/official_d1crl___vs_d1ede__, width=800, height=600, dpi=300, ray=1
