"""Build HLT PUPPI jet HT / MHT from the cached hltAK4PuppiJet collection.

Writes <cache>/<version>/<version>_<sample>_hltPuppiJetSums.parquet with the same layout
as the L1 jet sums (L1puppiJetSC4sums): per event a list of two entries,
    hltPuppiJetSums_pt      [HT, MHT]
    hltPuppiJetSums_phi     [0, MHT phi]
    hltPuppiJetSums_sumType [0, 1]
so the HLT sums can be selected exactly like the L1 ones, e.g. in an objects config
    hltPuppiJetSums:
      ids:
        HT:  {cuts: {inclusive: ["{sumType} == 0"]}}
        MHT: {cuts: {inclusive: ["{sumType} == 1"]}}
HT = scalar sum of jet pt, MHT = |vector sum of jet pT|, MHT phi = phi of minus that
sum, over hltAK4PuppiJet with pt > 30 GeV and |eta| < 2.4 (defaults, as in the Phase-2
HLT PFPuppiHT / PFPuppiMHT paths; the jet pt is the nano hltAK4PuppiJet_pt as stored).

The nano jets are uncorrected (~0.8 x gen pT), so this HT is ~0.77 x gen HT. The HLT HT
object is therefore the nano's hltPFPuppiHT (cached directly, one value per event,
objects config `hltPFPuppiHT:default`: corrected jets pT > 30, |eta| < 5, E_T sum);
the HT here is kept for comparison and MHT (no corrected MHT in the nano) is taken from
here. hltPFPuppiMET (type-1 PUPPI sumEt) is not cached.

Usage (after caching hltAK4PuppiJet, and after merge_chunks.py for chunked samples):
    python3 menu_tools/caching/make_hlt_sums.py --version V50nano_170pre6HLT \\
        --sample MinBias
"""

import argparse
import os

import awkward as ak
import numpy as np

from menu_tools.utils import constants

SRC = "hltAK4PuppiJet"
TARGET = "hltPuppiJetSums"


def make_sums(jets, pt_min=30.0, abs_eta_max=2.4):
    pt = jets[f"{SRC}_pt"]
    eta = jets[f"{SRC}_eta"]
    phi = jets[f"{SRC}_phi"]
    sel = (pt > pt_min) & (abs(eta) < abs_eta_max)
    pt, phi = pt[sel], phi[sel]
    ht = ak.to_numpy(ak.sum(pt, axis=-1)).astype(np.float32)
    px = ak.to_numpy(ak.sum(pt * np.cos(phi), axis=-1))
    py = ak.to_numpy(ak.sum(pt * np.sin(phi), axis=-1))
    mht = np.hypot(px, py).astype(np.float32)
    mhtphi = np.where(mht > 0, np.arctan2(-py, -px), 0.0).astype(np.float32)
    n = len(ht)
    counts = np.full(n, 2, dtype=np.int64)
    flat_pt = np.stack([ht, mht], axis=1).ravel()
    flat_phi = np.stack([np.zeros(n, np.float32), mhtphi], axis=1).ravel()
    flat_type = np.tile(np.array([0, 1], dtype=np.int64), n)
    return ak.unflatten(
        ak.zip(
            {
                f"{TARGET}_pt": flat_pt,
                f"{TARGET}_phi": flat_phi,
                f"{TARGET}_sumType": flat_type,
            }
        ),
        counts,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--version", required=True)
    parser.add_argument("--sample", required=True)
    parser.add_argument("--jet-pt", type=float, default=30.0)
    parser.add_argument("--jet-eta", type=float, default=2.4)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    pattern = os.path.join(
        constants.CACHE_DIR, args.version, f"{args.version}_{args.sample}_%s.parquet"
    )
    target = pattern % TARGET
    if os.path.exists(target) and not args.overwrite:
        print(f"{target} exists, skipping")
        return
    jets = ak.from_parquet(
        pattern % SRC, columns=[f"{SRC}_pt", f"{SRC}_eta", f"{SRC}_phi"]
    )
    sums = make_sums(jets, args.jet_pt, args.jet_eta)
    ak.to_parquet(sums, target + ".tmp")
    os.replace(target + ".tmp", target)
    print(f"Wrote {target}: {len(sums)} events")


if __name__ == "__main__":
    main()
