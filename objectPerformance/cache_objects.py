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

    def __init__(self, version, sample, obj, tree, branches, dryrun=False):
        self._version = version
        self._sample = sample
        self._object = obj.split('_')[0]
        self._tree = tree
        if not isinstance(branches, list):
            self._branches = get_branches(sample_cfg["ntuple_path"], tree, obj)
        else:
            self._branches = branches
        self._ntuple_path = ""
        self._set_ntuple_path()
        self._final_ak_array = None
        try:
            self._part_type = obj.split('_')[1]
        except IndexError:
            self._part_type = ""
        self._dryrun = dryrun
        os.makedirs("cache", exist_ok=True)

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

    def _set_ntuple_path(self):
        """
        Load cfg file to extract path to ntuples.
        """
        with open("cfg_caching/V22.yaml", 'r') as f:
            cfg = yaml.safe_load(f)[self._version][self._sample]
        self._ntuple_path = cfg["ntuple_path"]

    def _filter_genpart_branches(self, all_arrays):
        """
        Filter genparticle branches. For leptons
        apply eta cut and choose largest pT object
        in each event.
        """
        if not self._object.startswith("part"):
            return all_arrays

        partId = abs(all_arrays["Id"])
        sel_id = (partId == get_pdg_id(self._part_type))
        for branch in all_arrays:
            all_arrays[branch] = all_arrays[branch][sel_id]

        sel_pt = ak.argmax(all_arrays["Pt"], axis=-1, keepdims=True)

        for branch in all_arrays:
            all_arrays[branch] = all_arrays[branch][sel_pt]
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
            all_parts[branch] = ak.fill_none(all_parts[branch], -999)

        return all_parts

    def _filter_iso_branches(self, all_parts, all_arrays):
        """
        Compute Isolation on selected gen-leptons
        that are matched to final state particles.
        Filter out selected gen-leptons that do not
        satisfy the isolation requirement.
        """
        leptons = ak.zip({k.lower(): all_arrays[k] for k in all_arrays.keys()})
        fs_parts = ak.zip({k.lower(): all_parts[k] for k in all_parts.keys()})

        full_set = {}
        full_set["leptons"] = ak.with_name(leptons, "Momentum4D")
        full_set["fs_parts"] = ak.with_name(fs_parts, "Momentum4D")

        combs = ak.cartesian({"leptons": full_set["leptons"],
                              "fs_parts": full_set["fs_parts"]},
                             axis=-1)
        lep, fs = ak.unzip(combs)

        dR = fs.deltaR(lep)

        # TODO: Make this cut configurable
        sel_dR = dR < 0.3
        pt = full_set["fs_parts"]["pt"][sel_dR]

        # Compute Iso, reflecting definition in:
        # https://github.com/FHead/Phase2-L1MenuTools/blob/main/ObjectPerformances/V22Processing/source/HelperFunctions.cpp#L240
        Iso = ak.sum(pt, axis=-1) / full_set["leptons"]["pt"] - 1

        # TODO: Make this cut configurable
        sel_Iso = Iso > -1
        sel = sel_Iso
        final_leptons = {}

        for key in full_set["leptons"].fields:
            final_leptons[key.capitalize()] = full_set["leptons"][key][sel]

        return final_leptons

    def _postprocess_branches(self, all_arrays):
        if self._object.startswith("part"):
            all_parts = all_arrays.copy()
            all_parts = self._filter_fspart_branches(all_parts)
            all_arrays = self._filter_genpart_branches(all_arrays)
            return self._filter_iso_branches(all_parts, all_arrays)
        return all_arrays

    def _load_branches_from_ntuple(self, fname, all_arrays, branches):
        with uproot.open(fname) as f:
            for branch in branches:
                branch_arr = f[self._tree][branch].arrays(library="ak")[branch]
                branch_key = branch.removeprefix("part")
                all_arrays[branch_key] = ak.concatenate(
                    [all_arrays[branch_key], branch_arr]
                )
        return all_arrays

    @timer("Loading objects files")
    def _concat_array_from_ntuples(self):
        fnames = glob.glob(self._ntuple_path)[:]
        bar = IncrementalBar("Progress", max=len(fnames))

        branches = [self._object + x for x in self._branches]
        all_arrays = {x.removeprefix("part"): [] for x in branches}

        for fname in fnames:
            bar.next()
            all_arrays = self._load_branches_from_ntuple(
                fname, all_arrays, branches)
            all_arrays = self._postprocess_branches(all_arrays)

        self._final_ak_array = ak.zip(all_arrays)
        bar.finish()

    def _cache_file_exists(self):
        """
        Checks if there is parquet file in cache
        with the name 'version_sample_object.parquet'
        """
        cached_files = glob.glob("cache/*")
        return "cache/" + self.parquet_fname + ".parquet" in cached_files

    def _save_array_to_parquet(self):
        ak.to_parquet(
            self._final_ak_array,
            where=f"cache/{self.parquet_fname}.parquet"
        )

    def load(self):
        print(f"Process {self._object + self._part_type} object...")
        if not self._cache_file_exists():
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
        "--dry-run",
        "-d",
        action="store_true",
        help="Only do print-out of objects and branches to be loaded."
    )
    args = parser.parse_args()

    with open("cfg_caching/V22.yaml", 'r') as f:
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
                        dryrun=args.dry_run
                    )
                    loader.load()
