"""SAMS numerical primitives. All calculations use original signal grids in SI."""
from dataclasses import dataclass
from pathlib import Path
import csv
import re
import numpy as np
import pandas as pd

UNITS = {"s": ("s", 1.), "ns": ("s", 1e-9), "ps": ("s", 1e-12),
         "us": ("s", 1e-6), "V": ("V", 1.), "mV": ("V", 1e-3),
         "A": ("A", 1.), "mA": ("A", 1e-3), "uA": ("A", 1e-6), "nA": ("A", 1e-9)}

@dataclass
class Signal:
    name: str
    x: np.ndarray
    y: np.ndarray
    axis: str
    unit: str
    flags: list

    def valid(self, axis=None, unit=None):
        if self.flags or (axis and self.axis != axis) or (unit and self.unit != unit):
            raise ValueError(f"Invalid signal {self.name}: {self.flags}, {self.axis}/{self.unit}")
        return self


def parse(path: Path):
    """ViVA paired X/Y or CSV columns with explicit units, e.g. time[ns],Q[mV]."""
    with path.open(encoding="utf-8-sig") as f:
        lines = [f.readline().strip() for _ in range(6)]
    if lines[0].startswith(";Version"):
        names = [s.strip().lstrip(";").lstrip("/") for s in next(csv.reader([lines[1]]))]
        units = [s.strip().lstrip(";") for s in next(csv.reader([lines[5]]))]
        if len(units) != 2 * len(names):
            raise ValueError("VCSV unit/column count mismatch")
        frame = pd.read_csv(path, skiprows=6, header=None, float_precision="round_trip")
        if frame.shape[1] != len(units):
            raise ValueError("VCSV data/column count mismatch")
        pairs = [(n, frame.iloc[:, 2*i], frame.iloc[:, 2*i+1], units[2*i], units[2*i+1]) for i, n in enumerate(names)]
    else:
        frame = pd.read_csv(path, comment=";", float_precision="round_trip")
        if frame.empty or len(frame.columns) < 2:
            raise ValueError("No numerical signal pairs")
        def label(s):
            m = re.fullmatch(r"(.+?)\s*\[([^]]+)\]", s.strip())
            if not m:
                raise ValueError("CSV requires explicit units: time[ns],Q[V]")
            return m.groups()
        if frame.shape[1] % 2 == 0 and all(label(c)[0].lower() in ("time", "dc", "voltage", "vin", "x") for c in frame.columns[::2]):
            pairs = [(label(frame.columns[i+1])[0], frame.iloc[:, i], frame.iloc[:, i+1], label(frame.columns[i])[1], label(frame.columns[i+1])[1]) for i in range(0, frame.shape[1], 2)]
        else:
            xu = label(frame.columns[0])[1]
            pairs = [(label(c)[0], frame.iloc[:, 0], frame[c], xu, label(c)[1]) for c in frame.columns[1:]]
    signals = {}
    for name, xs, ys, xu, yu in pairs:
        if name in signals:
            raise ValueError("Duplicate signal name")
        empty = xs.isna() & ys.isna()
        x = pd.to_numeric(xs[~empty], errors="coerce").to_numpy(dtype=float)
        y = pd.to_numeric(ys[~empty], errors="coerce").to_numpy(dtype=float)
        axis, xf = UNITS.get(xu, (xu, 1.))
        unit, yf = UNITS.get(yu, (yu, 1.))
        x, y = x*xf, y*yf
        flags = []
        if xu not in UNITS or yu not in UNITS:
            flags.append(f"ambiguous units {xu}/{yu}")
        if len(x) < 2 or not np.isfinite(x).all() or not np.isfinite(y).all():
            flags.append("missing/nonfinite samples")
        if len(x) > 1 and not np.all(np.diff(x) > 0):
            flags.append("nonmonotonic axis")
        signals[name] = Signal(name, x, y, axis, unit, flags)
    return signals, len(frame)


def window(s: Signal, start, end):
    s.valid()
    tolerance = 16*np.finfo(float).eps*max(abs(start),abs(end),abs(s.x[-1]))
    if end <= start or start < s.x[0]-tolerance or end > s.x[-1]+tolerance:
        raise ValueError(f"Incomplete event window for {s.name}")
    start, end = max(start,s.x[0]), min(end,s.x[-1])
    x = np.r_[start, s.x[(s.x > start) & (s.x < end)], end]
    return x, np.interp(x, s.x, s.y)


def crossings(s, threshold, direction, start, end):
    s.valid("s", "V")
    x, y = window(s, start, end)
    a, b = y[:-1]-threshold, y[1:]-threshold
    idx = np.flatnonzero((a < 0) & (b >= 0) if direction == "rise" else (a > 0) & (b <= 0))
    return x[idx] - a[idx]*(x[idx+1]-x[idx])/(b[idx]-a[idx])


