#!/afs/cern.ch/user/d/dhundhau/public/miniconda3/envs/py310/bin/python
import argparse
from datetime import timedelta
import glob
import itertools
import time

import awkward as ak
from progress.bar import IncrementalBar
import uproot
import yaml

from utils import get_pdg_id
from utils import get_branches


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
        except:
            self._part_type = ""
        self._dryrun = dryrun

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
        with open("cfg.yaml", 'r') as f:
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
        sel_eta = all_arrays["Eta"] < 2.4
        sel = sel_id & sel_eta
        sel_pt = ak.argmax(all_arrays["Pt"][sel], axis=-1, keepdims=True)
        for branch in all_arrays:
            all_arrays[branch] = all_arrays[branch][sel_pt]
        return all_arrays

    def _postprocess_branches(self, all_arrays):
        if self._object.startswith("part"):
            return self._filter_genpart_branches(all_arrays)
        return all_arrays

    def _concat_array_from_ntuples(self):
        fnames = glob.glob(self._ntuple_path)[:]

        print(f"Loading objects from {len(fnames)} files...")
        bar = IncrementalBar("Progress", max=len(fnames))
        t0 = time.time()

        branches = [self._object + x for x in self._branches]
        all_arrays = {x.removeprefix("part"): [] for x in branches}
        for fname in fnames:
            bar.next()
            with uproot.open(fname) as f:
                for branch in branches:
                    branch_key = branch.removeprefix("part")
                    br = f[self._tree][branch].arrays(library="ak")[branch]
                    all_arrays[branch_key] = ak.concatenate([all_arrays[branch_key], br])
            all_arrays = self._postprocess_branches(all_arrays)

        self._final_ak_array = ak.zip(all_arrays)

        t1 = time.time()
        bar.finish()
        print(f"Loading completed in {timedelta(seconds=round(t1 - t0, 0))}s")

    def _cache_file_exists(self):
        """
        Checks if there is parquet file in tmp
        with the name 'version_sample_object.parquet'
        """
        cached_files = glob.glob("tmp/*")
        return "tmp/" + self.parquet_fname + ".parquet" in cached_files

    def _save_array_to_parquet(self):
        ak.to_parquet(
            self._final_ak_array,
            where=f"tmp/{self.parquet_fname}.parquet"
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

    with open("cfg.yaml", 'r') as f:
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

