"""HLT ParT tau tag (TauvsAll on HLT AK4 PUPPI jets): working points, path emulation, rates.

Needs a p2nano v2 cache (default V50nano_170pre6HLTv2) with the slim ParT candidates
`hltAK4PuppiJetParT` (menu_tools/caching/make_hlt_jets_part.py), the L1 and HLT bit records,
and GenVisTau for the signal samples.

Di-tau path emulation, as HLT_DoubleMediumPFPuppiParTTauh30_eta2p1 (TauTagFilter
hltDoublePFJets30ParTTauhTagMediumWPL2DoubleTau): L1_pDoublePuppiTau52_52 AND >= 2
UNcorrected hltAK4PuppiJet with pT > T, |eta| < 2.1 and ParT TauvsAll > cut (no dR between
the jets, no matching to the L1 taus). Per event the largest cut that still passes is the
second-highest TauvsAll among the jets above T (`s2`), so the rate at any cut is a count of
s2 > cut.

1. Validation: the emulation at the HLT cut (T = 30, TauvsAll > 0.11645) against the HLT bit,
   event by event, in every sample (the stored scores have a 10-bit mantissa).
2. Working points (minimum bias, 31,038 kHz / N_MB per event):
   ParT1kHz:   the smallest stored-score cut with <= floor(1 kHz / per-event rate) events at
               T = 30 GeV (the HLT path's pT cut), i.e. at most 64 of the 2M events;
   ParT1kHz35: the same at T = 35 GeV;
   ParTEff90 / ParTEff80: 90% / 80% per-jet efficiency for genuine HH tau_h (jets with pT > 20,
               |eta| < 2.1 matched within dR < 0.3 to a GenVisTau with pT > 20, |eta| < 2.1);
               minimum-bias jet fake rate (pT > 20, |eta| < 2.1) quoted.
   MediumParT is the HLT WP (0.11645).
3. Emulated bits HLT_EMU_DoubleParTTauh<T>_<WP> for every sample, written as the record
   <version>_<sample>_HLTEMU.parquet (path_efficiency reads HLT_EMU_* from it).
4. Rates and event counts (Garwood 68%) of the seed, the two HLT di-tau paths and the emulated
   ParT paths; HH / DY event efficiencies (2 GenVisTau with pT > 25 GeV, |eta| < 2.1); a
   repeated-collision check of the passing minimum-bias events (the same leading tagged jet
   in several events: minimum bias reuses pileup collisions).

Outputs: configs/V50nano/object_performance/part/{part_wps.csv,part_rates.csv,part_summary.json}.

    python3 scripts/part/part_wps.py [--version V50nano_170pre6HLTv2]
"""

import argparse
import json
import os

import awkward as ak
import numpy as np
import pandas as pd
from scipy.stats import chi2

from menu_tools.utils import constants

OBJ = "hltAK4PuppiJetParT"
SEED = "L1_pDoublePuppiTau52_52_final"
HLT_PART = "HLT_DoubleMediumPFPuppiParTTauh30_eta2p1"
HLT_DEEPTAU = "HLT_DoubleMediumDeepTauPFTauHPS35_eta2p1"
MEDIUM = 0.11645
SIGNALS = ["HHTo2B2Tau", "DYLL_M50", "TT"]
OUTDIR = os.path.join("configs", "V50nano", "object_performance", "part")


def garwood(n: int, cl: float = 0.68) -> tuple[float, float]:
    a = 1 - cl
    lo = 0.0 if n == 0 else chi2.ppf(a / 2, 2 * n) / 2
    hi = chi2.ppf(1 - a / 2, 2 * (n + 1)) / 2
    return float(lo), float(hi)


class Sample:
    def __init__(self, version: str, sample: str):
        self.version, self.sample = version, sample
        pat = os.path.join(constants.CACHE_DIR, version, f"{version}_{sample}_%s.parquet")
        self.pat = pat
        j = ak.from_parquet(pat % OBJ)
        self.pt = j[f"{OBJ}_pt"]
        self.eta = j[f"{OBJ}_eta"]
        self.phi = j[f"{OBJ}_phi"]
        self.score = j[f"{OBJ}_TauvsAll"]
        self.n = len(j)
        self.seed = ak.to_numpy(ak.from_parquet(pat % "L1", columns=[SEED])[SEED]).astype(bool)
        hlt = ak.from_parquet(pat % "HLT", columns=[HLT_PART, HLT_DEEPTAU])
        self.hlt_part = ak.to_numpy(hlt[HLT_PART]).astype(bool)
        self.hlt_deeptau = ak.to_numpy(hlt[HLT_DEEPTAU]).astype(bool)
        assert len(self.seed) == self.n == len(self.hlt_part), "records not row-aligned"

    def s2(self, thr: float) -> np.ndarray:
        """Second-highest TauvsAll of the jets with pT > thr, |eta| < 2.1 (-inf if < 2)."""
        s = self.score[(self.pt > thr) & (abs(self.eta) < 2.1)]
        s = ak.sort(s, axis=1, ascending=False)
        return ak.to_numpy(ak.fill_none(ak.pad_none(s, 2, axis=1)[:, 1], -np.inf))

    def gen_taus(self):
        g = ak.from_parquet(self.pat % "GenVisTau")
        return g["GenVisTau_pt"], g["GenVisTau_eta"], g["GenVisTau_phi"]


