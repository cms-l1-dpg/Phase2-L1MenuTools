"""Write the online-to-offline scalings in the format of the P2GT emulator menus.

Run after `object_performance` has written the scalings of a version:

    p2gt_scalings --version V50nano_170pre6 --label "Annual Review 2026"

reads outputs/<version>/object_performance/scalings/<object>:<id>:<region>.yaml
and writes `l1tGTObject_scalings.py` (the `scalings` dict of the CMSSW menus in
L1Trigger/Configuration/python/Phase2GTMenus/SeedDefinitions/<menu>/), with the
objects renamed to their P2GT collections (L1nnPuppiTau -> CL2Taus, ...) and
the parameters rounded to two decimals.

With `--cmssw <CMSSW_BASE>/src` the file is written into the menu folders
directly (step1_2024 and v0p0_2026 by default, see `--menus`), after checking
that every scalings key the seeds of that menu use exists, and printing what
changes with respect to the file it replaces.
"""
import argparse
import json
import os
import re
import sys
from glob import glob
from typing import Optional

import numpy as np
import yaml

from menu_tools.utils.constants import P2GT_DECIMALS

# MenuTools object -> P2GT collection; other objects keep their MenuTools name
P2GT_NAMES = {
    "L1gmtMuon": "GMTSaPromptMuons",
    "L1gmtTkMuon": "GMTTkMuons",
    "L1puppiJetSC4": "CL2JetsSC4",
    "L1puppiJetSC8": "CL2JetsSC8",
    "L1tkElectron": "CL2Electrons",
    "L1tkPhoton": "CL2Photons",
    "L1nnPuppiTau": "CL2Taus",
    "L1puppiMET": "CL2EtSum",
    "L1puppiJetSC4sums": "CL2HtSum",
}

DEFAULT_MENUS = ["step1_2024", "v0p0_2026"]
MENU_DIR = "L1Trigger/Configuration/python/Phase2GTMenus/SeedDefinitions"
FNAME = "l1tGTObject_scalings.py"

# The trailing space of the first line matches the existing menu files
HEADER = (
    "### L1T Object threshold scalings \n"
    "### as derived by the Phase-2 L1 DPG Menu team\n"
    "### using the Phase-2 MenuTools: "
    "https://github.com/cms-l1-dpg/Phase2-L1MenuTools\n"
    "\n"
    "### Corresponds to version {provenance}\n"
    "### See the L1T Phase-2 Menu Twiki for more details: "
    "https://twiki.cern.ch/twiki/bin/viewauth/CMS/PhaseIIL1TriggerMenuTools"
    "#Phase_2_L1_Trigger_objects_based\n"
    "\n"
    "### NB Objects starting with L1 are not yet part of the Step1 Menu and thus "
    "no seeds implemented in the P2GT emulator\n"
    "\n"
)


def release_from_version(version: str) -> Optional[str]:
    """CMSSW release from a version name, e.g. V50nano_170pre6 -> CMSSW_17_0_0_pre6."""
    m = re.search(r"_(\d\d)(\d)pre(\d+)", version)
    if not m:
        return None
    return f"CMSSW_{m.group(1)}_{m.group(2)}_0_pre{m.group(3)}"


def provenance(version: str, label: Optional[str], release: Optional[str]) -> str:
    major = version.split("_")[0].replace("nano", "")
    config = f"the {label} config" if label else f"the MenuTools {version} outputs"
    text = f"{major} derived with {config}"
    if release:
        series = "_".join(release.removeprefix("CMSSW_").split("_")[:2]) + "_x"
        text += f" in the {series} release ({release})"
    return text


def read_scalings(
    scalings_dir: str, decimals: int = P2GT_DECIMALS
) -> tuple[dict, list[str]]:
    """Nested dict object -> id -> region -> {offset, slope}, and the skipped files.

    Files written by object_performance with a plot-name prefix (when a file for
    the object already existed) are skipped, as are names not of the form
    <object>:<id>:<region>.yaml.
    """
    scalings: dict = {}
    skipped = []
    for path in sorted(glob(os.path.join(scalings_dir, "*.yaml"))):
        parts = os.path.basename(path).removesuffix(".yaml").split(":")
        if len(parts) != 3 or "_" in parts[0]:
            skipped.append(os.path.basename(path))
            continue
        obj, obj_id, region = parts
        with open(path) as f:
            params = yaml.safe_load(f)
        key = P2GT_NAMES.get(obj, obj)
        scalings.setdefault(key, {}).setdefault(obj_id, {})[region] = {
            "offset": float(np.round(float(params["offset"]), decimals)),
            "slope": float(np.round(float(params["slope"]), decimals)),
        }
    return scalings, skipped


def render(scalings: dict, header: str) -> str:
    return (
        header + "scalings = " + json.dumps(scalings, indent=4, sort_keys=True) + "\n"
    )


def load_scalings_file(path: str) -> dict:
    namespace: dict = {}
    with open(path) as f:
        exec(f.read(), namespace)
    return namespace["scalings"]


def flatten(d: dict, prefix: tuple = ()) -> dict:
    out = {}
    for k, v in d.items():
        if isinstance(v, dict) and not {"offset", "slope"} <= set(v):
            out.update(flatten(v, prefix + (k,)))
        else:
            out[prefix + (k,)] = v
    return out


