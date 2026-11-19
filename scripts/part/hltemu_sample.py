"""HLTEMU record (emulated ParT di-tau paths, bits HLT_EMU_*) for one more sample, with the WPs of
configs/V50nano/object_performance/part/part_wps.csv unchanged (step 3 of part_wps.py, which covers
MinBias, HHTo2B2Tau, DYLL_M50 and TT). Prints the emulated Medium path against the HLT ParT bit.

    python3 scripts/part/hltemu_sample.py --sample HHTo4B [--version V50nano_170pre6HLTv2]
"""

import argparse
import os
import sys

import awkward as ak
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import part_wps as P  # noqa: E402


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--sample", required=True)
    p.add_argument("--version", default="V50nano_170pre6HLTv2")
    args = p.parse_args()
    wp = pd.read_csv(os.path.join(P.OUTDIR, "part_wps.csv")).set_index("wp")["cut"]
    paths = {
        "HLT_EMU_DoubleParTTauh30_Medium": (30, wp["MediumParT"]),
        "HLT_EMU_DoubleParTTauh30_1kHz": (30, wp["ParT1kHz"]),
        "HLT_EMU_DoubleParTTauh35_1kHz": (35, wp["ParT1kHz35"]),
        "HLT_EMU_DoubleParTTauh30_Eff90": (30, wp["ParTEff90"]),
        "HLT_EMU_DoubleParTTauh30_Eff80": (30, wp["ParTEff80"]),
    }
    s = P.Sample(args.version, args.sample)
    s2 = {t: s.s2(t) for t in (30, 35)}
    bits = {k: s.seed & (s2[t] > c) for k, (t, c) in paths.items()}
    emu, hlt = bits["HLT_EMU_DoubleParTTauh30_Medium"], s.hlt_part
    print(
        f"{args.sample}: {s.n} events; {P.HLT_PART} {int(hlt.sum())}, emulation {int(emu.sum())}, "
        f"HLT only {int((hlt & ~emu).sum())}, emulation only {int((~hlt & emu).sum())}"
    )
    for k, b in bits.items():
        print(f"  {k}: {int(b.sum())}")
    out = s.pat % "HLTEMU"
    ak.to_parquet(ak.zip(bits), out + ".tmp")
    os.replace(out + ".tmp", out)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
