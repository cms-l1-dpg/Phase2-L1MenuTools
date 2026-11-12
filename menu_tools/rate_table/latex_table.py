"""Turn a rate_table CSV into the LaTeX menu table used for the annual reviews.

Two inputs are combined:

* the menu config (``*_menu_cfg.yml``), from which thresholds and the
  "additional requirements" are derived automatically, and
* a per-menu *layout* file (``*_table_layout.yml``), which holds the things
  that genuinely need a human: section order, pretty seed labels, object
  plateaus and any hand-written overrides.

The layout is written once per menu (``rate_table_tex <config> --init`` makes
a skeleton), after which every new CSV for that menu can be turned into a
table with ``rate_table_tex <config>``.

Layout format::

    title: 'Step 1.5 menu, V50nano'
    pu_columns:                      # one rate column per entry, left to right;
      # CSV from outputs/<version>_140PU/rate_tables:
      - {pu: 140, version_suffix: '_140PU'}
      - {pu: 200, version_suffix: ''}         # the --version itself
    total_rate_margin: 0.3          # adds a "Total (+30%)" line; omit/null for none
    rate_decimals: 0
    columns: [seed, thresholds, rate, requirements]   # add `plateau` to show it
    objects:                         # per-object defaults, keyed by nano name
      L1gmtTkMuon: {plateau: '95', max_eta: 2.4}
    footnotes: ['(**) seed not in the TDR menu']
    sections:
      - name: 'Muon seeds'
        seeds:
          L1_SingleTkMu:
            label: 'Single TkMuon'
            # optional per-seed keys:
            # thresholds: '22'              replaces the derived thresholds
            # requirements: '$|\\eta|<2.4$'  replaces the derived requirements
            # extra_requirements: 'VLoose'  appended to the derived requirements
            # plateau: '95'                 replaces the per-object plateaus
            # online_rate: 12               for the `online_rate` column

Seeds that are in the CSV but not in the layout are not dropped: they are
appended in a separate section and a warning is printed. Seeds that are in
the layout but not in the menu are skipped with a warning, so one layout can
be shared between closely related menus.
"""
import argparse
import math
import os
import re
import shutil
import subprocess
import sys
import warnings
from typing import Optional, Sequence, cast

import pandas as pd
import yaml

from menu_tools.rate_table.menu_config import MenuConfig

# Carried over from the AR25 tables. These are object-level plateau
# efficiencies, not the scaling working points; re-check before publishing.
DEFAULT_OBJECTS: dict[str, dict] = {
    "L1gmtTkMuon": {"plateau": "95", "max_eta": 2.4},
    "L1gmtDispMuon": {"plateau": "99", "max_eta": 2.4},
    "L1tkElectron": {"plateau": "93"},
    "L1EG": {"plateau": "99"},
    "L1tkPhoton": {"plateau": "97"},
    "L1caloTau": {"plateau": "99"},
    "L1nnPuppiTau": {"plateau": "90", "requirement": r"NN score $>0.22$"},
    "L1puppiJetSC4": {"plateau": "100"},
    "L1puppiExtJetSC4": {"plateau": "100"},
    "L1puppiJetSC4NG": {"plateau": "100"},
    "L1puppiJetSC8": {"plateau": "100"},
    "L1puppiJetSC4sums": {"plateau": "100"},
    "L1puppiMET": {"plateau": "100"},
    "L1TrackTripletWord": {"plateau": "100"},
}

# Symbols used as subscripts for mass and dR requirements between legs
OBJECT_SYMBOLS = {
    "L1gmtTkMuon": r"\mu",
    "L1gmtDispMuon": r"\mu",
    "L1tkElectron": "e",
    "L1EG": "e",
    "L1tkPhoton": r"\gamma",
    "L1caloTau": r"\tau",
    "L1nnPuppiTau": r"\tau",
    "L1puppiJetSC4": "j",
    "L1puppiExtJetSC4": "j",
    "L1puppiJetSC4NG": "j",
    "L1puppiJetSC8": "J",
}

# Objects that only carry event-level information and never form a column entry
NON_PHYSICS_OBJECTS = {"L1PV"}

ONLINE_MARK = r"$^{\dagger}$"

PREAMBLE = r"""\documentclass{article}
\usepackage[a4paper,margin=0.4cm]{geometry}
\usepackage[utf8]{inputenc}
\usepackage{xcolor}
\usepackage{xspace}
\usepackage{adjustbox}
\usepackage{amsmath}
\usepackage{slashed}
\usepackage{multirow}
\usepackage{float}
\newcommand{\PT}{\ensuremath{p_{\mathrm{T}}}\xspace}
\newcommand{\pt}{\ensuremath{p_{\mathrm{T}}}\xspace}
\newcommand{\ET}{\ensuremath{E_{\mathrm{T}}}\xspace}
\newcommand{\HT}{\ensuremath{H_{\mathrm{T}}}\xspace}
\newcommand{\MHT}{\ensuremath{\slashed{H}_{\mathrm{T}}}\xspace}
\newcommand{\mT}{\ensuremath{m_{\mathrm{T}}}\xspace}
\newcommand{\ETm}{\ensuremath{E_{\mathrm{T}}^{\text{miss}}}\xspace}
\newcommand{\MET}{\ETm}
\newcommand{\ETmiss}{\ETm}
\newcommand{\ptmiss}{\ensuremath{\pt^\text{miss}}\xspace}
\newcommand{\Lone}{L1\xspace}
"""

# key -> (three header lines, column alignment)
COLUMNS: dict[str, tuple[tuple[str, str, str], str]] = {
    "seed": (("", "L1 Trigger seeds", ""), "l"),
    "name": (("", "Seed name", ""), "l"),
    "thresholds": (("Offline", "Threshold(s)", "[GeV]"), "c"),
    "rate": (("Rate", r"$\langle \mathrm{PU} \rangle = {pu}$", "[kHz]"), "c"),
    "online_rate": (("Online", "rate", "[kHz]"), "c"),
    "requirements": (("Additional", "Requirement(s)", "[cm, GeV]"), "c"),
    # Efficiency at which the object turn-on plateaus (from the turn-on curves)
    "plateau": (("Objects", "plateau", r"[\%]"), "c"),
}
DEFAULT_COLUMNS = ["seed", "thresholds", "rate", "requirements"]