def describe_changes(old: dict, new: dict, top: int = 10) -> list[str]:
    fo, fn = flatten(old), flatten(new)
    lines = []
    removed = sorted(":".join(k) for k in set(fo) - set(fn))
    added = sorted(":".join(k) for k in set(fn) - set(fo))
    if removed:
        lines.append(f"  removed: {', '.join(removed)}")
    if added:
        lines.append(f"  added:   {', '.join(added)}")
    changed = []
    for k in sorted(set(fo) & set(fn)):
        if fo[k] != fn[k]:
            shift = max(
                abs(fn[k]["slope"] - fo[k]["slope"]) / max(abs(fo[k]["slope"]), 1e-9),
                abs(fn[k]["offset"] - fo[k]["offset"]) / 10.0,
            )
            changed.append((shift, k))
    lines.append(
        f"  changed: {len(changed)} of {len(set(fo) & set(fn))} common entries"
    )
    for _, k in sorted(changed, reverse=True)[:top]:
        o, n = fo[k], fn[k]
        lines.append(
            f"    {':'.join(k):34s} slope {o['slope']:6.2f} -> {n['slope']:6.2f}"
            f"   offset {o['offset']:8.2f} -> {n['offset']:8.2f}"
        )
    return lines


THRS_CALL = re.compile(
    r'get_object_thrs\(\s*[^,()]+,\s*"([A-Za-z0-9]+)"\s*(?:,\s*"([A-Za-z0-9]+)"\s*)?\)'
)


def keys_used_by_menu(menu_dir: str) -> set[tuple[str, str]]:
    """(object, id) of every get_object_thrs call in the seed files of a menu."""
    used = set()
    for path in glob(os.path.join(menu_dir, "*.py")):
        with open(path) as f:
            for obj, obj_id in THRS_CALL.findall(f.read()):
                used.add((obj, obj_id or "default"))
    return used


def missing_keys(scalings: dict, used: set[tuple[str, str]]) -> list[str]:
    return sorted(f"{o}:{i}" for o, i in used if i not in scalings.get(o, {}))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Write MenuTools scalings in the format of the P2GT emulator menus."
    )
    parser.add_argument("--version", required=True, help="e.g. V50nano_170pre6")
    parser.add_argument(
        "--scalings-dir",
        help="default: outputs/<version>/object_performance/scalings",
    )
    parser.add_argument("--label", help='e.g. "Annual Review 2026", for the header')
    parser.add_argument(
        "--release", help="CMSSW release for the header (default: from the version)"
    )
    parser.add_argument(
        "--decimals",
        type=int,
        default=P2GT_DECIMALS,
        help=f"default: {P2GT_DECIMALS}, as rate_table --truncated",
    )
    out = parser.add_argument_group("output")
    out.add_argument(
        "-o",
        "--output",
        action="append",
        help="file to write (repeatable; default: "
        f"outputs/<version>/object_performance/{FNAME}, unless --cmssw)",
    )
    out.add_argument(
        "--cmssw", help="CMSSW src directory: write into the menu folders there"
    )
    out.add_argument(
        "--menus",
        nargs="+",
        default=DEFAULT_MENUS,
        help=f"menu folders for --cmssw (default: {' '.join(DEFAULT_MENUS)})",
    )
    out.add_argument("--compare", help="also show the changes w.r.t. this file")
    out.add_argument(
        "--dry-run", action="store_true", help="only show checks and changes"
    )
    out.add_argument(
        "--force", action="store_true", help="write even if menu keys are missing"
    )
    args = parser.parse_args()

    scalings_dir = args.scalings_dir or os.path.join(
        "outputs", args.version, "object_performance", "scalings"
    )
    scalings, skipped = read_scalings(scalings_dir, args.decimals)
    if not scalings:
        sys.exit(f"No scalings found in {scalings_dir}")
    n_entries = len(flatten(scalings))
    print(f"Read {n_entries} scalings for {len(scalings)} objects from {scalings_dir}")
    if skipped:
        print(f"Skipped {len(skipped)} file(s): {', '.join(skipped)}")
    release = args.release or release_from_version(args.version)
    text = render(
        scalings,
        HEADER.format(provenance=provenance(args.version, args.label, release)),
    )

    if args.compare:
        print(f"Changes w.r.t. {args.compare}:")
        print("\n".join(describe_changes(load_scalings_file(args.compare), scalings)))

    targets = list(args.output or [])
    problems = []
    if args.cmssw:
        for menu in args.menus:
            menu_dir = os.path.join(args.cmssw, MENU_DIR, menu)
            if not os.path.isdir(menu_dir):
                sys.exit(f"No menu folder {menu_dir}")
            path = os.path.join(menu_dir, FNAME)
            missing = missing_keys(scalings, keys_used_by_menu(menu_dir))
            if missing:
                problems.append(f"{menu}: no scalings for {', '.join(missing)}")
            if os.path.exists(path):
                print(f"Changes for {menu}:")
                print("\n".join(describe_changes(load_scalings_file(path), scalings)))
            targets.append(path)
    elif not targets:
        targets = [os.path.join("outputs", args.version, "object_performance", FNAME)]

    for p in problems:
        print(f"ERROR: {p}")
    if args.dry_run:
        return
    if problems and not args.force:
        sys.exit(
            "Not writing: the menus use scalings that are missing (or use --force)"
        )
    for path in targets:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w") as f:
            f.write(text)
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
