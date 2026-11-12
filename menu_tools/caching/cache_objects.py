import argparse
import functools
import sys
import glob
import os
import re
import time

import awkward as ak
from tqdm import tqdm
import uproot
import vector
import yaml

from menu_tools.utils import constants
from menu_tools.utils import utils


vector.register_awkward()


@functools.lru_cache(maxsize=None)
def sorted_ntuple_files(ntuple_path):
    """All files matching `ntuple_path`, sorted.

    The order must be deterministic: every object of a sample is cached by a separate
    pass over the files, and the per-event arrays of different objects (L1, HLT, bits)
    are combined later, so they must stay row-aligned. Chunked caching (--job) slices
    this same sorted list. Memoised: globbing the 12.5k-file minimum-bias directory
    on EOS takes ~0.4 s, and it was done several times per object.
    """
    return tuple(sorted(glob.glob(ntuple_path)))


@functools.lru_cache(maxsize=None)
def _load_cfg(cfg_file):
    with open(cfg_file, "r") as f:
        return yaml.safe_load(f)


@functools.lru_cache(maxsize=None)
def _tree_keys(fname, tree):
    with uproot.open(fname) as f:
        return tuple(f[tree].keys())


def _all_branches(fname, tree, obj):
    """Like utils.get_branches, for one file, memoised (nano trees only)."""
    if tree != "Events":
        return utils.get_branches(fname, tree, obj)
    return [
        x.removeprefix(obj + "_") for x in _tree_keys(fname, tree) if x.startswith(obj + "_")
    ]


def chunk_files(fnames, files_per_job, job):
    """Slice `job` (0-based) of the sorted file list, `files_per_job` files each."""
    return fnames[job * files_per_job : (job + 1) * files_per_job]


