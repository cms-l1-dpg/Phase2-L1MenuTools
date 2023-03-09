#!/afs/cern.ch/user/d/dhundhau/public/miniconda3/envs/py310/bin/python
import argparse
import glob
import os

import awkward as ak
from progress.bar import IncrementalBar
import uproot
import vector
import yaml

from utils import get_pdg_id
from utils import get_branches
from utils import timer


vector.register_awkward()


class ObjectCacher():

    def __init__(self, version, sample, obj, tree, branches, cfg_file,
                 dryrun=False):
        self._version = version
        self._sample = sample
        self._cfg_file = cfg_file
        self._object = obj.split('_')[0]
        self._tree = tree
        self._final_ak_array = None
        self._ref_part_iso_dR_vals = [0.1, 0.15, 0.2, 0.3, 1.5]
        self._ref_part_iso = {
            f"dr_{dR}": [] for dR in self._ref_part_iso_dR_vals
        }
        try:
            self._part_type = obj.split('_')[1]
        except IndexError:
            self._part_type = ""
        self._dryrun = dryrun
        # Get Branches
        if not isinstance(branches, list):
            self._branches = get_branches(self._ntuple_path, tree, obj)
        else:
            self._branches = branches
        self.cache_out_path = f"cache/{version}/"
        os.makedirs(self.cache_out_path, exist_ok=True)

    @property
    def parquet_fname(self):
        """
        Returns the name of the output file
        that the object will produce.
        """
        fname = (
            self._version
            + '_' + self._sample
            + "_" + self._object
        )
        if self._part_type:
            fname += "_" + self._part_type
        return fname

    @property
    def _ntuple_path(self):
        """
        Load cfg file to extract path to ntuples.
        """
        local_ntuple_path = f"l1ntuples/{self._version}/{self._sample}/*.root"
        if glob.glob(local_ntuple_path):
            return local_ntuple_path

        with open(self._cfg_file, 'r') as f:
            cfg = yaml.safe_load(f)[self._version][self._sample]
        return cfg["ntuple_path"]

    def _p4_sum(self, array, axis=-1):
        """
        Inspired from:
        https://github.com/CoffeaTeam/coffea/blob/
        875d1d02f04cac381c5b5b754513408beeba5739/coffea/nanoevents/
        methods/vector.py#L568
        Get the total four-momentum from a collection of four-momenta.
        with_name="Momentum4D" allows to use array.pt, array.eta, etc
        """
        return ak.zip(
            {
                "px": ak.sum(array.px, axis=axis, keepdims=True),
                "py": ak.sum(array.py, axis=axis, keepdims=True),
                "pz": ak.sum(array.pz, axis=axis, keepdims=True),
                "E": ak.sum(array.E, axis=axis, keepdims=True),
            },
            with_name="Momentum4D",
            behavior=array.behavior
        )

    def _get_visible_taus(self, all_parts):
        """
        Create a collection of gen-level taus.
        Leptonic taus are discarded.
        Only the visible component (i.e. no neutrinos)
        of hadronically-decaying taus is considered.
        """
        sel_no_nu_e = abs(all_parts["Id"]) != 12
        sel_no_nu_mu = abs(all_parts["Id"]) != 14
        sel_no_nu_tau = abs(all_parts["Id"]) != 16
        sel = sel_no_nu_e & sel_no_nu_mu & sel_no_nu_tau

        for branch in all_parts:
            all_parts[branch] = all_parts[branch][sel]

        all_tau_p = all_parts.copy()
        all_tau_m = all_parts.copy()

        sel = all_tau_p['Parent'] == 15
        for branch in all_tau_p:
            all_tau_p[branch] = all_tau_p[branch][sel]

        sel = all_tau_m['Parent'] == -15
        for branch in all_tau_m:
            all_tau_m[branch] = all_tau_m[branch][sel]

        all_tau_m = ak.zip({k.lower(): all_tau_m[k] for k in all_tau_m.keys()})
        all_tau_m = ak.with_name(all_tau_m, "Momentum4D")

        all_tau_p = ak.zip({k.lower(): all_tau_p[k] for k in all_tau_p.keys()})
        all_tau_p = ak.with_name(all_tau_p, "Momentum4D")

        sel_ele = ak.any(abs(all_tau_p['id']) == 11, axis=-1)
        sel_mu = ak.any(abs(all_tau_p['id']) == 13, axis=-1)
        sel_lep = sel_ele | sel_mu
        all_tau_p = ak.mask(all_tau_p, sel_lep, valid_when=False)

        sel_ele = ak.any(abs(all_tau_m['id']) == 11, axis=-1)
        sel_mu = ak.any(abs(all_tau_m['id']) == 13, axis=-1)
        sel_lep = sel_ele | sel_mu
        all_tau_m = ak.mask(all_tau_m, sel_lep, valid_when=False)

        fs_tau_p = self._p4_sum(all_tau_p)
        fs_tau_m = self._p4_sum(all_tau_m)

        # Parent, Id and Stat are dummy branches, only needed
        # for technical consistency.
        final_taus = {
            'Pt': ak.concatenate([fs_tau_p.pt, fs_tau_m.pt], axis=-1),
            'Eta': ak.concatenate([fs_tau_p.eta, fs_tau_m.eta], axis=-1),
            'Phi': ak.concatenate([fs_tau_p.phi, fs_tau_m.phi], axis=-1),
            'E': ak.concatenate([fs_tau_p.E, fs_tau_m.E], axis=-1),
            'Parent': ak.concatenate([fs_tau_p.E, fs_tau_m.E], axis=-1),
            'Id': ak.concatenate([fs_tau_p.E, fs_tau_m.E], axis=-1),
            'Stat': ak.concatenate([fs_tau_p.E, fs_tau_m.E], axis=-1)
        }

        return final_taus

    def _filter_genpart_branches(self, all_arrays):
        """
        Filter genparticle branches by Id.
        """
        partId = abs(all_arrays["Id"])
        sel_id = (partId == get_pdg_id(self._part_type))
        for branch in all_arrays:
            all_arrays[branch] = all_arrays[branch][sel_id]
            all_arrays[branch] = ak.fill_none(all_arrays[branch], -999)

        return all_arrays

    def _filter_fspart_branches(self, all_parts):
        """
        Select all the final state particles.
        This collection is used only for dR matching
        and Isolation computations, but it's not saved.
        Neutrino final state particles are not considered.
        """
        sel_no_nu_e = abs(all_parts["Id"]) != 12
        sel_no_nu_mu = abs(all_parts["Id"]) != 14
        sel_no_nu_tau = abs(all_parts["Id"]) != 16
        sel_fs = all_parts["Stat"] == 1
        sel = sel_fs & sel_no_nu_e & sel_no_nu_mu & sel_no_nu_tau

        for branch in all_parts:
            all_parts[branch] = all_parts[branch][sel]

        return all_parts

    def _compute_ref_part_isolation(self, fs_parts, ref_parts):
        """
        Compute Isolation on selected gen-leptons
        that are matched to final state particles.
        """
        leptons = ak.zip({k.lower(): ref_parts[k] for k in ref_parts.keys()})
        fs_parts = ak.zip({k.lower(): fs_parts[k] for k in fs_parts.keys()})

        # Compute dR between leptons and final state particles
        full_set = {
            "leptons": ak.with_name(leptons, "Momentum4D"),
            "fs_parts": ak.with_name(fs_parts, "Momentum4D"),
        }
        combs = ak.cartesian(full_set, axis=-1, nested=True)
        lep, fs = ak.unzip(combs)
        dR = fs.deltaR(lep)

        # Compute Iso, reflecting definition in:
        # https://github.com/FHead/Phase2-L1MenuTools/blob/main/
        #   ObjectPerformances/V22Processing/source/HelperFunctions.cpp#L240
        # TODO: Make for loop over standard values of dR thresholds
        for dR_threshold in self._ref_part_iso_dR_vals:
            sel_dR = dR < dR_threshold
            pt = fs["pt"][sel_dR]
            iso = ak.sum(pt, axis=-1) / leptons["pt"] - 1
            self._ref_part_iso[f"dr_{dR_threshold}"] = ak.concatenate(
                [self._ref_part_iso[f"dr_{dR_threshold}"], iso],
            )

    def _postprocess_branches(self, arr):
        if self._object.startswith("part"):
            if "tau" in self._part_type:
                ref_parts = self._get_visible_taus(arr.copy())
            else:
                ref_parts = self._filter_genpart_branches(arr.copy())
            fs_parts = self._filter_fspart_branches(arr.copy())
            self._compute_ref_part_isolation(fs_parts, ref_parts)
            arr = ref_parts
        return arr

    def _load_branches_from_ntuple(self, chunk_array, arr, branches):
        for branch in branches:
            branch_arr = arr[branch]
            branch_key = branch.removeprefix("part")
            chunk_array[branch_key] = branch_arr
        return chunk_array

    def _ak_array_in_chunk(self, arr, chunk_array, branches):
        for branch in branches:
            branch_key = branch.removeprefix("part")
            arr[branch_key] = ak.concatenate(
                [arr[branch_key], chunk_array[branch_key]]
            )
        return arr

    @timer("Loading objects files")
    def _concat_array_from_ntuples(self):
        fnames = glob.glob(self._ntuple_path)[:]
        bar = IncrementalBar("Progress", max=len(fnames))

        branches = [self._object + x for x in self._branches]
        all_arrays = {x.removeprefix("part"): [] for x in branches}

        for fname in fnames:
            bar.next()
            new_array = {x.removeprefix("part"): [] for x in branches}

            # Read files in chunks to avoid issues with large size files
            chunk_name = f"{fname}:{self._tree}"
            for array in uproot.iterate(chunk_name, step_size=100):
                chunk_array = {x.removeprefix("part"): [] for x in branches}
                chunk_array = self._load_branches_from_ntuple(
                    chunk_array, array, branches
                )
                chunk_array = self._postprocess_branches(chunk_array)

                new_array = self._ak_array_in_chunk(
                    new_array, chunk_array, branches
                )

            # Concatenate array from "fname file" to all_arrays
            all_arrays = self._ak_array_in_chunk(
                all_arrays, new_array, branches
            )

        bar.finish()

        if self._object.startswith("part"):
            all_arrays = {**all_arrays, **self._ref_part_iso}
        if len(all_arrays) > 1:
            self._final_ak_array = ak.zip({**all_arrays})
        else:
            self._final_ak_array = ak.Array(all_arrays)

    def _cache_file_exists(self):
        """
        Checks if there is parquet file in cache
        with the name 'version_sample_object.parquet'
        """
        cached_files = glob.glob(self.cache_out_path + "*")
        fpath = self.cache_out_path + f"{self.parquet_fname}.parquet"
        return fpath in cached_files

    def _save_array_to_parquet(self):
        """
        Save
        """
        ak.to_parquet(
            self._final_ak_array,
            where=self.cache_out_path + f"{self.parquet_fname}.parquet"
        )

    def load(self):
        #print(f"Process {self._object + self._part_type} object...")

        if self._cache_file_exists():
            return

        print(
            f"Loading {self._object + self._part_type} object "
            f"with the following branches: {self._branches}"
        )

        if self._dryrun:
            return

        self._concat_array_from_ntuples()
        self._save_array_to_parquet()


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "cfg",
        default="cfg_caching/V22.yaml",
        help=""
    )
    parser.add_argument(
        "--dry-run",
        "-d",
        action="store_true",
        help="Only do print-out of objects and branches to be loaded."
    )
    args = parser.parse_args()

    with open(args.cfg, 'r') as f:
        cfg = yaml.safe_load(f)
    for version, samples in cfg.items():
        print("Processing: version", version)
        for sample, sample_cfg in samples.items():
            print("\tSample:", sample)
            for tree, object_branches in sample_cfg["trees_branches"].items():
                if tree == "ntuple_path":
                    continue
                for obj, branches in object_branches.items():
                    print("\t\tObject:", obj)
                    loader = ObjectCacher(
                        version=version,
                        sample=sample,
                        tree=tree,
                        obj=obj,
                        branches=branches,
                        cfg_file=args.cfg,
                        dryrun=args.dry_run
                    )
                    loader.load()