def write_delay(wl, q, qb, supply, event_ns, bit):
    start, end = (event_ns-1)*1e-9, (event_ns+8)*1e-9
    rises = crossings(wl, supply/2, "rise", start, end)
    if len(rises) != 1:
        raise ValueError("Missing/ambiguous wordline event")
    edge = rises[0]
    falls = crossings(wl, supply/2, "fall", edge, end)
    if not len(falls):
        raise ValueError("Missing wordline falling edge")
    fall = falls[0]
    events = crossings(q, supply/2, "rise" if bit else "fall", edge, fall)
    if len(events) != 1:
        raise ValueError("Missing/ambiguous storage-node crossing")
    # Check the entire post-WL interval, ending before the next scheduled access.
    for signal, high in ((q, bit), (qb, 1-bit)):
        signal.valid("s", "V")
        _, values = window(signal, fall+0.2e-9, min(end, (event_ns+9)*1e-9))
        if not np.all(values > .8*supply if high else values < .2*supply):
            raise ValueError("Electrical failure: written state did not persist")
    return {"delay_ps": float((events[0]-edge)*1e12), "wl_rise_ns": float(edge*1e9),
            "q_cross_ns": float(events[0]*1e9), "wl_fall_ns": float(fall*1e9)}


def energy(signals, rails, start_ns, end_ns):
    total = 0.
    for name, voltage in rails.items():
        signal = signals[name].valid("s", "A")
        x, current = window(signal, start_ns*1e-9, end_ns*1e-9)
        total += -voltage * np.trapz(current, x)
    return float(total * 1e15)


def survival(signals, bit, cell_name):
    q, qb, cell = (signals[n].valid("s", "V") for n in ("Q", "QB", cell_name))
    for start, end in ((25., 65.), (75., 100.)):
        for sig, high in ((q, bit), (qb, 1-bit)):
            x, y = window(sig, start*1e-9, end*1e-9)
            if x[0] < cell.x[0] or x[-1] > cell.x[-1]:
                raise ValueError("Incomplete cell-supply window")
            v = np.interp(x, cell.x, cell.y)
            if not np.all(y > .8*v if high else y < .2*v):
                return False
    return True


def snm(vin, q, qb):
    """Largest axis-aligned square per lobe of piecewise-linear monotone VTCs.

    With v=y-x and u=y+x, a square's diagonal joins the two boundaries
    at constant v. Its side is |uA-uB|/2. Maxima occur at union breakpoints.
    """
    vin.valid("V", "V"); q.valid("V", "V"); qb.valid("V", "V")
    lo, hi = max(vin.x[0], q.x[0], qb.x[0]), min(vin.x[-1], q.x[-1], qb.x[-1])
    x = np.unique(np.r_[q.x, qb.x, vin.x])
    x = x[(x >= lo) & (x <= hi)]
    if not np.allclose(np.interp(x, vin.x, vin.y), x, atol=1e-8):
        raise ValueError("VIN does not match voltage sweep")
    a, b = np.interp(x, q.x, q.y), np.interp(x, qb.x, qb.y)
    if any(np.max(np.diff(y)) > 1e-6 or y[0]-y[-1] < .3*(hi-lo) for y in (a,b)):
        raise ValueError("Invalid inverter transfer curve")
    va, ua = (a-x)[::-1], (a+x)[::-1]
    vb, ub = x-b, x+b
    low, high = max(va[0], vb[0]), min(va[-1], vb[-1])
    v = np.unique(np.r_[va, vb, low, high]); v = v[(v >= low) & (v <= high)]
    delta = np.interp(v, va, ua)-np.interp(v, vb, ub)
    roots = sorted([float(v[i]) for i in np.flatnonzero(abs(delta)<1e-12)] + [v[i]-delta[i]*(v[i+1]-v[i])/(delta[i+1]-delta[i]) for i in range(len(v)-1) if delta[i]*delta[i+1] < 0])
    roots = [r for i,r in enumerate(roots) if i==0 or r-roots[i-1]>1e-10]
    # Stable states are outer intersections, the metastable point divides lobes.
    if len(roots) != 3:
        raise ValueError(f"Expected three butterfly intersections, found {len(roots)}")
    lobes = []
    for left, right in zip(roots[:-1], roots[1:]):
        points = v[(v >= left) & (v <= right)]
        d = np.interp(points, va, ua)-np.interp(points, vb, ub)
        k = int(np.argmax(np.abs(d))); vv = points[k]
        u1, u2 = sorted((float(np.interp(vv, va, ua)), float(np.interp(vv, vb, ub))))
        side = (u2-u1)/2
        xx, yy = (u1-vv)/2, (u1+vv)/2
        lobes.append({"side_mv": side*1000, "square": [[xx,yy],[xx+side,yy],[xx+side,yy+side],[xx,yy+side],[xx,yy]]})
    return {"snm_mv": min(l["side_mv"] for l in lobes), "lobes": lobes,
            "curves": {"a": np.column_stack((x,a)).tolist(), "b": np.column_stack((b,x)).tolist()}}
