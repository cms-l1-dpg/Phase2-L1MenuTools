from functools import reduce
from itertools import combinations
import os
from typing import Optional, Union
import re
import warnings
import yaml

from tqdm import tqdm

import awkward as ak

import numpy as np
import pandas as pd
import vector

from menu_tools.rate_table.menu_config import MenuConfig
from menu_tools.utils import constants
from menu_tools.utils import objects
from menu_tools.utils import scalings

from scipy.stats import beta, norm

# Events per chunk when evaluating a seed. 0 restores whole-file behaviour.
CHUNK_SIZE = int(os.environ.get("MENU_TABLE_CHUNK", "20000"))

# 0: tqdm only. 1: the per-leg/per-seed prints. 2: also the table after each seed.
VERBOSE = int(os.environ.get("MENU_TABLE_VERBOSE", "1"))


def get_eff_err(npass,ntot, alpha=1 - 0.68):
    
    x = npass
    n = ntot
    
    lo_bound = beta.ppf(alpha / 2, x, n - x + 1)
    eff_err_lo = x / n - np.nan_to_num(lo_bound, nan=0.0)
    hi_bound = beta.ppf(1 - alpha / 2, x + 1, n - x)
    eff_err_hi = np.nan_to_num(hi_bound, nan=1.0) - x / n

    eff_err_avg = (abs(eff_err_lo) + abs(eff_err_hi))/2
    
    return eff_err_avg, eff_err_lo, eff_err_hi

vector.register_awkward()


