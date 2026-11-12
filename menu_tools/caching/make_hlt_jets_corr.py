"""Apply the Phase-2 HLT jet energy corrections to the cached hltAK4PuppiJet.

The nano stores hltAK4PFPuppiJets, i.e. the HLT AK4 PUPPI jets *before* the jet energy
corrections, while the HLT paths cut on hltAK4PFPuppiJetsCorrected. The HLT
correction chain
(HLTrigger/Configuration/python/HLT_75e33/modules/hltAK4PFPuppiJetCorrector*_cfi.py)
is L1FastJet x L2Relative x L3Absolute with payload `AK4PFPuppiHLT`. In the global tag
of the production (auto:phase2_realistic_T35) L1FastJet and L3Absolute are the
constant 1 (so no rho is needed) and only L2Relative, a function of the raw jet
(pT, eta), is non-trivial. The payloads, dumped with
`cmsRun configs/V50nano/cache_objects/hlt_jec/dump_jec_cfg.py`, are in
configs/V50nano/cache_objects/hlt_jec/.

Writes, next to the input parquet,
  <version>_<sample>_hltAK4PuppiJetCorr.parquet
      the jets with all hltAK4PuppiJet fields (prefix hltAK4PuppiJetCorr_), pt and mass
      corrected, plus `rawPt` and `jecFactor`; sorted by corrected pt;
  <version>_<sample>_hltPuppiJetCorrSums.parquet
      hltPuppiJetCorrSums_{pt,phi,sumType} in the L1puppiJetSC4sums layout:
      sumType 0: HT  as hltPFPuppiHT  (HLT_PFPuppiHT1070): sum of corrected jet pT,
                 pT > 30 GeV, |eta| < 2.4;
      sumType 1: MHT as hltPFPuppiMHT (HLT_..._PFPuppiMHT140): |vector sum| of
                 corrected jet E_T, E_T > 30 GeV, |eta| < 5 (HLTHtMhtProducer with
                 usePt = False).

Checks (3 ttbar files, 3000 events): the scalar E_T sum of these jets (E_T > 30, |eta| <
5) reproduces the nano hltPFPuppiHT (= sumEt of hltPFPuppiMHT) within 0.5 GeV in 99.9%
of the events, and the emulated HT > 1070 and jet pT > 520 agree event by event with the
HLT_PFPuppiHT1070 and HLT_AK4PFPuppiJet520 bits.

Usage (after caching / merging hltAK4PuppiJet):
    python3 menu_tools/caching/make_hlt_jets_corr.py --version V50nano_170pre6HLT \\
        --sample TT
"""

import argparse
import os

import awkward as ak
import numpy as np

from menu_tools.utils import constants

SRC = "hltAK4PuppiJet"
TARGET = "hltAK4PuppiJetCorr"
SUMS = "hltPuppiJetCorrSums"
JEC_DIR = os.path.join("configs", "V50nano", "cache_objects", "hlt_jec")
JEC_L2 = "phase2_realistic_T35_L2Relative_AK4PFPuppiHLT.txt"


def load_jec_table(fname: str) -> np.ndarray:
    """Rows of a JetCorrectorParameters text file with one eta binning variable:
    etamin etamax npar ptmin ptmax p0 ... p5."""
    with open(fname) as f:
        header = f.readline()
        if "log10(x)" not in header:
            raise ValueError(f"{fname}: unexpected formula {header.strip()}")
        rows = [[float(x) for x in ln.split()] for ln in f if ln.strip()]
    return np.array(rows)


def l2relative(pt, eta, table: np.ndarray) -> np.ndarray:
    """L2Relative factor, formula
    max(0.0001, p0 + p1 / (log10(x)^2 + p2) + p3 * exp(-p4 * (log10(x) - p5)^2)),
    x = raw pT clamped to the bin's [ptmin, ptmax]; eta outside the table takes the edge
    bin.
    """
    pt = np.asarray(pt, dtype=np.float64)
    eta = np.asarray(eta, dtype=np.float64)
    i = np.clip(np.searchsorted(table[:, 0], eta, side="right") - 1, 0, len(table) - 1)
    p = table[i]
    lx = np.log10(np.clip(pt, p[:, 3], p[:, 4]))
    c = (
        p[:, 5]
        + p[:, 6] / (lx**2 + p[:, 7])
        + p[:, 8] * np.exp(-p[:, 9] * (lx - p[:, 10]) ** 2)
    )
    return np.maximum(1e-4, c)


