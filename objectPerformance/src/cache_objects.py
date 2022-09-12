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
            f"isolation_dr_{dR}": [] for dR in self._ref_part_iso_dR_vals
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
        """
        sel_fs = all_parts["Stat"] == 1
        for branch in all_parts:
            all_parts[branch] = all_parts[branch][sel_fs]
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
            self._ref_part_iso[f"isolation_dr_{dR_threshold}"] = ak.concatenate(  # noqa
                [self._ref_part_iso[f"isolation_dr_{dR_threshold}"], iso],
            )

    def _postprocess_branches(self, arr):
        if self._object.startswith("part"):
            ref_parts = self._filter_genpart_branches(arr.copy())
            fs_parts = self._filter_fspart_branches(arr.copy())
            self._compute_ref_part_isolation(fs_parts, ref_parts)
            arr = ref_parts
        return arr

    def _load_branches_from_ntuple(self, fname, arr, branches):
        with uproot.open(fname) as f:
            for branch in branches:
                branch_arr = f[self._tree][branch].arrays(library="ak")[branch]
                branch_key = branch.removeprefix("part")
                arr[branch_key] = ak.concatenate(
                    [arr[branch_key], branch_arr]
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
            new_array = self._load_branches_from_ntuple(
                fname, new_array, branches
            )
            new_array = self._postprocess_branches(new_array)

            # Concatenate array from "fname file" to all_arrays
            for branch in branches:
                branch_key = branch.removeprefix("part")
                all_arrays[branch_key] = ak.concatenate(
                    [all_arrays[branch_key], new_array[branch_key]]
                )
        bar.finish()

        if self._object.startswith("part"):
            all_arrays = {**all_arrays, **self._ref_part_iso}
        self._final_ak_array = ak.zip({**all_arrays})

    def _cache_file_exists(self):
        """
        Checks if there is parquet file in cache
        with the name 'version_sample_object.parquet'
        """
        cached_files = glob.glob(self.cache_out_path + "*")
        return self.cache_out_path + f"{self.parquet_fname}.parquet" in cached_files

    def _save_array_to_parquet(self):
        """
        Save
        """
        ak.to_parquet(
            self._final_ak_array,
            where=self.cache_out_path+f"{self.parquet_fname}.parquet"
        )

    def load(self):
        print(f"Process {self._object + self._part_type} object...")

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
        for sample, sample_cfg in samples.items():
            for tree, object_branches in sample_cfg["trees_branches"].items():
                if tree == "ntuple_path":
                    continue
                for obj, branches in object_branches.items():
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

