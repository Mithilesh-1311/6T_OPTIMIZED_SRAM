"""Explicit acceptance and conditions from historical setup, verified against traces."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
DERIVED = ROOT / "data/derived"
ARTIFACTS = ROOT / "artifacts"
MAPPING = {"wl": "net2", "bl": "net3", "blb": "net4", "cell": "net5", "main": "net6", "wen": "net13", "data": "net14", "preb": "net19"}

def accepted():
    runs = {}
    def add(file, kind, vdd=1., temp=27, mode=None, bit=None, vret=.9):
        runs[file] = dict(kind=kind, vdd_v=vdd, temp_c=temp, mode=mode, bit=bit, vret_v=vret,
                          provenance="Historical setup/netlist record + waveform consistency; temperature not encoded in raw export")
    for temp in (27,85):
        for mode in (0,1):
            add(("sel0updated.txt" if mode == 0 else "sel1updated.vcsv.txt") if temp==27 else f"active_sel{mode}_85c.vcsv.txt", "active", temp=temp, mode=mode)
            add(f"active_vdd09_{temp}c_sel{mode}{'_f' if mode else ''}.txt", "active", .9, temp, mode, vret=.8)
        for bit in (0,1):
            hold = ("ACTIVE_HOLD_DATA0.vcsv.txt" if bit==0 else "ACTIVE_HOLD_DATA1_COMPLETE.vcsv.txt") if temp==27 else f"active_hold_data{bit}_85c.vcsv.txt"
            add(hold, "active_hold", temp=temp, bit=bit)
            ret = ("retention_data0_fresh.vcsv.txt" if bit==0 else "RETENTION_DATA0_DC.vcsv.txt") if temp==27 else f"retention_data{bit}_85c.vcsv.txt"
            add(ret, "retention", temp=temp, bit=bit)
            add(f"ret_data{bit}_{temp}c_vret08.vcsv.txt", "retention", temp=temp, bit=bit, vret=.8)
        for v in (1.,.9,.8):
            token = {1.:"1V", .9:"09V", .8:"08V"}[v]
            suffix = "_F" if v==.8 or (v==1. and temp==27) else ""
            add(f"SNM_HOLD_{token}_{temp}C{suffix}.txt", "hold_snm", v, temp)
        for v in (1.,.9):
            token = "1V" if v==1 else "09V"
            add(f"SNM_READ_{token}_{temp}C{'_F' if v==1 else ''}.txt", "read_snm", v, temp)
    return runs

def exclusion(name):
    if name.endswith(".docx"):
        return "rejected", "Empty non-numerical file"
    if name == "SNM_HOLD_1V_27C.txt":
        return "rejected", "Floating pull-down/WL; invalid VTC and reverse sweep in historical record"
    if name == "RETENTION_BIT0.vcsv.txt":
        return "ambiguous", "Earlier uncertain pulsed DATA; replaced by verified DC bit0 run"
    if name == "ACTIVE_HOLD_DATA1.vcsv.txt":
        return "superseded", "Missing retention-source current; COMPLETE export used"
    if name in ("RETENTION_DATA0_DC_FIXED.vcsv.txt", "RETENTION_VDATA_1.vcsv.txt"):
        return "superseded", "Related bit1 evidence; not independent of accepted mislabeled DATA0_DC export"
    if name.startswith("active_vdd09_"):
        return "superseded", "Original long-mode SEL=1 V; corrected _f uses 0.9 V"
    return "superseded", "Earlier design revision, coarse/incomplete export or companion traces; excluded from final revision"