def tex_escape(text: str) -> str:
    """Escape plain text (e.g. a seed name) for use outside math mode."""
    return re.sub(r"([_&%#$])", r"\\\1", text)


def _fmt_num(value: float) -> str:
    """12.0 -> '12', 2.172 -> '2.172'."""
    if float(value).is_integer():
        return str(int(value))
    return f"{value:g}"


###########################################################################
# Deriving thresholds and requirements from the menu config
###########################################################################

_THRESHOLD_RE = re.compile(
    r"^\s*(?:leg\d+\.)?(offline_pt|pt)\s*(>=|>)\s*(-?[\d.]+)\s*$"
)


def parse_threshold(cut: Optional[str]) -> Optional[tuple[float, bool]]:
    """Parse a leg `threshold_cut`.

    Returns:
        (value, is_online) or None if the cut is not a plain pT threshold.
    """
    if cut is None:
        return None
    match = _THRESHOLD_RE.match(str(cut))
    if not match:
        return None
    return float(match.group(3)), match.group(1) == "pt"


def _object_max_eta(obj_key: str, version: str, objects_cfg: dict) -> Optional[float]:
    """Tightest |eta| bound implied by the object definition itself (ID cuts
    and eta-region suffix), or by `max_eta` in the layout's `objects` block."""
    bounds = []
    nano_name = obj_key.split(":")[0]
    if objects_cfg.get(nano_name, {}).get("max_eta") is not None:
        bounds.append(float(objects_cfg[nano_name]["max_eta"]))
    try:
        # Imported lazily: pulls in awkward, which `--init` and the tests do not need.
        from menu_tools.utils.objects import Object

        obj = Object(obj_key, version)
        for cut in (obj.cuts or {}).get("inclusive", []):
            for val in re.findall(r"abs\(\{eta\}\)\s*<\s*([\d.]+)", cut):
                bounds.append(float(val))
    except Exception as exc:  # object config missing, awkward missing, ...
        warnings.warn(f"Could not load object `{obj_key}` for eta cuts: {exc}")
    # |eta| < 7 is the framework's "no cut"
    bounds = [b for b in bounds if b < 7]
    return min(bounds) if bounds else None


# Each pattern maps a cross-mask fragment to a (kind, payload) item.
_LEG = r"leg(\d+)"
_NUM = r"(-?[\d.]+)"
_CROSS_PATTERNS = [
    ("eta", re.compile(rf"abs\(\s*{_LEG}\.eta\s*\)\s*<\s*{_NUM}")),
    ("dz", re.compile(rf"abs\(\s*{_LEG}\.z0\s*-\s*{_LEG}\.z0\s*\)\s*<\s*{_NUM}")),
    ("deta", re.compile(rf"abs\(\s*{_LEG}\.eta\s*-\s*{_LEG}\.eta\s*\)\s*<\s*{_NUM}")),
    ("dr_max", re.compile(rf"{_LEG}\.deltaR\(\s*{_LEG}\s*\)\s*<\s*{_NUM}")),
    ("dr_min", re.compile(rf"{_LEG}\.deltaR\(\s*{_LEG}\s*\)\s*>\s*{_NUM}")),
    (
        "mass_min",
        re.compile(rf"\(\s*((?:{_LEG}\s*\+\s*)+{_LEG})\s*\)\.mass\s*>\s*{_NUM}"),
    ),
    (
        "mass_max",
        re.compile(rf"\(\s*((?:{_LEG}\s*\+\s*)+{_LEG})\s*\)\.mass\s*<\s*{_NUM}"),
    ),
    ("os", re.compile(rf"{_LEG}\.charge\s*\*\s*{_LEG}\.charge\s*<\s*0(?:\.0*)?")),
    (
        "os3",
        re.compile(
            r"abs\(\s*leg\d+\.charge\s*\+\s*leg\d+\.charge\s*\+\s*leg\d+\.charge\s*"
            r"\)\s*==\s*1(?:\.0*)?"
        ),
    ),
    (
        "btag",
        re.compile(
            rf"\(\s*(?:{_LEG}\.btagscore\s*\+?\s*)+\)\s*>\s*{_NUM}", re.IGNORECASE
        ),
    ),
]


def _mask_items(mask: str) -> tuple[list[tuple], bool]:
    """Find all recognised conditions in one cross-mask string.

    Returns:
        items: list of (kind, value, legs) tuples
        fully_parsed: False if the mask contains something not understood
    """
    items = []
    leftover = mask
    for kind, pattern in _CROSS_PATTERNS:
        for match in pattern.finditer(mask):
            groups = match.groups()
            value = None
            legs: tuple = ()
            if kind == "eta":
                legs, value = (groups[0],), float(groups[1])
            elif kind in ("dz", "deta", "dr_max", "dr_min"):
                legs, value = (groups[0], groups[1]), float(groups[2])
            elif kind in ("mass_min", "mass_max"):
                legs, value = tuple(re.findall(r"leg(\d+)", groups[0])), float(
                    groups[-1]
                )
            elif kind == "btag":
                value = float(groups[-1])
            elif kind == "os":
                legs = (groups[0], groups[1])
            items.append((kind, value, legs))
            leftover = leftover.replace(match.group(0), "")
    # Anything but brackets, boolean operators and whitespace left -> not understood
    fully_parsed = re.sub(r"[()&|\s]", "", leftover) == ""
    return items, fully_parsed


