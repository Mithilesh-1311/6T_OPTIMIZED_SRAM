# SAMS data audit

Dataset `56fd2a89b9e4`. 47 originals; decisions: {'accepted': 30, 'superseded': 14, 'ambiguous': 1, 'rejected': 2}.
Accepted waveform/DC data rows: 1,693,678. These are not independent ML cases.

Conditions combine historical setup/netlist record and trace checks; raw exports do not independently certify temperature, corner or complete topology.

| Original | Decision | Rows | Reason / quality flags |
|---|---|---:|---|
| ACTIVE_HOLD_DATA0.vcsv.txt | accepted | 100158 | Final configured revision; signal/window checks applied; net11: ambiguous units s/yunit; net14: ambiguous units s/yunit |
| active_hold_data0_85c.vcsv.txt | accepted | 100136 | Final configured revision; signal/window checks applied; net11: ambiguous units s/yunit; net14: ambiguous units s/yunit |
| ACTIVE_HOLD_DATA1.vcsv.txt | superseded | 100167 | Missing retention-source current; COMPLETE export used; net11: ambiguous units s/yunit |
| active_hold_data1_85c.vcsv.txt | accepted | 100141 | Final configured revision; signal/window checks applied; net11: ambiguous units s/yunit |
| ACTIVE_HOLD_DATA1_COMPLETE.vcsv.txt | accepted | 100167 | Final configured revision; signal/window checks applied; net11: ambiguous units s/yunit |
| active_sel0_85c.vcsv.txt | accepted | 60250 | Final configured revision; signal/window checks applied; net16: ambiguous units s/yunit |
| active_sel1_85c.vcsv.txt | accepted | 60304 | Final configured revision; signal/window checks applied;  |
| active_vdd09_27c_sel0.txt | accepted | 60299 | Final configured revision; signal/window checks applied; net16: ambiguous units s/yunit |
| active_vdd09_27c_sel1.txt | superseded | 60361 | Original long-mode SEL=1 V; corrected _f uses 0.9 V;  |
| active_vdd09_27c_sel1_f.txt | accepted | 60350 | Final configured revision; signal/window checks applied;  |
| active_vdd09_85c_sel0.txt | accepted | 60265 | Final configured revision; signal/window checks applied; net16: ambiguous units s/yunit |
| active_vdd09_85c_sel1.txt | superseded | 60334 | Original long-mode SEL=1 V; corrected _f uses 0.9 V;  |
| active_vdd09_85c_sel1_f.txt | accepted | 60320 | Final configured revision; signal/window checks applied;  |
| FILE .vcsv.txt | superseded | 1041 | Earlier design revision, coarse/incomplete export or companion traces; excluded from final revision;  |
| ret_data0_27c_vret08.vcsv.txt | accepted | 100183 | Final configured revision; signal/window checks applied;  |
| ret_data0_85c_vret08.vcsv.txt | accepted | 100163 | Final configured revision; signal/window checks applied;  |
| ret_data1_27c_vret08.vcsv.txt | accepted | 100194 | Final configured revision; signal/window checks applied;  |
| ret_data1_85c_vret08.vcsv.txt | accepted | 100168 | Final configured revision; signal/window checks applied;  |
| RETENTION_BIT0.vcsv.txt | ambiguous | 100215 | Earlier uncertain pulsed DATA; replaced by verified DC bit0 run;  |
| retention_data0_85c.vcsv.txt | accepted | 100163 | Final configured revision; signal/window checks applied; net14: ambiguous units s/yunit |
| RETENTION_DATA0_DC.vcsv.txt | accepted | 100194 | Final configured revision; signal/window checks applied;  |
| RETENTION_DATA0_DC_FIXED.vcsv.txt | superseded | 100183 | Related bit1 evidence; not independent of accepted mislabeled DATA0_DC export; net14: ambiguous units s/yunit |
| retention_data0_fresh.vcsv.txt | accepted | 100183 | Final configured revision; signal/window checks applied;  |
| retention_data1_85c.vcsv.txt | accepted | 100168 | Final configured revision; signal/window checks applied;  |
| RETENTION_VDATA_1.vcsv.txt | superseded | 100194 | Related bit1 evidence; not independent of accepted mislabeled DATA0_DC export;  |
| SEL0.vcsv.txt | superseded | 1041 | Earlier design revision, coarse/incomplete export or companion traces; excluded from final revision;  |
| sel01ps.vcsv.txt | superseded | 60258 | Earlier design revision, coarse/incomplete export or companion traces; excluded from final revision;  |
| sel0conservative.vcsv.txt | superseded | 2061 | Earlier design revision, coarse/incomplete export or companion traces; excluded from final revision;  |
| sel0updated.txt | accepted | 60284 | Final configured revision; signal/window checks applied;  |
| sel0updated.vcsv.docx | rejected | unavailable | Empty non-numerical file; No columns to parse from file |
| SEL1.vcsv.txt | superseded | 1046 | Earlier design revision, coarse/incomplete export or companion traces; excluded from final revision;  |
| sel1conservative.vcsv.txt | superseded | 2263 | Earlier design revision, coarse/incomplete export or companion traces; excluded from final revision;  |
| sel1ps.vcsv.txt | superseded | 60302 | Earlier design revision, coarse/incomplete export or companion traces; excluded from final revision;  |
| sel1updated.vcsv.txt | accepted | 60378 | Final configured revision; signal/window checks applied;  |
| SELV0.vcsv.txt | superseded | 1041 | Earlier design revision, coarse/incomplete export or companion traces; excluded from final revision;  |
| SELV1.vcsv.txt | superseded | 1046 | Earlier design revision, coarse/incomplete export or companion traces; excluded from final revision;  |
| SNM_HOLD_08V_27C_F.txt | accepted | 801 | Final configured revision; signal/window checks applied;  |
| SNM_HOLD_08V_85C_F.txt | accepted | 801 | Final configured revision; signal/window checks applied;  |
| SNM_HOLD_09V_27C.txt | accepted | 901 | Final configured revision; signal/window checks applied;  |
| SNM_HOLD_09V_85C.txt | accepted | 901 | Final configured revision; signal/window checks applied;  |
| SNM_HOLD_1V_27C.txt | rejected | 1792 | Floating pull-down/WL; invalid VTC and reverse sweep in historical record; Q: nonmonotonic axis; QB: nonmonotonic axis; VIN: nonmonotonic axis |
| SNM_HOLD_1V_27C_F.txt | accepted | 1001 | Final configured revision; signal/window checks applied;  |
| SNM_HOLD_1V_85C.txt | accepted | 1001 | Final configured revision; signal/window checks applied;  |
| SNM_READ_09V_27C.txt | accepted | 901 | Final configured revision; signal/window checks applied;  |
| SNM_READ_09V_85C.txt | accepted | 901 | Final configured revision; signal/window checks applied;  |
| SNM_READ_1V_27C_F.txt | accepted | 1001 | Final configured revision; signal/window checks applied;  |
| SNM_READ_1V_85C_F.txt | accepted | 1001 | Final configured revision; signal/window checks applied;  |

Exact duplicate groups: []. Shared signal groups are recorded in audit.json; never count these as new runs.

The accepted RETENTION_DATA0_DC export is bit 1 despite its name. Read-SNM files now exist, superseding the older guide's pending status. No public datasets were found or downloaded. Empty/invalid files, related exports and historical revisions remain preserved.