def matched_scores(s: Sample, min_pt: float = 20.0, dr: float = 0.3) -> np.ndarray:
    """TauvsAll of jets (pT > min_pt, |eta| < 2.1) matched to a GenVisTau (pT > 20, |eta| < 2.1)."""
    gpt, geta, gphi = s.gen_taus()
    gsel = (gpt > 20) & (abs(geta) < 2.1)
    geta, gphi = geta[gsel], gphi[gsel]
    jsel = (s.pt > min_pt) & (abs(s.eta) < 2.1)
    jets = ak.zip({"eta": s.eta[jsel], "phi": s.phi[jsel], "sc": s.score[jsel]})
    taus = ak.zip({"eta": geta, "phi": gphi})
    # per gen tau (axis 1), all jets (axis 2): the closest jet within dr
    g, j = ak.unzip(ak.cartesian([taus, jets], axis=1, nested=True))
    dphi = (j.phi - g.phi + np.pi) % (2 * np.pi) - np.pi
    d2 = (j.eta - g.eta) ** 2 + dphi**2
    best = ak.argmin(d2, axis=2, keepdims=True)
    d2b = ak.flatten(d2[best], axis=2)
    scb = ak.flatten(j.sc[best], axis=2)
    ok = ak.fill_none(d2b, 99.0) < dr * dr
    return ak.to_numpy(ak.flatten(ak.fill_none(scb, -99.0)[ok], axis=None))