def correct_jets(jets: ak.Array, table: np.ndarray) -> ak.Array:
    counts = ak.num(jets)
    flat = ak.flatten(jets)
    raw_pt = ak.to_numpy(flat[f"{SRC}_pt"]).astype(np.float64)
    fac = l2relative(raw_pt, ak.to_numpy(flat[f"{SRC}_eta"]), table)
    fields = {}
    for f in flat.fields:
        fields[f.replace(SRC + "_", TARGET + "_", 1)] = flat[f]
    fields[f"{TARGET}_pt"] = (raw_pt * fac).astype(np.float32)
    fields[f"{TARGET}_mass"] = (ak.to_numpy(flat[f"{SRC}_mass"]) * fac).astype(
        np.float32
    )
    fields[f"{TARGET}_rawPt"] = raw_pt.astype(np.float32)
    fields[f"{TARGET}_jecFactor"] = fac.astype(np.float32)
    out = ak.unflatten(ak.zip(fields), counts)
    order = ak.argsort(out[f"{TARGET}_pt"], axis=-1, ascending=False)
    return out[order]


def make_sums(cjets: ak.Array) -> ak.Array:
    pt = cjets[f"{TARGET}_pt"]
    eta = cjets[f"{TARGET}_eta"]
    phi = cjets[f"{TARGET}_phi"]
    mass = cjets[f"{TARGET}_mass"]
    # HT: pT sum, pT > 30, |eta| < 2.4 (hltPFPuppiHT, usePt = True)
    ht = ak.to_numpy(ak.sum(pt[(pt > 30) & (abs(eta) < 2.4)], axis=-1)).astype(
        np.float32
    )
    # MHT: E_T, E_T > 30, |eta| < 5 (hltPFPuppiMHT, usePt = False)
    p = pt * np.cosh(eta)
    et = np.sqrt(p**2 + mass**2) * pt / p
    sel = (et > 30) & (abs(eta) < 5)
    px = ak.to_numpy(ak.sum((et * np.cos(phi))[sel], axis=-1))
    py = ak.to_numpy(ak.sum((et * np.sin(phi))[sel], axis=-1))
    mht = np.hypot(px, py).astype(np.float32)
    mhtphi = np.where(mht > 0, np.arctan2(-py, -px), 0.0).astype(np.float32)
    n = len(ht)
    return ak.unflatten(
        ak.zip(
            {
                f"{SUMS}_pt": np.stack([ht, mht], axis=1).ravel(),
                f"{SUMS}_phi": np.stack(
                    [np.zeros(n, np.float32), mhtphi], axis=1
                ).ravel(),
                f"{SUMS}_sumType": np.tile(np.array([0, 1], dtype=np.int64), n),
            }
        ),
        np.full(n, 2, dtype=np.int64),
    )


def _write(arr, target):
    ak.to_parquet(arr, target + ".tmp")
    os.replace(target + ".tmp", target)
    print(f"Wrote {target}: {len(arr)} events")


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--version", required=True)
    parser.add_argument("--sample", required=True)
    parser.add_argument("--jec", default=os.path.join(JEC_DIR, JEC_L2))
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    pattern = os.path.join(
        constants.CACHE_DIR, args.version, f"{args.version}_{args.sample}_%s.parquet"
    )
    t_jets, t_sums = pattern % TARGET, pattern % SUMS
    if os.path.exists(t_jets) and os.path.exists(t_sums) and not args.overwrite:
        print(f"{t_jets} and {t_sums} exist, skipping")
        return
    cjets = correct_jets(ak.from_parquet(pattern % SRC), load_jec_table(args.jec))
    _write(cjets, t_jets)
    _write(make_sums(cjets), t_sums)


if __name__ == "__main__":
    main()
