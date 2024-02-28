from itertools import combinations
import os
from typing import Optional, Union
import re
import warnings
import yaml

import awkward as ak
import numpy as np
import vector

from menu_tools.rate_table.menu_config import MenuConfig
from menu_tools.utils import constants
from menu_tools.utils import objects
from menu_tools.utils import scalings


vector.register_awkward()


class MenuTable:
    """
    Base class that defines the rates table.
    This class contains method to read the minbias sample,
    convert online to offline pT, and compute the trigger rates.
    All the relevant information is dumped to a csv table.
    """

    def __init__(self, config: dict):
        self.config: MenuConfig = MenuConfig(config)
        self.table: Optional[list[dict[str, Union[str, float]]]] = None
        self._seed_masks: dict[str, np.ndarray] = self._prepare_masks()

    @property
    def trigger_seeds(self) -> dict:
        """Loads the menu definition.

        Loads the yaml file referenced in the config,
        containing the definition of the L1 seeds.

        Returns:
            menu_seeds: dict of
        """
        with open(self.config.menu_config, "r") as f:
            menu_seeds = yaml.safe_load(f)

        return menu_seeds

    def _transform_key(self, raw_key: str, obj: objects.Object) -> str:
        """Maps <object_name><obj_field> to <object_field>.

        Returns:
            key: string of with the l1 object name prefix removed, qual
            transformed to quality
        """
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
            arr: Array of cached `object_name` object from MinBias sample
        """
        obj = objects.Object(object_name, self.config.version)
        fpath = os.path.join(
            "cache",
            self.config.version,
            f"{self.config.version}_MinBias_{obj.nano_obj_name}.parquet",
        )
        arr = ak.from_parquet(fpath)

        # Remove object name prefix from array fields
        arr = ak.zip({self._transform_key(var, obj): arr[var] for var in arr.fields})

        # Apply scalings
        arr = scalings.add_offline_pt(arr, obj)
        arr["pt"] = scalings.get_pt_branch(arr)

        # TODO: What is this? Is it needed?
        # if "jagged0" in arr.fields:
        #     arr = arr["jagged0"]
        arr = ak.with_name(arr, "Momentum4D")
        return arr

    def remove_empty_events_and_nones(self, arr: ak.Array) -> ak.Array:
        ## apply mask if regular (non-jagged) array, e.g. MET/HT etc
        if "var" in str(arr.type):
            arr = arr[ak.num(arr) > 0]
        else:
            arr = arr[~ak.is_none(arr)]
        return arr

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

        for leg_key, leg in seed_legs.items():
            # Load object array if not already loeaded
            if leg["obj"] not in raw_object_arrays:
                raw_object_arrays[leg["obj"]] = self._load_cached_arrays(leg["obj"])

            # Prepare object ID mask
            obj = objects.Object(leg["obj"], self.config.version)
            obj_mask = objects.compute_selection_mask_for_object_cuts(
                obj, raw_object_arrays[leg["obj"]]
            )

            # Substitute
            leg_mask_str = re.sub(
                r"([a-zA-Z_]+ )", r"leg_array.\1", leg["threshold_cut"]
            )
            leg_array = raw_object_arrays[leg["obj"]]
            threshold_mask = eval(leg_mask_str)

            # Combined leg mask
            leg_mask = threshold_mask & obj_mask

            ## apply mask if regular (non-jagged) array, e.g. MET/HT etc
            if "var" in str(leg_array.type):
                masked_object_arrays[leg_key] = leg_array[leg_mask]
            else:
                masked_object_arrays[leg_key] = ak.mask(leg_array, leg_mask)

        return masked_object_arrays

    def get_combined_legs(self, leg_arrs: dict[str, ak.Array], seed_legs) -> ak.Array:
        """
        For multi-leg triggers, this function creates the combination of the legs.
        After the trigger legs are combined, the resulting array corresponding to the
        AND of all the conditions on each leg is returned.
        """
        if len(leg_arrs) > 1:
            combined_arrays = ak.cartesian(leg_arrs)
        else:
            combined_arrays = leg_arrs

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
                print(combined_arrays[leg1].fields)
                masks_remove_duplicates.append(
                    combined_arrays[leg1].idx != combined_arrays[leg2].idx
                )

        no_duplicates_mask = ak.from_numpy(
            np.ones(len(combined_arrays), dtype=np.bool_)
        )
        for i, mask in enumerate(masks_remove_duplicates):
            print(f"{i=}")
            no_duplicates_mask = no_duplicates_mask & mask

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

    def get_eval_string(self, legs_arrays: dict[str, ak.Array]) -> str:
        """Selects only relevant entries in the arrays and returns the
        awkward array corresponding to events which satisfy the cuts on the trigger
        legs.

        Returns:
          eval_str: TODO!
        """
        eval_strings: list = []
        for leg, leg_arr in legs_arrays.items():
            if "var" in str(leg_arr.type):
                eval_strings.append(f"(ak.num({leg}) > 0)")
            else:
                eval_strings.append(f"(ak.is_none({leg}) == False)")
        eval_str: str = " & ".join(eval_strings)

        return eval_str

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

    def get_trigger_pass_mask(self, seed_name: str) -> ak.Array:
        """Computes number of events passing the `seed`.

        After loading the minbias sample and the menu definition,
        each leg is selected and the masks are applied
        (together with cross-masks/seeds).

        Returns:
            total_mask: boolean awkward array mask defining trigger `seed`
        """
        print("====")
        print(seed_name)
        total_mask = 1
        ##
        seed_legs = self._filter_seed_legs(seed_name)
        legs_arrays = self.get_legs_arrays_for_seed(seed_legs)
        combined_legs = self.get_combined_legs(legs_arrays, seed_legs)
        combined_legs = self.remove_empty_events_and_nones(combined_legs)

        # for leg, leg_arr in legs_arrays.items():
        # print(leg)
        # _leg = combined_legs[leg]
        # TODO: comment what this check is about
        # if "var" in str(leg_arr.type):
        #     total_mask = total_mask & (ak.num(_leg) > 0)
        # else:
        #     total_mask = total_mask & ~ak.is_none(_leg)

        ## add cross_conditions
        cross_mask_strs: list = self.trigger_seeds[seed_name]["cross_masks"]
        if len(cross_mask_strs) > 0:
            eval_str = " & ".join(cross_mask_strs)
            eval_str = re.sub(r"(leg\d)", r"combined_legs['\1']", eval_str)
            _ = combined_legs["leg1"]
            _ = combined_legs["leg2"]
            print(combined_legs["leg1"].deltaR(combined_legs["leg2"]))
            print(eval_str)
            cross_mask = eval(f"ak.any({eval_str}, axis=1)")
            total_mask = total_mask & cross_mask

        ## Add cross-seeds
        cross_seeds = self._load_cross_seeds(seed_name)
        for xseed in cross_seeds:
            xseed_mask = self.get_trigger_pass_mask(self.trigger_seeds[xseed])
            total_mask = total_mask & xseed_mask

        total_mask = ak.fill_none(total_mask, False)
        return total_mask

    def _prepare_masks(self) -> dict[str, np.ndarray]:
        """Calls `get_trigger_pass_mask` for each object defined in the menu.
        The function returns the masks for each object.

        Returns:
            seed_masks: array contining masks all trigger seeds
        """
        seed_masks: dict = {}

        for seed_name in self.trigger_seeds:
            mask = self.get_trigger_pass_mask(seed_name)
            seed_masks[seed_name] = mask.to_numpy()

        return seed_masks

    def print_table(self) -> None:
        """
        TODO: This function should take all the printing stuff out of
        `make_table`
        """
        raise NotImplementedError
        # print(seed.ljust(50), ":\t%8i\t%.5f\t%.1f" % (npass, efficiency, rate))
        # tot_str = "Total:".ljust(50) + "\t%8i\t%.5f\t%.1f" % (npass, efficiency, rate)
        # print((len(tot_str) + 5) * "-")
        # print(tot_str)
        # print("Total nev: %i" % len(total_mask))

    def make_table(self) -> None:
        """
        Function that prints to screen the rates table.
        Returns a list containing the csv-compatible table.
        """

        table: list[dict[str, Union[str, float]]] = []
        all_seeds_or_mask = ak.zeros_like(self._seed_masks.values()[0])
        for seed, mask in self._seed_masks.items():
            # Compute seed values
            npass = np.sum(mask)
            efficiency = npass / len(mask)
            rate = efficiency * constants.RATE_NORM_FACTOR
            table.append(
                {"seed": seed, "npass": npass, "efficiency": efficiency, "rate": rate}
            )
            # Modify total mask
            all_seeds_or_mask = all_seeds_or_mask | mask

        ## Total OR of all seeds
        npass = np.sum(all_seeds_or_mask)
        efficiency = npass / len(all_seeds_or_mask)
        rate = efficiency * constants.RATE_NORM_FACTOR
        table.append(
            {"seed": "Total", "npass": npass, "efficiency": efficiency, "rate": rate}
        )
        table.append(
            {
                "seed": "Total Event Number",
                "npass": len(all_seeds_or_mask),
                "efficiency": np.nan,
                "rate": np.nan,
            }
        )

        self.table = table

    def dump_masks(self) -> None:
        """
        Dumps the masks produced by `_prepare_masks` to parquet file.
        """
        os.makedirs(self.config.table_outdir, exist_ok=True)
        out_path = os.path.join(
            self.config.table_outdir,
            f"{self.config.table_fname}_{self.config.version}_masks.parquet",
        )
        print(f"Dumping masks of seeds to `{out_path}`")
        ak.to_parquet(ak.zip(self._seed_masks), out_path)

    def save_table(self) -> None:
        """Function that saves to file the table produced by `make_table`."""
        if self.table is None:
            warnings.warn("Table was not computed yet. Run `make_table` first.")
            return

        os.makedirs(self.config.table_outdir, exist_ok=True)
        out_file = os.path.join(
            self.config.table_outdir,
            f"{self.config.table_fname}_{self.config.version}.csv",
        )
        with open(out_file, "w") as f:
            f.write(",".join(self.table[0]) + "\n")
            for seed in self.table:
                f.write(f"{seed['seed']},")
                f.write(f"{seed['npass']},")
                f.write(f"{seed['efficiency']},")
                f.write(f"{seed['rate']}\n")