def ditau_acceptance(s: Sample) -> np.ndarray:
    gpt, geta, _ = s.gen_taus()
    return ak.to_numpy(ak.sum((gpt > 25) & (abs(geta) < 2.1), axis=1) >= 2)


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--version", default="V50nano_170pre6HLTv2")
    p.add_argument("--target-khz", type=float, default=1.0)
    p.add_argument("--no-write-bits", action="store_true")
    args = p.parse_args()
    os.makedirs(OUTDIR, exist_ok=True)

    mb = Sample(args.version, "MinBias")
    per_ev = constants.RATE_NORM_FACTOR / mb.n  # kHz per minimum-bias event
    n_max = int(np.floor(args.target_khz / per_ev + 1e-9))
    print(f"MinBias: {mb.n} events, {per_ev * 1e3:.2f} Hz / event; 1 kHz = {n_max} events")

    wps = {"MediumParT": {"cut": MEDIUM, "thr": 30, "def": "HLT Medium WP"}}
    for thr, name in [(30, "ParT1kHz"), (35, "ParT1kHz35")]:
        s2 = mb.s2(thr)[mb.seed]
        srt = np.sort(s2[np.isfinite(s2)])[::-1]
        cut = float(srt[n_max]) if len(srt) > n_max else -1.0
        wps[name] = {
            "cut": cut,
            "thr": thr,
            "def": f"<= {n_max} MB events (seed AND >= 2 jets pT > {thr}, |eta| < 2.1)",
        }

    # efficiency WPs on genuine HH tau_h, minimum-bias jet fake rate
    hh = Sample(args.version, "HHTo2B2Tau")
    sc_tau = matched_scores(hh)
    mbj = ak.to_numpy(ak.flatten(mb.score[(mb.pt > 20) & (abs(mb.eta) < 2.1)]))
    for eff, name in [(0.9, "ParTEff90"), (0.8, "ParTEff80")]:
        cut = float(np.quantile(sc_tau, 1 - eff))
        wps[name] = {"cut": cut, "thr": 30, "def": f"{eff:.0%} per-jet eff. on HH tau_h"}
    rows = []
    for name, w in wps.items():
        rows.append(
            {
                "wp": name,
                "cut": w["cut"],
                "definition": w["def"],
                "hh_tau_jet_eff": float(np.mean(sc_tau > w["cut"])),
                "mb_jet_fake": float(np.mean(mbj > w["cut"])),
            }
        )
    wp_df = pd.DataFrame(rows)
    print(wp_df.to_string(index=False))
    wp_df.to_csv(os.path.join(OUTDIR, "part_wps.csv"), index=False, float_format="%.6g")

    # emulated paths
    paths = {
        "HLT_EMU_DoubleParTTauh30_Medium": (30, wps["MediumParT"]["cut"]),
        "HLT_EMU_DoubleParTTauh30_1kHz": (30, wps["ParT1kHz"]["cut"]),
        "HLT_EMU_DoubleParTTauh35_1kHz": (35, wps["ParT1kHz35"]["cut"]),
        "HLT_EMU_DoubleParTTauh30_Eff90": (30, wps["ParTEff90"]["cut"]),
        "HLT_EMU_DoubleParTTauh30_Eff80": (30, wps["ParTEff80"]["cut"]),
    }
    summary = {"n_minbias": mb.n, "khz_per_event": per_ev, "n_1khz": n_max, "wps": wps}
    rate_rows = []
    samples = {"MinBias": mb, "HHTo2B2Tau": hh}
    for sname in ["DYLL_M50", "TT"]:
        if os.path.exists(mb.pat.replace("MinBias", sname) % OBJ):
            samples[sname] = Sample(args.version, sname)
    for sname, s in samples.items():
        s2 = {t: s.s2(t) for t in (30, 35)}
        bits = {k: s.seed & (s2[t] > c) for k, (t, c) in paths.items()}
        # validation against the HLT bit
        emu, hltb = bits["HLT_EMU_DoubleParTTauh30_Medium"], s.hlt_part
        val = {
            "n_hlt": int(hltb.sum()),
            "n_emu": int(emu.sum()),
            "both": int((hltb & emu).sum()),
            "hlt_only": int((hltb & ~emu).sum()),
            "emu_only": int((~hltb & emu).sum()),
        }
        print(f"{sname}: ParT path {HLT_PART} vs emulation: {val}")
        summary.setdefault("validation", {})[sname] = val
        if not args.no_write_bits:
            out = s.pat % "HLTEMU"
            ak.to_parquet(ak.zip({k: v for k, v in bits.items()}), out + ".tmp")
            os.replace(out + ".tmp", out)
            print(f"wrote {out}")
        allbits = {"L1 " + SEED: s.seed, HLT_DEEPTAU: s.hlt_deeptau, HLT_PART: s.hlt_part}
        allbits.update(bits)
        acc = ditau_acceptance(s) if sname in SIGNALS and sname != "TT" else None
        for k, b in allbits.items():
            n = int(b.sum())
            r = {"sample": sname, "bit": k, "events": n, "of": len(b)}
            if sname == "MinBias":
                lo, hi = garwood(n)
                r.update(
                    rate_khz=n * per_ev, rate_lo_khz=lo * per_ev, rate_hi_khz=hi * per_ev
                )
            if acc is not None:
                r.update(
                    acc_events=int(acc.sum()),
                    acc_pass=int((b & acc).sum()),
                    eff_acc=float((b & acc).sum() / max(acc.sum(), 1)),
                )
            rate_rows.append(r)
        if sname == "MinBias":
            # repeated pileup collisions: identical leading passing jet in several events
            ev = np.flatnonzero(bits["HLT_EMU_DoubleParTTauh30_1kHz"])
            sel = (mb.pt > 30) & (abs(mb.eta) < 2.1) & (mb.score > wps["ParT1kHz"]["cut"])
            lead = ak.firsts(ak.zip({"pt": mb.pt[sel], "eta": mb.eta[sel], "phi": mb.phi[sel]})[ev])
            key = [
                (round(float(a), 1), round(float(b), 2), round(float(c), 2))
                for a, b, c in zip(lead.pt, lead.eta, lead.phi)
            ]
            n_dist = len(set(key))
            summary["mb_1khz_distinct_leading_jets"] = {"events": len(ev), "distinct": n_dist}
            print(f"ParT1kHz MB events {len(ev)}: {n_dist} distinct leading tagged jets")
    rdf = pd.DataFrame(rate_rows)
    print(rdf.to_string(index=False))
    rdf.to_csv(os.path.join(OUTDIR, "part_rates.csv"), index=False, float_format="%.5g")
    with open(os.path.join(OUTDIR, "part_summary.json"), "w") as f:
        json.dump(summary, f, indent=1, default=float)


if __name__ == "__main__":
    main()
