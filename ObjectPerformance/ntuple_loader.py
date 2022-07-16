#!/afs/cern.ch/user/d/dhundhau/miniconda3/envs/py310/bin/python
from datetime import timedelta
import glob
import itertools
import time

import pandas as pd
from progress.bar import IncrementalBar
import uproot
import yaml


class NTupleLoader():

    def __init__(self, version, sample):
        self._version = version
        self._sample = sample
        self._ntuple_path = ""
        self._trees_branches = {}
        self._df = None
        self._load_cfg()

    def _load_trees_branches(self, f):
        df = None
        for tree_key, branches in self._trees_branches.items():
            for branch_key in branches:
                df_gen = f[tree_key].arrays(
                    branch_key,
                    library="pd"
                )
                df = pd.concat([df, df_gen], axis=1)
        return df

    def _load_ntuples_into_df(self):
        fnames = glob.glob(self._ntuple_path)[:40]
        df = None

        print(f"Loading objects from {len(fnames)} files...")
        bar = IncrementalBar("Progress", max=len(fnames))
        t0 = time.time()

        for f_in in fnames:
            bar.next()
            with uproot.open(f_in) as f:
                df_file = self._load_trees_branches(f)
            df = pd.concat([df, df_file], axis=0)

        t1 = time.time()
        bar.finish()
        print(f"Loading completed in {timedelta(seconds=round(t1 - t0, 0))}s")
        self.df = df

    def _get_h5_fname(self):
        return self._version + '_' + self._sample

    def _load_cfg(self):
        with open("cfg.yaml", 'r') as f:
            cfg = yaml.safe_load(f)[self._version][self._sample]
        self._ntuple_path = cfg["ntuple_path"]
        self._trees_branches = cfg["trees_branches"]

    def _cache_has_columns(self):
        """
        Checks if the required columns
        are present in the cached h5 file.
        """
        required_keys = list(itertools.chain(*[x for x in self._trees_branches.values()]))
        print(required_keys)
        return all([x in self.df.columns for x in required_keys])

    def _cache_file_exists(self):
        """
        Checks if there is h5 file in tmp
        with the name 'version_sample.h5'
        """
        try:
            self.df = pd.read_hdf(f"tmp/{self._get_h5_fname()}.h5", key="l1")
            return True
        except FileNotFoundError:
            return False

    def _save_df(self):
        self.df.to_hdf(f"tmp/{self._get_h5_fname()}.h5", key="l1")

    def load(self):
        if not (self._cache_file_exists() and self._cache_has_columns()):
            print("No adequate cache file.")
            self._load_ntuples_into_df()
            self._save_df()


if __name__ == "__main__":
    loader = NTupleLoader("V22", "TT")
    loader.load()