def derive_seed(seed_def: dict, version: str, objects_cfg: dict) -> dict:
    """Derive the table ingredients for one seed from its menu definition."""
    legs = {k: v for k, v in seed_def.items() if re.match(r"leg\d+$", k)}
    cross_masks = seed_def.get("cross_masks") or []

    # --- thresholds, in leg order, skipping PV-like legs
    thresholds: list[str] = []
    has_online = False
    unparsed: list[str] = []
    physics_legs = []
    for leg_name, leg in legs.items():
        nano = leg["obj"].split(":")[0]
        if nano in NON_PHYSICS_OBJECTS:
            continue
        physics_legs.append(leg_name)
        parsed = parse_threshold(leg.get("threshold_cut"))
        if parsed is None:
            if leg.get("threshold_cut") is not None:
                unparsed.append(f"{leg_name}: {leg['threshold_cut']}")
            thresholds.append("--")
            continue
        value, online = parsed
        thresholds.append(_fmt_num(value) + (ONLINE_MARK if online else ""))
        has_online |= online

    # --- requirements from the cross masks
    per_leg_eta: dict[str, float] = {}
    items: list[tuple] = []
    for mask in cross_masks:
        mask_items, ok = _mask_items(str(mask))
        if not ok:
            unparsed.append(str(mask))
        if "|" in str(mask) and len(mask_items) > 1:
            # OR of conditions: keep them together, rendered as "a or b"
            items.append(("or", mask_items, ()))
            continue
        for item in mask_items:
            if item[0] == "eta":
                leg = f"leg{item[2][0]}"
                per_leg_eta[leg] = min(item[1], per_leg_eta.get(leg, math.inf))
            else:
                items.append(item)

    # Combine explicit eta cuts with those implied by the object definition
    for leg_name in physics_legs:
        obj_eta = _object_max_eta(legs[leg_name]["obj"], version, objects_cfg)
        if obj_eta is not None:
            per_leg_eta[leg_name] = min(obj_eta, per_leg_eta.get(leg_name, math.inf))

    requirements: list[str] = []
    eta_values = []
    for leg_name in physics_legs:
        if leg_name in per_leg_eta and per_leg_eta[leg_name] not in eta_values:
            eta_values.append(per_leg_eta[leg_name])
    requirements += [rf"$|\eta|<{_fmt_num(v)}$" for v in eta_values]
    leg_symbols = {
        leg_name[3:]: OBJECT_SYMBOLS.get(legs[leg_name]["obj"].split(":")[0], "")
        for leg_name in physics_legs
    }
    requirements += _render_items(items, leg_symbols)
    # Object-level requirements from the layout, e.g. an ID score cut
    for leg_name in physics_legs:
        extra = objects_cfg.get(legs[leg_name]["obj"].split(":")[0], {}).get(
            "requirement"
        )
        if extra and extra not in requirements:
            requirements.append(extra)

    # --- plateau: per-object values, deduplicated in leg order
    plateaus: list[str] = []
    for leg_name in physics_legs:
        nano = legs[leg_name]["obj"].split(":")[0]
        raw_value = objects_cfg.get(nano, {}).get("plateau")
        plateau = "?" if raw_value is None else str(raw_value)
        if plateau not in plateaus:
            plateaus.append(plateau)

    return {
        "thresholds": ",".join(thresholds),
        "requirements": ", ".join(requirements),
        "plateau": ",".join(plateaus),
        "has_online": has_online,
        "unparsed": unparsed,
        "objects": [legs[leg]["obj"] for leg in physics_legs],
    }


def _subscript(legs: tuple, leg_symbols: dict[str, str]) -> str:
    """'_{j\\mu}' for legs of different/multiple objects, '' if unknown."""
    symbols = [leg_symbols.get(leg, "") for leg in legs]
    if not all(symbols):
        return ""
    return "_{" + " ".join(symbols) + "}"


def _render_items(
    items: list[tuple], leg_symbols: Optional[dict[str, str]] = None
) -> list[str]:
    """Render parsed cross-mask items to LaTeX, merging duplicates."""
    leg_symbols = leg_symbols or {}
    out: list[str] = []

    def add(text: str) -> None:
        if text not in out:
            out.append(text)

    # Mass windows: pair min and max on the same set of legs
    mass: dict[tuple, dict[str, float]] = {}
    for kind, value, legs in items:
        if kind in ("mass_min", "mass_max"):
            mass.setdefault(tuple(legs), {})[kind] = value

    for kind, value, legs in items:
        if kind == "dz":
            add(rf"${{\Delta}}z<{_fmt_num(value)}$")
        elif kind == "deta":
            add(rf"${{\Delta}}\eta<{_fmt_num(value)}$")
        elif kind in ("dr_max", "dr_min"):
            if kind == "dr_min" and value <= 0:  # dR > 0 is only duplicate removal
                continue
            symbols = [leg_symbols.get(leg, "") for leg in legs]
            sub = _subscript(legs, leg_symbols) if len(set(symbols)) > 1 else ""
            op = "<" if kind == "dr_max" else ">"
            add(rf"${{\Delta}}R{sub}{op}{_fmt_num(value)}$")
        elif kind in ("mass_min", "mass_max"):
            window = mass[tuple(legs)]
            lo, hi = window.get("mass_min"), window.get("mass_max")
            m = "m" + _subscript(legs, leg_symbols)
            if lo is not None and hi is not None:
                add(rf"${_fmt_num(lo)}<{m}<{_fmt_num(hi)}$")
            elif lo is not None:
                add(rf"${m}>{_fmt_num(lo)}$")
            else:
                add(rf"${m}<{_fmt_num(cast(float, hi))}$")
        elif kind == "os":
            add(r"$q_1\times q_2<0$")
        elif kind == "os3":
            add(r"$|\sum q|=1$")
        elif kind == "btag":
            add(rf"Tot. b-tag score $>{_fmt_num(value)}$")
        elif kind == "or":
            add(" or ".join(_render_items(value, leg_symbols)))
    return out


###########################################################################
# Inputs
###########################################################################


def read_section_hints(menu_config_path: str) -> dict[str, str]:
    """Map each active seed to the column-0 comment directly above it.

    Menu configs are usually grouped as ``# Run 3 Pure Muons`` followed by
    seeds; YAML loses the comments, so we read the raw text. Commented-out
    YAML (``#   leg1:`` etc.) is ignored.
    """
    hints: dict[str, str] = {}
    current: Optional[str] = None
    with open(menu_config_path) as f:
        for line in f:
            if not line.strip():
                continue
            if line.startswith("#"):
                # "# # ### GTT" -> "GTT"; pure banners ("# ######") are ignored
                text = re.sub(r"^[#\s]+", "", line).strip()
                looks_like_yaml = re.match(r"^[\w\-]+\s*:", text) or text.startswith(
                    "-"
                )
                if (
                    text
                    and not looks_like_yaml
                    and not re.fullmatch(r"[#=\-*\s]*", text)
                ):
                    current = text
                continue
            key = re.match(r"^([A-Za-z0-9_]+)\s*:", line)
            if key:
                hints[key.group(1)] = current or "Unsorted seeds"
    return hints