def n_chunks(n_files, files_per_job):
    return -(-n_files // files_per_job)


def chunk_dir(version):
    return os.path.join(constants.CACHE_DIR, version, "chunks")


def chunk_suffix(job):
    return f"_chunk{job:05d}"


class ObjectCacher:
    def __init__(
        self,
        version,
        sample,
        obj,
        tree,
        branches,
        cfg_file,
        dryrun=False,
        files_per_job=None,
        job=None,
    ):
        self._version = version
        self._sample = sample
        self._cfg_file = cfg_file
        self._object = obj.split("_")[0]
        self._tree = tree
        self._final_ak_array = None
        self._ref_part_iso_dR_vals = [0.1, 0.15, 0.2, 0.3, 1.5]
        self._ref_part_iso = {f"dr_{dR}": [] for dR in self._ref_part_iso_dR_vals}
        try:
            self._part_type = obj.split("_")[1]
        except IndexError:
            self._part_type = ""
        self._dryrun = dryrun
        # Chunked mode: cache only files [job*files_per_job, (job+1)*files_per_job)
        # of the sorted file list, into <version>/chunks/<name>_chunkNNNNN.parquet;
        # merge_chunks.py concatenates them in chunk order.
        if (files_per_job is None) != (job is None):
            raise ValueError("--files-per-job and --job must be given together")
        self._files_per_job = files_per_job
        self._job = job
        # Get Branches. Copy lists: YAML anchors can make several samples share one
        # list object, and the sums handling below appends to it.
        # `branches` can be a list, "all" (all `<obj>_*` branches of the first file),
        # or a dict {"exclude": [regex, ...]} = "all" minus the fields matching any regex
        # (e.g. the `_pHLT` copies of the HLT bits).
        if isinstance(branches, list):
            self._branches = list(branches)
        else:
            # first file of the sorted list (get_branches globs and takes [0])
            first = sorted_ntuple_files(self._ntuple_path)[:1]
            self._branches = (
                _all_branches(first[0], tree, obj)
                if first
                else utils.get_branches(self._ntuple_path, tree, obj)
            )
            if isinstance(branches, dict):
                excl = [re.compile(x) for x in branches.get("exclude", [])]
                self._branches = [
                    b for b in self._branches if not any(r.search(b) for r in excl)
                ]
        if self._job is not None:
            self.cache_out_path = chunk_dir(version) + "/"
        else:
            self.cache_out_path = os.path.join(constants.CACHE_DIR, version) + "/"
        os.makedirs(self.cache_out_path, exist_ok=True)

    @property
    def parquet_fname(self):
        """
        Returns the name of the output file
        that the object will produce.
        """
        fname = self._version + "_" + self._sample + "_" + self._object
        if self._part_type:
            fname += "_" + self._part_type
        if self._job is not None:
            fname += chunk_suffix(self._job)
        return fname

    @property
    def _input_files(self):
        fnames = sorted_ntuple_files(self._ntuple_path)
        if self._job is not None:
            fnames = chunk_files(fnames, self._files_per_job, self._job)
        return fnames

    @property
    def _ntuple_path(self):
        """
        Load cfg file to extract path to ntuples.
        """
        local_ntuple_path = f"l1ntuples/{self._version}/{self._sample}/*.root"
        if glob.glob(local_ntuple_path):
            return local_ntuple_path

        cfg = _load_cfg(self._cfg_file)[self._version][self._sample]
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
            behavior=array.behavior,
        )

    def _get_visible_taus(self, all_parts, status_check=True):
        """
        Create a collection of gen-level taus.
        Leptonic taus are discarded.
        Only the visible component (i.e. no neutrinos)
        of hadronically-decaying taus is considered.
        """
        all_parts = ak.zip({k.lower(): all_parts[k] for k in all_parts.keys()})

        if status_check:
            sel = (all_parts.id == 15) & (all_parts.stat == 2)

            is_tau = ak.any(sel, axis=-1)
            all_parts = ak.where(is_tau, all_parts, ak.full_like(all_parts, -1000))

        all_parts = {
            f: field
            for f, field in zip(
                ["Id", "Stat", "Pt", "Eta", "Phi", "Parent", "E"], ak.unzip(all_parts)
            )
        }

        sel_no_nu_e = abs(all_parts["Id"]) != 12
        sel_no_nu_mu = abs(all_parts["Id"]) != 14
        sel_no_nu_tau = abs(all_parts["Id"]) != 16
        sel_no_nan = abs(all_parts["Id"]) != 1000
        sel = sel_no_nu_e & sel_no_nu_mu & sel_no_nu_tau & sel_no_nan

        for branch in all_parts:
            all_parts[branch] = all_parts[branch][sel]
        all_tau_p = all_parts.copy()
        all_tau_m = all_parts.copy()

        sel = all_tau_p["Parent"] == 15
        for branch in all_tau_p:
            all_tau_p[branch] = all_tau_p[branch][sel]

        sel = all_tau_m["Parent"] == -15
        for branch in all_tau_m:
            all_tau_m[branch] = all_tau_m[branch][sel]

        all_tau_m = ak.zip({k.lower(): all_tau_m[k] for k in all_tau_m.keys()})
        all_tau_m = ak.with_name(all_tau_m, "Momentum4D")

        all_tau_p = ak.zip({k.lower(): all_tau_p[k] for k in all_tau_p.keys()})
        all_tau_p = ak.with_name(all_tau_p, "Momentum4D")

        sel_ele = ak.any(abs(all_tau_p["id"]) == 11, axis=-1)
        sel_mu = ak.any(abs(all_tau_p["id"]) == 13, axis=-1)
        sel_lep = sel_ele | sel_mu
        all_tau_p = ak.mask(all_tau_p, sel_lep, valid_when=False)

        sel_ele = ak.any(abs(all_tau_m["id"]) == 11, axis=-1)
        sel_mu = ak.any(abs(all_tau_m["id"]) == 13, axis=-1)
        sel_lep = sel_ele | sel_mu
        all_tau_m = ak.mask(all_tau_m, sel_lep, valid_when=False)

        fs_tau_p = self._p4_sum(all_tau_p)
        fs_tau_m = self._p4_sum(all_tau_m)

        # Parent, Id and Stat are dummy branches, only needed
        # for technical consistency.
        final_taus = {
            "Pt": ak.concatenate([fs_tau_p.pt, fs_tau_m.pt], axis=-1),
            "Eta": ak.concatenate([fs_tau_p.eta, fs_tau_m.eta], axis=-1),
            "Phi": ak.concatenate([fs_tau_p.phi, fs_tau_m.phi], axis=-1),
            "E": ak.concatenate([fs_tau_p.E, fs_tau_m.E], axis=-1),
            "Parent": ak.concatenate([fs_tau_p.E, fs_tau_m.E], axis=-1),
            "Id": ak.concatenate([fs_tau_p.E, fs_tau_m.E], axis=-1),
            "Stat": ak.concatenate([fs_tau_p.E, fs_tau_m.E], axis=-1),
        }

        return final_taus

    def _filter_genpart_branches(self, all_arrays):
        """
        Filter genparticle branches by Id.
        """
        partId = abs(all_arrays["Id"])
        sel_id = partId == utils.get_pdg_id(self._part_type)
        for branch in all_arrays:
            all_arrays[branch] = all_arrays[branch][sel_id]
            all_arrays[branch] = ak.fill_none(all_arrays[branch], -999)

        return all_arrays

    def _filter_fspart_branches(self, all_parts, status_check=True):
        """
        Select all the final state particles.
        This collection is used only for dR matching
        and Isolation computations, but it's not saved.
        Neutrino final state particles are not considered.
        """
        all_parts = ak.zip({k.lower(): all_parts[k] for k in all_parts.keys()})

        if status_check:
            sel = (all_parts.id == 15) & (all_parts.stat == 2)

            is_tau = ak.any(sel, axis=-1)
            all_parts = ak.where(is_tau, all_parts, ak.full_like(all_parts, -1000))

        all_parts = {
            f: field
            for f, field in zip(
                ["Id", "Stat", "Pt", "Eta", "Phi", "Parent", "E"], ak.unzip(all_parts)
            )
        }

        sel_no_nu_e = abs(all_parts["Id"]) != 12
        sel_no_nu_mu = abs(all_parts["Id"]) != 14
        sel_no_nu_tau = abs(all_parts["Id"]) != 16
        sel_no_nan = abs(all_parts["Id"]) != 1000
        sel_fs = all_parts["Stat"] == 1
        sel = sel_fs & sel_no_nu_e & sel_no_nu_mu & sel_no_nu_tau & sel_no_nan

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

    @property
    def _nano_branches(self):
        ## Nano
        if self._tree == "Events":
            return [f"{self._object}_{x}" for x in self._branches]
        ## menu ntuple
        return [self._object + x for x in self._branches]

    def _begin(self):
        """Start reading: per-branch lists of per-step arrays, concatenated in _finish."""
        self._pieces = {x.removeprefix("part"): [] for x in self._nano_branches}

    def _add_file(self, tree_obj):
        """Read this object's branches from an open TTree (one file)."""
        branches = self._nano_branches
        # Read files in chunks to avoid issues with large size files
        for array in tree_obj.iterate(filter_name=branches, step_size="100 MB"):
            chunk_array = {x.removeprefix("part"): [] for x in branches}
            chunk_array = self._load_branches_from_ntuple(chunk_array, array, branches)
            chunk_array = self._postprocess_branches(chunk_array)
            for branch in branches:
                key = branch.removeprefix("part")
                self._pieces[key].append(chunk_array[key])

    def _finish(self):
        all_arrays = {
            k: ak.concatenate(v) if len(v) > 1 else v[0] for k, v in self._pieces.items()
        }
        del self._pieces

        if self._object.startswith("part"):
            all_arrays = {**all_arrays, **self._ref_part_iso}

        if len(all_arrays) > 1:
            self._final_ak_array = ak.zip({**all_arrays})
            # sums -> add local index
            if "sums" in self._object.lower():
                self._final_ak_array[f"{self._object}_sumType"] = ak.local_index(
                    self._final_ak_array
                )
                self._branches += [f"{self._object}_sumType"]
        else:
            self._final_ak_array = ak.Array(all_arrays)

    @utils.timer("Loading objects files")
    def _concat_array_from_ntuples(self):
        self._begin()
        for fname in tqdm(self._input_files):
            with uproot.open(fname) as f:
                self._add_file(f[self._tree])
        self._finish()

    def _cache_file_exists(self):
        """
        Checks if there is parquet file in cache
        with the name 'version_sample_object.parquet'
        """
        # Check the one path rather than listing the whole cache directory.
        fpath = self.cache_out_path + f"{self.parquet_fname}.parquet"
        return os.path.exists(fpath)

    def _save_array_to_parquet(self):
        """
        Save
        """
        # An empty array would be cached and then skipped on every later run.
        if len(self._final_ak_array) == 0:
            raise RuntimeError(
                f"No events read for {self.parquet_fname}; not writing an empty cache file"
            )
        fpath = self.cache_out_path + f"{self.parquet_fname}.parquet"
        # Write then rename, so an interrupted write never leaves a complete-looking file.
        ak.to_parquet(
            self._final_ak_array,
            destination=fpath + ".tmp",
        )
        os.replace(fpath + ".tmp", fpath)

    def _needs_work(self):
        """False if cached already or dry run; raises if there are no input files."""
        if self._cache_file_exists():
            return False

        print(
            f"Loading {self._object + self._part_type} object "
            f"with the following branches: {self._branches}"
        )

        if self._dryrun:
            return False

        if not self._input_files:
            raise FileNotFoundError(
                f"No input ntuples match `{self._ntuple_path}`"
                + (f" in job {self._job}" if self._job is not None else "")
                + f"; not writing {self.parquet_fname}"
            )
        return True

    def load(self):
        if not self._needs_work():
            return
        start_time = time.time()
        self._concat_array_from_ntuples()
        self._save_array_to_parquet()
        print(f"Loaded {self.parquet_fname} in {time.time() - start_time:.2f} s")