class MenuTable:
    """
    Base class that defines the rates table.
    This class contains method to read the minbias sample,
    convert online to offline pT, and compute the trigger rates.
    All the relevant information is dumped to a csv table.
    """

    def __init__(
        self,
        config: dict,
        config_version: Optional[str] = None,
        override_version: Optional[str] = None,
        override_scalings_version: Optional[str] = None,
        override_sample: Optional[str] = None,
    ):
        self.config: MenuConfig = MenuConfig(
            config,
            config_version=config_version,
            override_version=override_version,
            override_scalings_version=override_scalings_version,
            override_sample=override_sample,
        )

        print(f"INFO: Loading cached inputs from cache/{self.config.version}")
        print(f"INFO: Saving outputs to outputs/{self.config.version}/rate_tables")
        print(f"INFO: Loading object configs from configs/{self.config.config_version_for_objects}/objects")
        print(f"INFO: Loading scalings from outputs/{self.config.scalings_version}/object_performance/scalings")
        print(f"INFO: Using sample {self.config.sample}")
        if self.config.is_signal:
            print("INFO: Signal sample requested; table holds efficiencies, rate column dropped")
        if CHUNK_SIZE > 0:
            print(f"INFO: Evaluating seeds in chunks of {CHUNK_SIZE} events")

        self.arr_cache = {}
        self._obj_mask_cache: dict[str, ak.Array] = {}
        self.table: Optional[list[dict[str, Union[str, float]]]] = None
        self._trigger_seeds: Optional[dict] = None
        self._seed_masks: dict[str, np.ndarray] = {}
        self._prepare_masks()

    @property
    def trigger_seeds(self) -> dict:
        """Loads the menu definition.

        Loads the yaml file referenced in the config,
        containing the definition of the L1 seeds.

        Returns:
            menu_seeds: dict of
        """
        # Only load seed table once
        if self._trigger_seeds is not None:
            return self._trigger_seeds

        with open(self.config.menu_config, "r") as f:
            menu_seeds = yaml.safe_load(f)

        self._trigger_seeds = menu_seeds

        return menu_seeds

    def _transform_key(self, raw_key: str, obj: objects.Object) -> str:
        """Maps <object_name><obj_field> to <object_field>.

        Returns:
            key: string of with the l1 object name prefix removed, qual
            transformed to quality
        """
        if raw_key.startswith("L1"):
            key = raw_key.removeprefix(obj.nano_obj_name + "_")
        else:
            key = raw_key.removeprefix(obj.nano_obj_name).lower()

        if "qual" in key:
            return "quality"
        return key

    def _load_cached_arrays(self, object_name: str) -> ak.Array:
        """Loads array for specified object/version combination
        from the cached parquet file.

        object_name: <object>:<id>:<eta_range> combination defining a `utils.Object`
        object.

        Returns:
            arr: Array of cached `object_name` object from sample specified in
            config
        """
        obj = objects.Object(object_name, self.config.config_version_for_objects)
        fpath = os.path.join(
            "cache",
            self.config.version,
            f"{self.config.version}_{self.config.sample}_{obj.nano_obj_name}.parquet",
        )

        arr = ak.from_parquet(fpath)
        # if fpath not in self.arr_cache:
        #     print("Loading from parquet")
        #     arr = ak.from_parquet(fpath)
        #     print(f"adding to cache: {fpath}")
        #     self.arr_cache[fpath] = arr
        # else:
        #     print("Loading from cache")
        #     arr = self.arr_cache[fpath]

        # Remove object name prefix from array fields
        arr = ak.zip({self._transform_key(var, obj): arr[var] for var in arr.fields})

        # Apply scalings, except for PV variable, which has no scalings
        if (
            ("PV" not in object_name)
            and ("disp" not in object_name.lower())
            and ("TrackTripletWord" not in object_name)
            and ("ExtTrackHT" not in object_name)
            and ("mass" not in object_name)
        ):
            if VERBOSE:
                print("adding scalings")
            arr = scalings.add_offline_pt(arr, obj, scaling_version=self.config.scalings_version)

        if "idx" not in arr.fields:
            arr["idx"] = ak.local_index(arr)

        # When loading sums (MET, HT, etc.) transfrom the array structure to
        # mimic that of "normal" objects which have lists at the event level
        # instead of a single number.
        if isinstance(arr[0], ak.highlevel.Record):
            arr = ak.zip({field: [[k] for k in arr[field]] for field in arr.fields})

        if "eta" in arr.fields:
            arr = ak.with_name(arr, "Momentum4D")

        if VERBOSE:
            print("done loading")
        return arr

    def _get_object_mask(self, object_name: str, arr: ak.Array) -> ak.Array:
        """Object ID mask, memoised: it is requested once per leg but depends only on the object."""
        if object_name not in self._obj_mask_cache:
            obj = objects.Object(object_name, self.config.config_version_for_objects)
            self._obj_mask_cache[object_name] = (
                objects.compute_selection_mask_for_object_cuts(obj, arr)
            )
        return self._obj_mask_cache[object_name]

    def get_legs_arrays_for_seed(
        self, seed_legs: dict[str, dict[str, str]]
    ) -> dict[str, ak.Array]:
        """Parses the config file (menu definition)
        to get the cuts to be used for the definition of each trigger leg
        and the L1 object used.
        The function returns the awkard array after the application of the cuts.

        seed_legs: dict of dicts with the keys `obj` and `leg_mask` defining leg of
        a seed.

        Returns:
            masked_object_arrays: Array of object the leg is defined on with
            the mask defined by the `leg_mask` value applied.
        """
        raw_object_arrays = {}
        masked_object_arrays = {}
        # Legs repeating the same (object, threshold) are built once. Seed-scoped.
        leg_array_cache: dict[tuple, ak.Array] = {}

        for leg_key, leg in seed_legs.items():
            cache_key = (leg["obj"], leg["threshold_cut"])
            if cache_key in leg_array_cache:
                masked_object_arrays[leg_key] = leg_array_cache[cache_key]
                continue

            # Load object array if not already loeaded
            if leg["obj"] not in raw_object_arrays:
                if VERBOSE:
                    print("Loading ", leg["obj"])

                if leg["obj"] not in self.arr_cache:
                    if VERBOSE:
                        print(f"Caching {leg['obj']}")
                    self.arr_cache[leg["obj"]] = self._load_cached_arrays(leg["obj"])
                else:
                    if VERBOSE:
                        print(f"Using cached {leg['obj']}")
                # raw_object_arrays[leg["obj"]] = self._load_cached_arrays(leg["obj"])
                raw_object_arrays[leg["obj"]] = self.arr_cache[leg["obj"]]

            # Prepare object ID mask
            obj_mask = self._get_object_mask(leg["obj"], raw_object_arrays[leg["obj"]])

            leg_mask = obj_mask
            leg_array = raw_object_arrays[leg["obj"]]
            if leg["threshold_cut"] is not None:
                # Substitute
                if re.match(r"leg\d", leg["threshold_cut"]):
                    leg_mask_str = re.sub(
                        r"(leg\d)", r"leg_array", leg["threshold_cut"]
                    )
                else:
                    leg_mask_str = re.sub(
                        r"([a-zA-Z_]+ )", r"leg_array.\1", leg["threshold_cut"]
                    )
                threshold_mask = eval(leg_mask_str)
                leg_mask = threshold_mask & obj_mask

            ## apply mask if regular (non-jagged) array, e.g. MET/HT etc
            if "var" in str(leg_array.type):
                masked = leg_array[leg_mask]
            else:
                masked = ak.mask(leg_array, leg_mask)

            leg_array_cache[cache_key] = masked
            masked_object_arrays[leg_key] = masked

        return masked_object_arrays

    def get_combined_legs(self, leg_arrs: dict[str, ak.Array], seed_legs) -> ak.Array:
        """
        For multi-leg triggers, this function creates the combination of the legs.
        After the trigger legs are combined, the resulting array corresponding to the
        AND of all the conditions on each leg is returned.
        """
        combined_arrays = ak.cartesian(leg_arrs)

        # duplicate handling (exclude combinations)
        # first check whether objects are repeating
        objs = [o["obj"] for o in seed_legs.values()]
        seed_has_one_leg_per_object = all([objs.count(o) <= 1 for o in objs])

        if seed_has_one_leg_per_object:
            return combined_arrays

        masks_remove_duplicates = []
        for leg1, leg2 in combinations(leg_arrs, 2):
            ## check that the legs are the same type object, skip otherwise
            if seed_legs[leg1]["obj"] == seed_legs[leg2]["obj"]:
                masks_remove_duplicates.append(
                    combined_arrays[leg1].idx != combined_arrays[leg2].idx
                )

        # Reduce over the masks instead of seeding with an all-True array.
        no_duplicates_mask = reduce(lambda a, b: a & b, masks_remove_duplicates)

        combined_arrays = combined_arrays[no_duplicates_mask]
        return combined_arrays

    def _filter_seed_legs(self, seed: str) -> dict:
        """Skim all non-leg entries from the seed menu definition and return
        as dict.

        Returns:
            seed_legs: dict with all legs from `seed` menu definition
        """
        seed_legs = {
            leg_name: leg
            for leg_name, leg in self.trigger_seeds[seed].items()
            if re.match(r"leg\d", leg_name)
        }
        return seed_legs

    def _load_cross_seeds(self, seed_name: str) -> list:
        """Loads the cross seeds

        seed: name of the trigger seed

        Returns:
            cross_seeds: todo
        """
        cross_seeds: list = []
        seeds = self.trigger_seeds[seed_name]
        if "x_seeds" not in seeds:
            return cross_seeds

        cross_seeds = seeds[seed_name]["x-seeds"]
        assert isinstance(cross_seeds, list), "x-seeds value must be list!"
        return cross_seeds

    def _pass_mask_for_chunk(
        self,
        legs_arrays: dict[str, ak.Array],
        seed_legs: dict,
        cross_mask_strs: list,
    ) -> ak.Array:
        """Per-event pass mask for one slice of events.

        Filtering the combinations after each cross mask is equivalent to ANDing
        them all, but keeps only two combination-length booleans live at a time.
        """
        combined_legs = self.get_combined_legs(legs_arrays, seed_legs)

        ## add cross_conditions
        for cross_mask_str in cross_mask_strs:
            eval_str = re.sub(r"(leg\d)", r"combined_legs['\1']", cross_mask_str)
            mask = ak.fill_none(eval(eval_str), False, axis=None)
            combined_legs = combined_legs[mask]

        # Cut on the individual object thresholds
        # if "var" in str(combined_legs.type):
        return ak.num(combined_legs, axis=-1) > 0
        # else:
        #     raise RuntimeError("This part of the code needs some work!")
        #     # total_mask = total_mask & ~ak.is_none(_leg)

    def get_trigger_pass_mask(self, seed_name: str) -> np.ndarray:
        """Computes number of events passing the `seed`.

        After loading the minbias sample and the menu definition,
        each leg is selected and the masks are applied
        (together with cross-masks/seeds).

        Returns:
            total_mask: boolean numpy array mask defining trigger `seed`
        """
        if VERBOSE:
            print("==> ", seed_name)
        seed_legs = self._filter_seed_legs(seed_name)
        legs_arrays = self.get_legs_arrays_for_seed(seed_legs)
        cross_mask_strs: list = self.trigger_seeds[seed_name]["cross_masks"]

        # Nothing below reduces across events, so per-chunk masks concatenate.
        n_events = len(next(iter(legs_arrays.values())))
        step = CHUNK_SIZE if CHUNK_SIZE > 0 else n_events

        pieces = []
        for lo in range(0, n_events, step):
            chunk = {k: v[lo : lo + step] for k, v in legs_arrays.items()}
            chunk_mask = self._pass_mask_for_chunk(chunk, seed_legs, cross_mask_strs)
            chunk_mask = ak.fill_none(chunk_mask, False, axis=None)
            pieces.append(ak.to_numpy(chunk_mask).astype(np.bool_))

        total_mask = pieces[0] if len(pieces) == 1 else np.concatenate(pieces)

        ## Add cross-seeds
        cross_seeds = self._load_cross_seeds(seed_name)
        for xseed in cross_seeds:
            xseed_mask = self.get_trigger_pass_mask(self.trigger_seeds[xseed])
            total_mask = total_mask & xseed_mask

        return total_mask

    def _prepare_masks(self) -> dict[str, np.ndarray]:
        """Calls `get_trigger_pass_mask` for each object defined in the menu.
        The function returns the masks for each object.

        Returns:
            seed_masks: array contining masks all trigger seeds
        """
        seed_masks: dict = {}

        pbar = tqdm(self.trigger_seeds)
        for seed_name in pbar:
            mask = np.asarray(self.get_trigger_pass_mask(seed_name))
            seed_masks[seed_name] = mask
            self._seed_masks = seed_masks
            if len(mask):
                efficiency = mask.sum() / len(mask)
                if self.config.is_signal:
                    summary = f"eff {efficiency * 100:.3g}%"
                else:
                    summary = f"{efficiency * constants.RATE_NORM_FACTOR:.1f} kHz"
                pbar.set_postfix_str(f"{seed_name}: {summary}")
            # make_table rebuilds the whole table each call, so this is O(n_seeds^2).
            if VERBOSE >= 2:
                self.make_table()
                self.print_table()

        # self.compute_tot_and_pure()

        return seed_masks

    def print_table(self) -> None:
        """
        Prints the rate table to stdout.
        """
        print("===============")
        print("=====TABLE=====")
        print("===============")
        df_table = pd.DataFrame(self.table)
        print(df_table)

    def compute_tot_and_pure(self) -> pd.DataFrame:
        df_masks = ak.to_dataframe(self._seed_masks)
        counts = {}

        for seed in df_masks.columns:
            counts[seed] = {
                "total": df_masks[seed].sum(),
                "pure": (
                    (df_masks[seed] == True)
                    & ~(df_masks.drop(seed, axis=1).any(axis=1))
                ).sum(),
            }

        counts["total"] = {
            "total": np.sum(np.any(df_masks, axis=1)),
            "pure": 0,
        }

        df_counts = pd.DataFrame(counts).T
        df_counts.index.name = "seed"

        # ## ALTERNATIVE
        ntot = len(df_masks[seed])
        df_counts["eff_total"] = df_counts["total"] / ntot
        df_counts["eff_pure"] = df_counts["pure"] / ntot

        df_counts["rate_total"] = df_counts["eff_total"] * constants.RATE_NORM_FACTOR
        df_counts["rate_pure"] = df_counts["eff_pure"] * constants.RATE_NORM_FACTOR

        print(df_counts)
        out_file = os.path.join(
            self.config.table_outdir,
            f"{self.config.table_fname}_{self.config.version}{self.config.scalings_suffix}{self.config.sample_suffix}_pd.csv",
        )
        df_counts.to_csv(out_file)

        return df_counts

    def make_table(self) -> None:
        """
        Function that prints to screen the rates table.
        Returns a list containing the csv-compatible table.
        """
        print("Making table")

        table: list[dict[str, Union[str, float]]] = []
        # Accumulate the OR in numpy rather than rebuilding an array per seed.
        all_seeds_or_mask = np.zeros(
            len(np.asarray(list(self._seed_masks.values())[0])), dtype=np.bool_
        )

        for seed, mask in self._seed_masks.items():
            mask = np.asarray(mask)
            # Compute seed values
            npass = np.sum(mask)
            efficiency = npass / len(mask)
            # effErr, effErrLo, effErrHi = get_eff_err(npass, len(mask), alpha=1-0.68)
            row: dict[str, Union[str, float]] = {
                "seed": seed,
                "npass": npass,
                "efficiency": efficiency,
                # "effErr": effErr,
            }
            if not self.config.is_signal:
                row["rate"] = efficiency * constants.RATE_NORM_FACTOR
                # row["rateErr"] = effErr * constants.RATE_NORM_FACTOR
            table.append(row)
            # Modify total mask
            all_seeds_or_mask |= mask

        ## Total OR of all seeds
        npass = np.sum(all_seeds_or_mask)
        efficiency = npass / len(all_seeds_or_mask)
        # effErr, effErrLo, effErrHi = get_eff_err(npass, len(all_seeds_or_mask), alpha=1-0.68)
        total_row: dict[str, Union[str, float]] = {
            "seed": "Total",
            "npass": npass,
            "efficiency": efficiency,
            # "effErr": effErr,
        }
        nevts_row: dict[str, Union[str, float]] = {
            "seed": "Total Event Number",
            "npass": len(all_seeds_or_mask),
            "efficiency": np.nan,
            # "effErr": np.nan,
        }
        if not self.config.is_signal:
            total_row["rate"] = efficiency * constants.RATE_NORM_FACTOR
            # total_row["rateErr"] = effErr * constants.RATE_NORM_FACTOR
            nevts_row["rate"] = np.nan
            # nevts_row["rateErr"] = np.nan
        table.append(total_row)
        table.append(nevts_row)
        self.table = table

    def dump_masks(self) -> None:
        """
        Dumps the masks produced by `_prepare_masks` to parquet file.
        """
        os.makedirs(self.config.table_outdir, exist_ok=True)
        out_path = os.path.join(
            self.config.table_outdir,
            f"{self.config.table_fname}_{self.config.version}{self.config.scalings_suffix}{self.config.sample_suffix}_masks.parquet",
        )
        print(f"Dumping masks of seeds to `{out_path}`")
        # Masks are held as bool; drop the astype for an 8x smaller file.
        dumped = {k: np.asarray(v).astype(np.int64) for k, v in self._seed_masks.items()}
        ak.to_parquet(ak.zip(dumped), out_path, compression = "LZ4")

    def save_table(self) -> None:
        """Function that saves to file the table produced by `make_table`."""
        if self.table is None:
            warnings.warn("Table was not computed yet. Run `make_table` first.")
            return

        os.makedirs(self.config.table_outdir, exist_ok=True)
        out_file = os.path.join(
            self.config.table_outdir,
            f"{self.config.table_fname}_{self.config.version}{self.config.scalings_suffix}{self.config.sample_suffix}.csv",
        )
        columns = list(self.table[0].keys())
        with open(out_file, "w") as f:
            f.write(",".join(columns) + "\n")
            for seed in self.table:
                f.write(",".join(str(seed[col]) for col in columns) + "\n")