def load_layout(path: str) -> dict:
    with open(path) as f:
        layout = yaml.safe_load(f) or {}
    layout.setdefault("sections", [])
    return layout


def default_layout_path(menu_config_path: str) -> str:
    """configs/V50nano/rate_table/step1p5_menu_cfg.yml
    -> configs/V50nano/rate_table/step1p5_table_layout.yml"""
    base = os.path.basename(menu_config_path)
    stem = re.sub(r"(_menu)?_cfg\.ya?ml$", "", base)
    return os.path.join(os.path.dirname(menu_config_path), f"{stem}_table_layout.yml")


def csv_path_for(config: MenuConfig) -> str:
    """Mirror of `MenuTable.save_table` naming."""
    return os.path.join(
        config.table_outdir,
        f"{config.table_fname}_{config.version}{config.scalings_suffix}"
        f"{config.sample_suffix}.csv",
    )


###########################################################################
# Rendering
###########################################################################


def _format_rate(rate: Optional[float], decimals: int) -> str:
    if rate is None or (isinstance(rate, float) and math.isnan(rate)):
        return "--"
    rounded = round(rate, decimals)
    if rounded == 0 and rate > 0:
        return "$<$" + ("1" if decimals == 0 else f"{10 ** -decimals:g}")
    return f"{rounded:.{decimals}f}"


def build_rows(
    menu: dict, layout: dict, rates: dict[int, dict[str, float]], version: str
) -> tuple[list[tuple[str, list[dict]]], bool]:
    """`rates` maps pile-up -> {seed: rate}, one entry per rate column."""
    """Resolve the layout against the menu and the CSV into render-ready rows."""
    objects_cfg = DEFAULT_OBJECTS | (layout.get("objects") or {})
    sections = []
    placed = set()
    any_online = False

    for section in layout["sections"]:
        rows = []
        for seed, entry in (section.get("seeds") or {}).items():
            entry = entry or {}
            if seed not in menu:
                print(
                    f"WARNING: `{seed}` is in the layout but not in the menu, skipping"
                )
                continue
            placed.add(seed)
            derived = derive_seed(menu[seed], version, objects_cfg)
            for problem in derived["unparsed"]:
                # threshold problems are reported as "legN: <cut>"
                key = "thresholds" if re.match(r"leg\d+: ", problem) else "requirements"
                if key not in entry:
                    print(
                        f"WARNING: {seed}: could not translate `{problem}`, set "
                        f"`{key}` by hand"
                    )
            requirements = entry.get("requirements", derived["requirements"])
            if entry.get("extra_requirements"):
                requirements = ", ".join(
                    x for x in (requirements, entry["extra_requirements"]) if x
                )
            thresholds = str(entry.get("thresholds", derived["thresholds"]))
            any_online |= ONLINE_MARK in thresholds
            for pu, pu_rates in rates.items():
                if pu_rates and seed not in pu_rates:
                    print(f"WARNING: `{seed}` not found in the PU {pu} CSV")
            rows.append(
                {
                    "seed": entry.get("label", tex_escape(seed)),
                    "name": r"\texttt{" + tex_escape(seed) + "}",
                    "thresholds": thresholds,
                    "rate": {pu: pu_rates.get(seed) for pu, pu_rates in rates.items()},
                    "online_rate": entry.get("online_rate", ""),
                    "requirements": requirements or "",
                    "plateau": str(entry.get("plateau", derived["plateau"])),
                    "unparsed": derived["unparsed"],
                }
            )
        if rows:
            sections.append((section["name"], rows))

    missing = [s for s in menu if s not in placed]
    if missing:
        print(
            f"WARNING: {len(missing)} seed(s) not in the layout, appended at the end: "
            f"{missing}"
        )
        rows = []
        for seed in missing:
            derived = derive_seed(menu[seed], version, objects_cfg)
            any_online |= derived["has_online"]
            rows.append(
                {
                    "seed": tex_escape(seed),
                    "name": r"\texttt{" + tex_escape(seed) + "}",
                    "thresholds": derived["thresholds"],
                    "rate": {pu: pu_rates.get(seed) for pu, pu_rates in rates.items()},
                    "online_rate": "",
                    "requirements": derived["requirements"],
                    "plateau": derived["plateau"],
                    "unparsed": derived["unparsed"],
                }
            )
        sections.append((r"\color{red}Seeds missing from the table layout", rows))

    return sections, any_online