def load_file_major(loaders):
    """Cache several objects of one sample/tree/file list, opening each file once.

    Deserialising the TTree metadata of a nano (~1000 branches) costs ~0.5 s per open,
    which dominated the per-object loop for the 160-event minimum-bias files. All objects
    of the file list are held in memory at once: use it with chunks (--job).
    """
    loaders = [ld for ld in loaders if ld._needs_work()]
    if not loaders:
        return
    start_time = time.time()
    fnames = loaders[0]._input_files
    tree = loaders[0]._tree
    assert all(ld._input_files == fnames and ld._tree == tree for ld in loaders)
    for ld in loaders:
        ld._begin()
    for fname in tqdm(fnames):
        with uproot.open(fname) as f:
            tree_obj = f[tree]
            for ld in loaders:
                ld._add_file(tree_obj)
    for ld in loaders:
        ld._finish()
        ld._save_array_to_parquet()
    print(
        f"Loaded {len(loaders)} objects from {len(fnames)} files "
        f"in {time.time() - start_time:.2f} s"
    )


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "cfg",
        help="Path to the config file in yaml format. Defaults in `configs/caching`.",
    )
    parser.add_argument(
        "--dry-run",
        "-d",
        action="store_true",
        help="Only do print-out of objects and branches to be loaded.",
    )
    parser.add_argument(
        "--samples",
        nargs="+",
        default=None,
        help="Only cache these samples (default: all samples in the config).",
    )
    parser.add_argument(
        "--objects",
        nargs="+",
        default=None,
        help="Only cache these objects (config keys, default: all).",
    )
    parser.add_argument(
        "--files-per-job",
        type=int,
        default=None,
        help="Chunked caching: number of input files per job (with --job). Output goes to "
        "<cache>/<version>/chunks/<version>_<sample>_<object>_chunkNNNNN.parquet; "
        "merge with menu_tools/caching/merge_chunks.py.",
    )
    parser.add_argument(
        "--job",
        type=int,
        default=None,
        help="Chunked caching: 0-based chunk index into the sorted file list.",
    )
    args = parser.parse_args()
    if (args.files_per_job is None) != (args.job is None):
        parser.error("--files-per-job and --job must be given together")
    return args


def main():
    # stdout block-buffers when piped or redirected, so force a flush per line.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(line_buffering=True)

    start_time = time.time()
    args = parse_args()
    cfg = _load_cfg(args.cfg)
    for version, samples in cfg.items():
        print("Processing: version", version)
        for sample, sample_cfg in samples.items():
            if args.samples and sample not in args.samples:
                continue
            print("\tSample:", sample)
            for tree, object_branches in sample_cfg["trees_branches"].items():
                if tree == "ntuple_path":
                    continue
                loaders = []
                for obj, branches in object_branches.items():
                    if args.objects and obj not in args.objects:
                        continue
                    print("\t\tObject:", obj)
                    loader = ObjectCacher(
                        version=version,
                        sample=sample,
                        tree=tree,
                        obj=obj,
                        branches=branches,
                        cfg_file=args.cfg,
                        dryrun=args.dry_run,
                        files_per_job=args.files_per_job,
                        job=args.job,
                    )
                    if args.job is None:
                        loader.load()
                    else:
                        loaders.append(loader)
                # chunked mode: read each file once for all objects
                load_file_major(loaders)
    print(f"Caching finished in {time.time() - start_time:.2f} s") 


if __name__ == "__main__":
    main()
