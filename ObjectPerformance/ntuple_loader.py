#!/eos/user/d/dhundhau/miniconda3/envs/l1phase2/bin/python
from datetime import timedelta
import glob
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
        self._gen_trees = {}
        self._reco_trees = []
        self._df = None
        self._load_config()
    
    def _apply_column_trafo(self, df, x, operation):
        if "sum" in operation:
            df = df.groupby(level=0).sum()
        if "sumThreshold30" in operation:
            df.loc[df[x] < 30, x] = 0
            df = df.groupby(level=0).sum()
        return df

    def _load_reco_trees(self, f):
        df = None
        for tree_key in self._reco_trees:
            df_reco = f["l1PhaseIITree/L1PhaseIITree"].arrays(
                tree_key,
                library="pd"
            )
            df = pd.concat([df, df_reco], axis=1)
        return df

    def _load_gen_trees(self, f):
        df = None
        for obs, tree_conf in self._gen_trees.items():
            tree_key = tree_conf["treeKey"]
            operation = tree_conf["operation"]
            df_gen = f["genTree/L1GenTree"].arrays(
                tree_key,
                library="pd"
            )
            df_gen = df_gen.rename(columns={tree_key: obs})
            df_gen = self._apply_column_trafo(df_gen, obs, operation)
            df = pd.concat([df, df_gen], axis=1)
        return df
    
    def _load_ntuples_into_df(self):
        fnames = glob.glob(self._ntuple_path + "L1NtuplePhaseII_Step1_*.root")[:]
        df = None

        print(f"Loading objects from {len(fnames)} files...")
        bar = IncrementalBar("Progress", max=len(fnames))
        t0 = time.time()

        for f_in in fnames:
            bar.next()
            with uproot.open(f_in) as f:
                df_gen = self._load_gen_trees(f)
                df_reco = self._load_reco_trees(f)
            df_merged = pd.concat([df_gen, df_reco], axis=1)
            df = pd.concat([df, df_merged], axis=0)

        t1 = time.time()
        bar.finish()
        print(f"Loading completed in {timedelta(seconds=round(t1 - t0, 0))}s")
        self.df = df

    def _get_h5_fname(self):
        return self._version + '_' + self._sample

    def _load_config(self):
        with open("config.yaml", 'r') as f:
            cfg = yaml.safe_load(f)[self._version][self._sample]
        self._ntuple_path = cfg["ntuple_path"]
        self._gen_trees = cfg["gen_trees"]
        self._reco_trees = cfg["reco_trees"]

    def _cache_has_columns(self):
        """
        Checks if the required columns
        are present in the cached h5 file.
        """
        required_keys = self._reco_trees + list(self._gen_trees.keys())
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