def render_table(
    layout: dict,
    sections: list[tuple[str, list[dict]]],
    totals: dict[int, Optional[float]],
    any_online: bool,
    source_csvs: list[str],
    rate_is_efficiency: bool = False,
) -> str:
    """`totals` maps pile-up -> total menu rate; its keys (in order) define the
    rate sub-columns that the `rate` column expands into."""
    columns = layout.get("columns", DEFAULT_COLUMNS)
    unknown = [c for c in columns if c not in COLUMNS]
    if unknown:
        raise ValueError(f"Unknown column(s) {unknown}, choose from {list(COLUMNS)}")
    decimals = int(layout.get("rate_decimals", 0))
    pus = list(totals)

    # Physical columns: (key, pu) with pu set only for the rate sub-columns
    phys: list[tuple[str, Optional[int]]] = []
    for col in columns:
        if col == "rate":
            phys += [("rate", pu) for pu in pus]
        else:
            phys.append((col, None))
    ncol = len(phys)
    rate_idx = [i for i, (key, _) in enumerate(phys) if key == "rate"]

    header_override = layout.get("column_headers") or {}

    def header(col: str) -> list[str]:
        if col in header_override:
            return list(header_override[col]) + [""] * (3 - len(header_override[col]))
        if col == "rate" and rate_is_efficiency:
            return ["Efficiency", "", r"[\%]"]
        return list(COLUMNS[col][0])

    def pu_label(pu: int) -> str:
        return rf"$\langle \mathrm{{PU}} \rangle = {pu}$"

    # Header: one line per level; multiple rate columns share a spanning "Rate [kHz]"
    lines: list[list[str]] = [[], [], []]
    for col in columns:
        h = header(col)
        if col == "rate" and len(pus) > 1:
            title = "Efficiency [\\%]" if rate_is_efficiency else f"{h[0]} {h[2]}"
            lines[0].append(rf"\multicolumn{{{len(pus)}}}{{c|}}{{{title}}}")
            # span header lines 2-3 so the PU labels sit vertically centred
            lines[1] += [rf"\multirow{{2}}{{*}}{{{pu_label(pu)}}}" for pu in pus]
            lines[2] += [""] * len(pus)
        elif col == "rate":
            h[1] = h[1].replace("{pu}", str(pus[0])) if not rate_is_efficiency else h[1]
            for i in range(3):
                lines[i].append(h[i])
        else:
            for i in range(3):
                lines[i].append(h[i])

    out = []
    for csv in source_csvs:
        out.append(f"% Generated by `rate_table_tex` from {csv}")
    # [H] (float package) keeps the table under its title; the height cap
    # shrinks long menus onto one page.
    out.append(r"\begin{table}[" + str(layout.get("float_placement", "H")) + "]")
    out.append(r"\begin{adjustbox}{width=\textwidth, max totalheight=0.95\textheight}")
    out.append(r"{\scriptsize")
    out.append(
        r"\begin{tabular}{|" + "|".join(COLUMNS[key][1] for key, _ in phys) + "|}"
    )
    out.append(r"\hline")
    out.append(" & ".join(lines[0]) + r" \\")
    if len(pus) > 1:
        out.append(rf"\cline{{{rate_idx[0] + 1}-{rate_idx[-1] + 1}}}")
    out.append(" & ".join(lines[1]) + r" \\")
    out.append(" & ".join(lines[2]) + r" \\")
    out.append(r"\hline")

    for name, rows in sections:
        out.append(rf"\hline \multicolumn{{{ncol}}}{{|l|}}{{{name}}} \\")
        for row in rows:
            cells = []
            for key, pu in phys:
                if key == "rate":
                    value = row["rate"].get(pu)
                    if rate_is_efficiency and value is not None:
                        value = 100 * value
                    cells.append(_format_rate(value, decimals))
                else:
                    cells.append(str(row[key]))
            for problem in row["unparsed"]:
                out.append(f"% NOTE: not auto-translated: {problem}")
            out.append(r"\hline " + " & ".join(cells) + r" \\")
        out.append(r"\hline")

    def summary_row(label: str, values: dict[int, Optional[float]]) -> str:
        """Label spans the columns left of the rates; each total sits under its
        own rate column; columns to the right are left empty."""
        cells = []
        if rate_idx[0] > 0:
            cells.append(rf"\multicolumn{{{rate_idx[0]}}}{{|l|}}{{{label}}}")
        cells += [_format_rate(values.get(pu), decimals) for pu in pus]
        n_right = ncol - rate_idx[-1] - 1
        if n_right:
            cells.append(rf"\multicolumn{{{n_right}}}{{c|}}{{}}")
        return " & ".join(cells) + r" \\"

    if (
        rate_idx
        and not rate_is_efficiency
        and any(v is not None for v in totals.values())
    ):
        out.append(r"\hline")
        out.append(summary_row("Rate for above Trigger seeds", totals))
        out.append(r"\hline")
        margin = layout.get("total_rate_margin")  # off unless set
        if margin is not None:
            with_margin = {
                pu: (v * (1 + margin) if v is not None else None)
                for pu, v in totals.items()
            }
            label = rf"\bf Total \Lone Menu Rate (+{_fmt_num(100 * margin)}\%)"
            out.append(summary_row(label, with_margin))
            out.append(r"\hline")

    # Footnotes go inside the tabular (without borders) so they float with it
    notes = []
    if any_online:
        notes.append(
            ONLINE_MARK + " online (L1) threshold, no online-to-offline scaling applied"
        )
    notes += layout.get("footnotes") or []
    for note in notes:
        out.append(rf"\multicolumn{{{ncol}}}{{l}}{{{note}}} \\")

    out.append(r"\end{tabular}")
    out.append(r"}")
    out.append(r"\end{adjustbox}")
    out.append(r"\end{table}")
    return "\n".join(out) + "\n"


def render_document(title: str, table: str) -> str:
    return (
        PREAMBLE
        + "\n\\begin{document}\n\n"
        + f"\\subsection*{{{title}}}\n\n"
        + table
        + "\n\\end{document}\n"
    )


# TeX installations to fall back on when the pdflatex on PATH lacks packages
# (e.g. the minimal system TeX Live on lxplus has no adjustbox).
TEXLIVE_FALLBACK_DIRS = [
    "/cvmfs/cms.cern.ch/external/tex/texlive/2017/bin/x86_64-linux",
]
REQUIRED_STY = [
    f"{name}.sty"
    for name in re.findall(r"\\usepackage(?:\[[^]]*\])?\{([^}]+)\}", PREAMBLE)
]


def _missing_packages(pdflatex: str) -> Optional[list[str]]:
    """Packages from the preamble that this TeX installation lacks, using the
    kpsewhich next to the given pdflatex. None if that cannot be checked."""
    kpsewhich = os.path.join(os.path.dirname(pdflatex), "kpsewhich")
    if not os.path.exists(kpsewhich):
        return None
    result = subprocess.run([kpsewhich, *REQUIRED_STY], capture_output=True, text=True)
    found = {
        os.path.basename(line.strip())
        for line in result.stdout.splitlines()
        if line.strip()
    }
    return [sty for sty in REQUIRED_STY if sty not in found]


