"""Generate the DY (DYLL_M50) copies of the tau performance configs.

    python3 scripts/make_dy_tau_configs.py configs/V50nano/object_performance

The DY copies keep the objects and the gen selection of the HH / VBF configs; they change
the sample, the plot names (+ "_DY"), the pT binning (soft DY taus), drop the scalings and
L1hpsTau (not in the V50nano_170pre6HLT caches) and cut the split_by summary_range at 100 GeV.
"""
import os
import sys

import yaml

D = sys.argv[1]

HLT = [
    "hlt_tau_matching",
    "hlt_tau_trigger",
    "hlt_tau_trigger_wMatching",
    "hlt_tau_eta",
    "hlt_tau_l1seed",
    "hlt_tau_resolution",
]
L1 = ["tau_matching", "tau_trigger", "tau_trigger_wMatching"]
FILES = [f + s for f in HLT + L1 for s in ("", "_dm")] + ["path_eff_taus_compare"]

PT_BINNING = {"min": 0, "max": 100, "step": 4}
RES_PT_EDGES = [20, 25, 30, 35, 40, 50, 60, 80, 100]


class NoAlias(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True


def _flow_list(dumper, data):
    return dumper.represent_sequence("tag:yaml.org,2002:seq", data, flow_style=True)


NoAlias.add_representer(list, _flow_list)


def dy_name(name: str) -> str:
    if name.endswith("_DM"):
        return name[: -len("_DM")] + "_DY_DM"
    return name + "_DY"


def is_pt_turnon(cfg):
    return cfg["reference_object"]["x_arg"] == "pt" and "binning" in cfg


def transform(cfg, fname):
    cfg = dict(cfg)
    cfg["sample"] = "DYLL_M50"
    cfg.pop("scalings", None)
    # L1hpsTau is not in the V50nano_170pre6HLT caches
    for key in ("test_objects",):
        if key in cfg:
            cfg[key] = {
                k: v for k, v in cfg[key].items() if not k.startswith("L1hpsTau:")
            }
    if "resolution" in cfg:
        cfg["resolution"]["vs"]["pt"] = {"edges": RES_PT_EDGES}
    elif fname == "path_eff_taus_compare":
        pass  # handled per plot below
    elif is_pt_turnon(cfg):
        cfg["binning"] = dict(PT_BINNING)
    split = cfg.get("split_by")
    if split and "summary_range" in split and fname != "path_eff_taus_compare":
        split["summary_range"] = [split["summary_range"][0], 100]
    return cfg


PATH_EFF = {
    "DoubleTauPathsVsSubleadPt": {
        "binning": {"edges": [0, 10, 15, 20, 25, 30, 35, 40, 45, 50, 60, 80, 100]},
        "plateau_min": 45,
        "summary_range": [45, 100],
    },
    "DoubleTauPathsVsLeadPt": {
        "binning": {"edges": [0, 20, 25, 30, 35, 40, 45, 50, 60, 80, 100, 150]},
    },
}


HEADER = {
    "turnon": """# DY copy of {src} (DYLL_M50, run with --version V50nano_170pre6HLT): the same plots,
# objects and gen selection as {src} ({sample}), plot names + "_DY", no scalings (the
# scalings stay from {sample}).
# Finer low-pT binning (0-100 GeV in 4 GeV; resolution vs pT 20-100 GeV): DY visible taus
# are soft (200k events, |eta| < 2.1: 27k visible taus with pT > 20 GeV, 4.9k with pT > 40
# GeV, 0.76k above 60 GeV), so the plateau above ~60 GeV is statistics-limited. The
# single-tau efficiencies (matching, turn-ons, resolution) are the main DY result.
# The decay-mode summary_range (fractions JSON, _dm files) is the {sample} one cut at 100 GeV.{extra}
# Generated from {src} (scripts/make_dy_tau_configs.py); keep in sync.
#
# Header of {src}:
""",
}

EXTRA = {
    "hlt_": """
# hltHpsPFTau is stored only in events in which an L1 tau seed fired: in DY (soft taus,
# rarely two above the L1 double-tau thresholds) far fewer events have HLT taus than in HH,
# so the HLT matching and matching + trigger efficiencies are much lower than in HH. The
# trigger efficiency given the match (hlt_tau_trigger) is the object-level comparison.""",
    "tau_": """
# L1 taus only: L1hpsTau is dropped (not in the V50nano_170pre6HLT caches).""",
}

PATH_HEADER = (
    "# DY copy of path_eff_taus_compare.yaml (DYLL_M50, run with --version "
    "V50nano_170pre6HLT): the same\n# di-tau path comparison (L1 seed "
    "L1_pDoublePuppiTau52_52, DeepTau HPS35, ParT Tauh30), the same gen\n# selection "
    'and decay-mode pairs, plot names + "_DY". The legend rates are the minimum-bias '
    "rates of\n# the bits (as in the HH config).\n"
    "# STATISTICS-LIMITED: DY visible taus are soft. Of the 200k DY events, 11.1k have "
    "two visible taus\n# in |eta| < 2.1, but only 1.4k have a subleading tau with "
    "pT > 30 GeV, 79 with pT > 45 GeV, 27 with\n# pT > 60 GeV and 7 with pT > 80 GeV "
    "(HH: 4.2k / 2.1k / 0.9k of 17.7k). The L1 seed (52 GeV\n# offline, ~38 / 30 GeV "
    "online per leg) is on its plateau only above ~60-80 GeV, so the DY path\n# "
    "efficiencies are turn-on dominated: finer low-pT binning (subleading pT 0-100 GeV), "
    "plateau entry\n# for subleading pT > 45 GeV (~80 events; HH: > 80 GeV); the "
    "|eta| and pileup plots keep the HH\n# selection (subleading pT > 60 GeV) and have "
    "only ~27 events.\n# Generated from path_eff_taus_compare.yaml "
    "(scripts/make_dy_tau_configs.py); keep in sync.\n#\n# Header of path_eff_taus_compare.yaml:\n"
)


def src_header(path):
    lines = []
    with open(path) as f:
        for line in f:
            if line.startswith("# DY (DYLL_M50) is not used"):
                break  # superseded by this DY copy
            if line.startswith("#") or not line.strip():
                if line.strip():
                    lines.append(line if line.startswith("# ") else line)
                continue
            break
    return "".join(
        "#   " + line[1:].lstrip() if line.startswith("#") else line for line in lines
    )


for f in FILES:
    src = os.path.join(D, f + ".yaml")
    with open(src) as fh:
        cfgs = yaml.safe_load(fh)
    out = {}
    samples = set()
    for name, cfg in cfgs.items():
        samples.add(cfg["sample"])
        new = transform(cfg, f)
        if f == "path_eff_taus_compare":
            p = PATH_EFF.get(name, {})
            if "binning" in p:
                new["binning"] = p["binning"]
            if "plateau_min" in p:
                new["path_efficiency"]["plateau_min"] = p["plateau_min"]
            if "summary_range" in p:
                new["split_by"]["summary_range"] = p["summary_range"]
        out[dy_name(name)] = new
    (sample,) = samples
    if f == "path_eff_taus_compare":
        header = PATH_HEADER
    else:
        extra = EXTRA["tau_"] if f.startswith("tau_") else EXTRA["hlt_"]
        header = HEADER["turnon"].format(src=f + ".yaml", sample=sample, extra=extra)
    header += src_header(src)
    body = "\n".join(
        yaml.dump(
            {k: v},
            Dumper=NoAlias,
            sort_keys=False,
            default_flow_style=False,
            width=200,
            allow_unicode=True,
        )
        for k, v in out.items()
    )
    dst = (
        os.path.join(D, f + "_DY.yaml")
        if not f.endswith("_dm")
        else os.path.join(D, f[: -len("_dm")] + "_DY_dm.yaml")
    )
    with open(dst, "w") as fh:
        fh.write(header + "\n" + body)
    print(dst, list(out))