def find_pdflatex() -> Optional[str]:
    """pdflatex to use: $RATE_TABLE_TEX_PDFLATEX if set, else the one on PATH if it
    has all needed packages, else the first complete TEXLIVE_FALLBACK_DIRS install."""
    forced = os.environ.get("RATE_TABLE_TEX_PDFLATEX")
    if forced:
        return forced
    on_path = shutil.which("pdflatex")
    candidates = ([on_path] if on_path else []) + [
        os.path.join(d, "pdflatex")
        for d in TEXLIVE_FALLBACK_DIRS
        if os.path.exists(os.path.join(d, "pdflatex"))
    ]
    missing_on_path: Optional[list[str]] = None
    for candidate in candidates:
        missing = _missing_packages(candidate)
        if not missing:  # complete, or cannot be checked
            if candidate != on_path:
                print(
                    f"INFO: {on_path or 'no pdflatex on PATH'}"
                    + (
                        f" lacks {', '.join(missing_on_path)}"
                        if missing_on_path
                        else ""
                    )
                    + f"; using {candidate}"
                )
            return candidate
        if candidate == on_path:
            missing_on_path = missing
    if on_path:
        print(
            f"WARNING: {on_path} lacks {', '.join(missing_on_path or [])} and no "
            "complete TeX Live found; "
            "trying anyway (set RATE_TABLE_TEX_PDFLATEX to choose one)"
        )
    return on_path


def compile_tex(tex_path: str) -> Optional[str]:
    """Run pdflatex next to the .tex; returns the pdf path or None."""
    pdflatex = find_pdflatex()
    if pdflatex is None:
        print("WARNING: pdflatex not found, skipping compilation")
        return None
    outdir = os.path.dirname(os.path.abspath(tex_path))
    cmd = [
        pdflatex,
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-output-directory",
        outdir,
        os.path.abspath(tex_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    stem = os.path.splitext(os.path.abspath(tex_path))[0]
    for ext in (".aux", ".log") if result.returncode == 0 else (".aux",):
        if os.path.exists(stem + ext):
            os.remove(stem + ext)
    if result.returncode != 0:
        print(f"ERROR: pdflatex failed, see {stem}.log")
        print("\n".join(result.stdout.splitlines()[-20:]))
        return None
    return stem + ".pdf"


def _pdf_to_png_commands(pdf_path: str, png_path: str, dpi: int) -> list[list[str]]:
    """Candidate converters for the first page, in order of preference."""
    stem = os.path.splitext(png_path)[0]
    cmds = []
    if shutil.which("pdftoppm"):  # poppler
        cmds.append(
            [
                "pdftoppm",
                "-png",
                "-r",
                str(dpi),
                "-f",
                "1",
                "-l",
                "1",
                "-singlefile",
                pdf_path,
                stem,
            ]
        )
    if shutil.which("gs"):  # ghostscript
        cmds.append(
            [
                "gs",
                "-q",
                "-dSAFER",
                "-dBATCH",
                "-dNOPAUSE",
                "-sDEVICE=png16m",
                f"-r{dpi}",
                "-dFirstPage=1",
                "-dLastPage=1",
                "-dTextAlphaBits=4",
                "-dGraphicsAlphaBits=4",
                f"-sOutputFile={png_path}",
                pdf_path,
            ]
        )
    for magick in (
        "magick",
        "convert",
    ):  # ImageMagick (needs ghostscript for PDFs itself)
        if shutil.which(magick):
            cmds.append(
                [
                    magick,
                    "-density",
                    str(dpi),
                    f"{pdf_path}[0]",
                    "-background",
                    "white",
                    "-alpha",
                    "remove",
                    png_path,
                ]
            )
            break
    return cmds


def crop_png(png_path: str, margin: int = 20) -> bool:
    """Trim the white page around the table, keeping `margin` pixels. Needs Pillow."""
    try:
        from PIL import Image, ImageChops
    except ImportError:
        print("WARNING: Pillow not available, PNG left uncropped")
        return False
    with Image.open(png_path) as im:
        rgb = im.convert("RGB")
    bbox = ImageChops.difference(rgb, Image.new("RGB", rgb.size, "white")).getbbox()
    if bbox is None:  # blank page
        return False
    left, top, right, bottom = bbox
    box = (
        max(0, left - margin),
        max(0, top - margin),
        min(rgb.width, right + margin),
        min(rgb.height, bottom + margin),
    )
    rgb.crop(box).save(png_path)
    return True


def _pymupdf_to_png(pdf_path: str, png_path: str, dpi: int) -> bool:
    """Pure-Python fallback (pip install pymupdf).

    Used when no command-line converter works.
    """
    try:
        import pymupdf  # type: ignore[import-not-found]
    except ImportError:
        try:
            import fitz as pymupdf  # type: ignore[import-not-found] # PyMuPDF < 1.24
        except ImportError:
            return False
    with pymupdf.open(pdf_path) as doc:
        doc[0].get_pixmap(dpi=dpi).save(png_path)
    return True


def export_png(pdf_path: str, dpi: int = 200, crop: bool = True) -> Optional[str]:
    """Render the first page of the PDF to a PNG next to it.

    E.g. for web plot browsers. Tries pdftoppm, ghostscript, ImageMagick, then
    PyMuPDF; crops to the table with Pillow.
    """
    png_path = os.path.splitext(pdf_path)[0] + ".png"
    made = False
    for cmd in _pdf_to_png_commands(pdf_path, png_path, dpi):
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and os.path.exists(png_path):
            made = True
            break
        print(f"WARNING: {cmd[0]} failed to make a PNG: {result.stderr.strip()[:200]}")
    if not made:
        made = _pymupdf_to_png(pdf_path, png_path, dpi)
    if not made:
        print(
            "WARNING: no working PDF-to-PNG converter (pdftoppm, gs, ImageMagick or "
            "PyMuPDF), skipping PNG"
        )
        return None
    if crop:
        crop_png(png_path)
    return png_path


###########################################################################
# Skeleton layout
###########################################################################


def _yaml_str(text: str) -> str:
    """Single-quoted YAML scalar: backslashes stay literal, which is what we
    want for LaTeX."""
    return "'" + str(text).replace("'", "''") + "'"


def make_skeleton(
    menu: dict,
    menu_config_path: str,
    version: str,
    title: str,
    inherit: Optional[dict] = None,
) -> str:
    hints = read_section_hints(menu_config_path)
    inherited: dict[str, dict] = {}
    if inherit:
        for section in inherit.get("sections", []):
            for seed, entry in (section.get("seeds") or {}).items():
                inherited[seed] = {"section": section["name"], **(entry or {})}

    objects_cfg = DEFAULT_OBJECTS | ((inherit or {}).get("objects") or {})

    # Keep menu order, grouping by section (inherited section wins over hint)
    order: dict[str, list[str]] = {}
    for seed in menu:
        section = inherited.get(seed, {}).get("section") or hints.get(
            seed, "Unsorted seeds"
        )
        order.setdefault(section, []).append(seed)

    used_objects = []
    for seed_def in menu.values():
        for key, leg in seed_def.items():
            if re.match(r"leg\d+$", key):
                nano = leg["obj"].split(":")[0]
                if nano not in NON_PHYSICS_OBJECTS and nano not in used_objects:
                    used_objects.append(nano)

    lines = [
        f"# Table layout for {menu_config_path}",
        "# Generated by `rate_table_tex --init`; edit freely. Seeds only need a "
        "`label`;",
        "# thresholds, requirements and plateaus are derived from the menu config "
        "unless",
        "# overridden here (the derived values are shown in the comments).",
        f"title: {_yaml_str(title)}",
        "pu_columns:",
        "  - {pu: 140, version_suffix: '_140PU'}",
        "  - {pu: 200, version_suffix: ''}",
        'total_rate_margin: null  # e.g. 0.3 adds a "Total (+30%)" line',
        "rate_decimals: 0",
        "columns: [seed, thresholds, rate, requirements]  # add `plateau` to show "
        "object plateaus",
        "footnotes: []",
        "objects:",
    ]
    for nano in used_objects:
        cfg = objects_cfg.get(nano, {})
        fields = [f"plateau: {_yaml_str(cfg.get('plateau', '?'))}"]
        if cfg.get("max_eta") is not None:
            fields.append(f"max_eta: {cfg['max_eta']}")
        if cfg.get("requirement"):
            fields.append(f"requirement: {_yaml_str(cfg['requirement'])}")
        lines.append(f"  {nano}: {{{', '.join(fields)}}}")
    lines.append("sections:")
    for section, seeds in order.items():
        lines.append(f"  - name: {_yaml_str(section)}")
        lines.append("    seeds:")
        for seed in seeds:
            derived = derive_seed(menu[seed], version, objects_cfg)
            entry = {k: v for k, v in inherited.get(seed, {}).items() if k != "section"}
            lines.append(f"      {seed}:")
            lines.append(f"        # objects: {', '.join(derived['objects'])}")
            lines.append(
                f"        # derived thresholds: {derived['thresholds']}".rstrip()
            )
            lines.append(
                f"        # derived requirements: {derived['requirements'] or '(none)'}"
            )
            for problem in derived["unparsed"]:
                lines.append(f"        # NOT auto-translated: {problem}")
            lines.append(
                f"        label: {_yaml_str(entry.pop('label', tex_escape(seed)))}"
            )
            for key, value in entry.items():
                lines.append(f"        {key}: {_yaml_str(value)}")
    return "\n".join(lines) + "\n"


###########################################################################
# CLI
###########################################################################


def _extract_version(path: str) -> Optional[str]:
    """configs/V50nano/rate_table/x.yml -> V50nano (same logic as rate_table,
    duplicated to avoid importing the awkward/scipy stack from there)."""
    parts = os.path.normpath(path).split(os.sep)
    if "configs" in parts and parts.index("configs") + 1 < len(parts):
        return parts[parts.index("configs") + 1]
    return None


def _load_inputs(args) -> tuple[MenuConfig, dict, str]:
    with open(args.config_file) as f:
        cfg_dict = yaml.safe_load(f)
    config = MenuConfig(
        cfg_dict,
        # objects come from configs/<dir of the config>, even with --version
        config_version=_extract_version(args.config_file),
        override_version=args.version,
        override_scalings_version=getattr(args, "scalings", None),
        override_sample=getattr(args, "signal", None),
        truncated=getattr(args, "truncated", False),
    )
    with open(config.menu_config) as f:
        menu = yaml.safe_load(f)
    layout_path = (
        args.layout
        or cfg_dict.get("table_layout")
        or default_layout_path(config.menu_config)
    )
    return config, menu, layout_path


def cmd_init(args) -> None:
    config, menu, layout_path = _load_inputs(args)
    out = layout_path
    if os.path.exists(out) and not args.force:
        sys.exit(
            f"{out} exists, use --force to overwrite or --layout to write elsewhere"
        )
    inherit = load_layout(args.inherit) if args.inherit else None
    title = args.title or f"{config.table_fname} ({config.version})"
    with open(out, "w") as f:
        f.write(
            make_skeleton(
                menu,
                config.menu_config,
                config.config_version_for_objects,
                title,
                inherit,
            )
        )
    print(f"Wrote skeleton layout to {out}")


def resolve_rate_csvs(
    layout: dict, config: MenuConfig, main_csv: str, cli_rates: Optional[list[str]]
) -> list[tuple[int, str]]:
    """(pu, csv) for each rate column, left to right.

    `--rates PU=PATH` (repeatable) wins. Otherwise each entry of the layout's
    `pu_columns` names a `version_suffix`: the CSV is the one `rate_table` writes
    for `--version <version><version_suffix>`, e.g. 140 PU runs kept as
    `<version>_140PU` in outputs/<version>_140PU/rate_tables. An empty suffix is
    the main CSV. Extra CSVs that do not exist are skipped with a warning.
    """
    if cli_rates:
        pairs = []
        for item in cli_rates:
            pu, _, path = item.partition("=")
            if not path:
                sys.exit(f"--rates expects PU=PATH, got `{item}`")
            pairs.append((int(pu), path))
        return pairs

    spec = layout.get("pu_columns") or [
        {"pu": layout.get("pu", 200), "version_suffix": ""}
    ]
    pairs = []
    for entry in spec:
        if "csv_suffix" in entry:
            sys.exit(
                "pu_columns: `csv_suffix` was replaced by `version_suffix` "
                "(CSV taken from outputs/<version><version_suffix>/rate_tables)"
            )
        suffix = entry.get("version_suffix", "")
        if not suffix:
            pairs.append((int(entry["pu"]), main_csv))
            continue
        other = MenuConfig(
            config._config,
            config_version=config._config_version,
            override_version=config.version + suffix,
            override_scalings_version=config._override_scalings_version,
            override_sample=config._override_sample,
            truncated=config._truncated,
        )
        path = csv_path_for(other)
        if not os.path.exists(path):
            print(f"WARNING: no PU {entry['pu']} CSV at {path}, dropping that column")
            continue
        pairs.append((int(entry["pu"]), path))
    return pairs


def cmd_make(args) -> None:
    config, menu, layout_path = _load_inputs(args)
    if not os.path.exists(layout_path):
        sys.exit(
            f"No layout at {layout_path}; create one with `rate_table_tex "
            f"{args.config_file} --init`"
        )
    layout = load_layout(layout_path)

    csv_path = args.csv or csv_path_for(config)
    if args.no_rates:
        # Layout preview: rate columns from `pu_columns`, all left as "--"
        spec = layout.get("pu_columns") or [{"pu": layout.get("pu", 200)}]
        rate_csvs: Sequence[tuple[int, Optional[str]]] = [
            (int(entry["pu"]), None) for entry in spec
        ]
    else:
        rate_csvs = resolve_rate_csvs(layout, config, csv_path, args.rates)

    rates: dict[int, dict[str, float]] = {}
    totals: dict[int, Optional[float]] = {}
    rate_is_efficiency = False
    for pu, path in rate_csvs:
        if path is None:
            rates[pu], totals[pu] = {}, None
            continue
        df = pd.read_csv(path)
        rate_is_efficiency = "rate" not in df.columns
        pu_rates = dict(
            zip(df["seed"], df["efficiency" if rate_is_efficiency else "rate"])
        )
        totals[pu] = pu_rates.pop("Total", None)
        pu_rates.pop("Total Event Number", None)
        rates[pu] = pu_rates
        print(f"INFO: PU {pu} rates from {path}")

    sections, any_online = build_rows(
        menu, layout, rates, config.config_version_for_objects
    )
    table = render_table(
        layout,
        sections,
        totals,
        any_online,
        [path for _, path in rate_csvs if path],
        rate_is_efficiency,
    )
    title = layout.get("title", f"{config.table_fname} ({config.version})")

    tex_path = args.output or os.path.splitext(csv_path)[0] + ".tex"
    os.makedirs(os.path.dirname(os.path.abspath(tex_path)), exist_ok=True)
    with open(tex_path, "w") as f:
        f.write(render_document(title, table) if not args.body_only else table)
    print(f"Wrote {tex_path}")

    if (args.compile or args.png) and not args.body_only:
        pdf = compile_tex(tex_path)
        if pdf:
            print(f"Wrote {pdf}")
            if args.png:
                png = export_png(pdf, dpi=args.dpi, crop=not args.no_crop)
                if png:
                    print(f"Wrote {png}")


EXAMPLES = """examples (from the repository root):
  rate_table_tex configs/V50nano/rate_table/step1p5_cfg.yml \
--version V50nano_170pre5 --png
  rate_table_tex configs/V50nano/rate_table/v0p0_cfg.yml \
--no-rates --compile -o v0p0_check.tex
  rate_table_tex configs/V50nano/rate_table/v0p0_cfg.yml --init \\
      --inherit configs/V50nano/rate_table/step1p5_table_layout.yml
"""


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="rate_table_tex",
        description=__doc__.split("\n\n")[0],
        epilog=EXAMPLES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "config_file",
        help="rate_table config, e.g. configs/V50nano/rate_table/step1p5_cfg.yml",
    )
    parser.add_argument(
        "--version",
        help="outputs/<version>/rate_tables to read the CSVs from and write to "
        "(same as for rate_table)",
        default=None,
    )
    parser.add_argument(
        "--layout",
        help="table layout (default: `table_layout` in the config, "
        "else <menu>_table_layout.yml next to the menu config)",
    )

    out = parser.add_argument_group("output")
    out.add_argument(
        "--compile", action="store_true", help="also run pdflatex to make the .pdf"
    )
    out.add_argument(
        "--png",
        action="store_true",
        help="also write a cropped .png of the table next to the .pdf (implies "
        "--compile)",
    )
    out.add_argument(
        "--dpi", type=int, default=200, help="PNG resolution (default: 200)"
    )
    out.add_argument(
        "--no-crop", action="store_true", help="keep the full A4 page in the PNG"
    )
    out.add_argument(
        "-o", "--output", help="write the .tex here instead of next to the CSV"
    )
    out.add_argument(
        "--body-only",
        action="store_true",
        help="only write the table environment, for \\input into another document",
    )

    inp = parser.add_argument_group("inputs")
    inp.add_argument(
        "--rates",
        action="append",
        metavar="PU=PATH",
        help="rate column from an explicit CSV, repeatable, left to right "
        "(overrides `pu_columns` in the layout)",
    )
    inp.add_argument(
        "--csv",
        help="main (200 PU) CSV, instead of the one derived from the config and "
        "--version",
    )
    inp.add_argument(
        "--no-rates",
        action="store_true",
        help="render without any CSV (rates shown as --), e.g. to check a new layout",
    )
    inp.add_argument(
        "--scalings", help="same as for rate_table, to pick up the matching CSV"
    )
    inp.add_argument(
        "--signal", help="same as for rate_table, to pick up the matching CSV"
    )
    inp.add_argument(
        "--truncated",
        action="store_true",
        help="same as for rate_table, to pick up the matching CSV",
    )

    new = parser.add_argument_group("new menu")
    new.add_argument(
        "--init",
        action="store_true",
        help="write a skeleton layout for this menu (to --layout or the default path) "
        "and exit",
    )
    new.add_argument(
        "--inherit",
        help="with --init: copy labels, overrides and sections from another layout "
        "for seeds with the same name",
    )
    new.add_argument("--title", help="with --init: table title")
    new.add_argument(
        "--force", action="store_true", help="with --init: overwrite an existing layout"
    )

    args = parser.parse_args()
    if not args.init:
        stray = [f"--{n}" for n in ("inherit", "title", "force") if getattr(args, n)]
        if stray:
            parser.error(f"{', '.join(stray)} can only be used with --init")
        cmd_make(args)
    else:
        cmd_init(args)


if __name__ == "__main__":
    main()
