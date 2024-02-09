import yaml
import os

import awkward as ak
import numpy as np
import uproot
import vector

from menu_tools.rate_table.menu_config import MenuConfig


vector.register_awkward()


class MenuTable:
    """
    Base class that defines the rates table.
    This class contains method to read the minbias sample,
    convert online to offline pT, and compute the trigger rates.
    All the relevant information is dumped to a csv table.
    """

    def __init__(self, cfg):
        self.cfg = MenuConfig(cfg)
        self.version = self.cfg.version
        self.fname = self.cfg.sample
        self.table_outdir = self.cfg.table_outdir
        self.table_fname = self.cfg.table_fname
        self.cfg_fname = self.cfg.menu_cfg
        self.scalings = self.get_scalings(
            os.path.join(self.cfg.scalings_outdir, self.cfg.scalings_file)
        )
        self.trig_seeds = self.get_trig_seeds()

    def load_minbias(self, obj):
        """
        Function to load the minbias sample to be used for the rates computation.
        The name of the file is specified in the config used for the MenuTable init.
        """
        with uproot.open(self.fname) as f:
            arr = f["l1PhaseIITree/L1PhaseIITree"].arrays(
                filter_name=f"{obj}*", how="zip"
            )
        return arr

    def get_scalings(self, scalings):
        """
        Get the list of scalings for all the L1 objects.
        Scalings are collected by the Scaler() class and
        saved to a yaml file.
        The inputs used are the files created in `objectPerformance`
        and saved in `objectPerformance/output/VX/scalings/*.txt`
        """
        with open(f"{scalings}", "r") as infile:
            scalings_eta = yaml.safe_load(infile.read())
        return scalings_eta

    def get_trig_seeds(self):
        """
        Get the menu definition.
        Load a yaml file containing the definition of the objects
        and the cuts of each leg for the different trigger paths.
        """
        with open(self.cfg_fname, "r") as infile:
            test_trig_seeds = yaml.safe_load(infile.read())

        return test_trig_seeds

    def add_offline_pt(self, arr, obj_scalings, pt_var=None):
        """
        Use the scalings to convert online pT to offline pT.
        The `pt_var` argument can be used to specify which observables
        should be used as "pT" for a given object.
        If `pt_var` is not specified, `pt` or `et` are used.
        For each object, a dedicated scaling in the barrel/endcap regions
        is applied to the online pT.
        """
        # initialise array of zeros identical to the original pt
        if pt_var is not None:
            pt_orig = arr[pt_var]
        elif "et" in arr.fields:
            pt_orig = arr.et
        elif "pt" in arr.fields:
            pt_orig = arr.pt
        elif "" in arr.fields:
            pt_orig = arr[""][:, 0]
        else:
            print("Error! Unknown pt branch")
            return 0

        if None in obj_scalings:
            values = obj_scalings[None]
            new_pt = pt_orig * values["slope"] + values["offset"] * (pt_orig > 0)
        else:
            new_pt = ak.zeros_like(pt_orig)

            # loop through eta regions with it's scaling parameters
            for region, values in obj_scalings.items():
                # create eta mask for this eta region
                eta_mask = (abs(arr.eta) >= values["eta_min"]) & (
                    abs(arr.eta) < values["eta_max"]
                )
                # scale pt for non-masked elements of this eta region
                new_pt = new_pt + eta_mask * (
                    pt_orig * values["slope"] + values["offset"]
                )

        return ak.with_field(arr, new_pt, "offline_pt")

    def scale_pt(self, obj, arr):
        """
        Wrapper function that calls `add_offline_pt` if the scaling is defined.
        If the scaling for a given object is not found, `offline_pt` is set to
        be equal to the online pt.
        """

        if obj in self.scalings:
            # print(self.scalings[obj])
            arr = self.add_offline_pt(arr, self.scalings[obj])
        else:
            print("No scalings found for " + obj)
            if "" in arr.fields:
                arr["et"] = arr[""]
                arr["pt"] = arr[""]
            arr["offline_pt"] = arr.pt

        if "eta" in arr.fields:
            arr["mass"] = 0.0 * ak.ones_like(arr["eta"])
            arr = ak.with_name(arr, "Momentum4D")

        arr["idx"] = ak.local_index(arr)
        return arr

    def format_values(self, arr):
        """
        Function to format values in the array.
        The `et` branch is converted to `pt`, if no `pt` is found in the array.
        If neither `pt` nor `et` are found in the array, the corresponding
        entries will be left empty or filled with the unique field of the array.
        The ID branches (`["passeseleid","passessaid","passesphoid"]`) are
        converted into boolean variables for easier usage in the triggers definition.
        """
        if "et" not in arr.fields:
            if "pt" in arr.fields:
                arr["et"] = arr.pt
            elif "" in arr.fields:
                arr["pt"] = arr[""]
                arr["et"] = arr[""]
        elif "pt" not in arr.fields:
            if "et" in arr.fields:
                arr["pt"] = arr.et

        for x in ["passeseleid", "passessaid", "passesphoid"]:
            if x in arr.fields:
                arr[x] = ak.values_astype(arr[x], bool)

        return arr

    def get_obj_arr(self, obj):
        """
        Function that loads the minbias sample and gets the relevant object from the
        TTree.
        The TBranches are loaded in an awkward array, `format_values` is used to parse
        the `pt`, `et`, and ID branches.
        The `scale_pt` function is used to convert the online pT into offline using the
        scalings.
        """
        # TODO: Implement reading from parquet
        # vers = self.version
        # arr = ak.from_parquet(fname)

        load_obj = obj

        if obj == "tkIsoElectron":
            load_obj = "tkElectron"

        arr = self.load_minbias(load_obj)
        if "jagged0" in arr.fields:
            arr = arr["jagged0"]

        arr = ak.zip({f.replace(load_obj, "").lower(): arr[f] for f in arr.fields})
        arr = self.format_values(arr)

        arr = self.scale_pt(obj, arr)

        return arr

    def get_legs(self, seed_legs):
        """
        Function that parses the config file (menu definition)
        to get the cuts to be used for the definition of each trigger leg
        and the L1 object used.
        The function returns the awkard array after the application of the cuts.
        """
        all_arrs = {}
        leg_arrs = {}

        for leg, items in seed_legs.items():
            obj = items["obj"]

            if obj not in all_arrs:
                all_arrs[obj] = self.get_obj_arr(obj)

            leg_mask_str = items["leg_mask"]

            leg_mask_str = "&".join([f"({s})" for s in leg_mask_str]).replace(
                leg, "leg_arr"
            )
            leg_arr = all_arrs[obj]

            # get masked array
            leg_mask = eval(leg_mask_str)

            ## apply mask if regular (non-jagged) array, e.g. MET/HT etc
            if "var" in str(leg_arr.type):
                leg_arrs[leg] = leg_arr[leg_mask]
            else:
                leg_arrs[leg] = ak.mask(leg_arr, leg_mask)

        return leg_arrs

    def get_combos(self, leg_arrs, seed_legs):
        """
        For multi-leg triggers, this function creates the combination of the legs.
        After the trigger legs are combined, the resulting array corresponding to the
        AND of all the conditions on each leg is returned.
        """
        if len(leg_arrs) > 1:
            combos = ak.cartesian(leg_arrs)
        else:
            combos = leg_arrs

        ## duplicate handling (exclude combinations)
        ## first check whether objects are repeating
        objs = [o["obj"] for o in seed_legs.values()]
        obj_cnts = {i: objs.count(i) for i in objs}

        if np.max(list(obj_cnts.values())) > 1:
            nodup_masks = []

            for i, l1 in enumerate(leg_arrs.keys()):
                for j, l2 in enumerate(leg_arrs.keys()):
                    if i >= j:
                        continue
                    ## check that the legs are the same type object, skip otherwise
                    if seed_legs[l1]["obj"] != seed_legs[l2]["obj"]:
                        continue
                    nodup_masks.append(combos[l1].idx != combos[l2].idx)

            if len(nodup_masks) > 0:
                eval_str = " & ".join(
                    [f"nodup_masks[{i}]" for i in range(len(nodup_masks))]
                )
                nodup_mask = eval(eval_str)
                combos = combos[nodup_mask]

        return combos

    def get_legs_and_masks(self, seed_legs):
        """
        Wrapper function that calls `get_legs` and `get_combos`.
        This function returns the awkward arrays with the legs definition
        and the definition of the combinations in case of multi-leg triggers.
        """
        ### load all legs
        leg_arrs = self.get_legs(seed_legs)

        ### leg duplicate removal
        combos = self.get_combos(leg_arrs, seed_legs)

        return leg_arrs, combos

    def get_eval_string(self, leg_arrs):
        """
        Function that selects only relevant entries in the arrays and returns the
        awkward array corresponding to events which satisfy the cuts on the trigger
        legs.
        """
        eval_str = []
        for leg, leg_arr in leg_arrs.items():
            if "var" in str(leg_arr.type):
                eval_str.append(f"(ak.num({leg}) > 0)")
            else:
                eval_str.append(f"(ak.is_none({leg}) == False)")
        eval_str = " & ".join(eval_str)

        return eval_str

    def seeds_from_cfg(self, seed):
        """
        Function that loads the information from the menu config.
        Returns the legs, cross_masks, and cross-triggers (if present).
        """
        seed_legs = {
            leg: self.trig_seeds[seed][leg]
            for leg in self.trig_seeds[seed]
            if "leg" in leg
        }
        cross_masks_str = self.trig_seeds[seed]["cross_masks"]
        if len(cross_masks_str) > 0:
            cross_masks_str = [cross_masks_str]
        cross_seeds = []
        for leg, items in self.trig_seeds[seed].items():
            if leg == "x-seeds":
                if isinstance(items, list):
                    cross_seeds += items
                else:
                    cross_seeds.append(items)
        return seed_legs, cross_masks_str, cross_seeds

    def get_npass(self, seed, trig_seed):
        """
        Main function that computes the nr of events passing each trigger.
        After loading the minbias sample and the menu definition,
        each leg is selected and the masks are applied
        (together with cross-masks/seeds).
        The function returns the total mask that defines the trigger.
        """
        seed_legs, cross_masks_str, cross_seeds = self.seeds_from_cfg(seed)
        leg_arrs, combos = self.get_legs_and_masks(seed_legs)

        ## define leg arrays
        for leg in leg_arrs:
            exec(f"{leg} = combos['{leg}']")

        ## require presence of legs
        eval_str = self.get_eval_string(leg_arrs)
        nleg_mask = eval(eval_str)

        ## create event mask
        total_mask = nleg_mask

        ## add cross_conditions
        if len(cross_masks_str) > 0:
            cross_mask = []

            for cross_mask_str in [
                item for sublist in cross_masks_str for item in sublist
            ]:
                cross_mask.append(eval(cross_mask_str))

            ## combine cross_masks
            eval_str = " & ".join([f"cross_mask[{i}]" for i in range(len(cross_mask))])
            cross_mask_all = eval(f"ak.any({eval_str}, axis = 1)")

            total_mask = total_mask & cross_mask_all

        ## Add cross-seeds:
        for xseed in cross_seeds:
            xseed_mask = self.get_npass(self.trig_seeds[xseed])
            total_mask = total_mask & xseed_mask

        total_mask = ak.fill_none(total_mask, False)
        return total_mask

    def prepare_masks(self):
        """
        Wrapper function that calls `get_npass`
        for each object defined in the menu.
        The function returns the masks for each object.
        """
        trig_masks = {}

        seeds = self.trig_seeds

        for seed in sorted(seeds):
            print(seed)

            mask = self.get_npass(seed, self.trig_seeds[seed])
            npass = np.sum(mask)
            print("##### Npasses:", npass, "\n")

            trig_masks[seed] = mask.to_numpy()

        return trig_masks

    def make_table(self):
        """
        Function that prints to screen the rates table.
        Returns a list containing the csv-compatible table.
        """
        table = []
        table.append("Seed,NPass,Eff,Rate\n")
        total_mask = 0
        trig_masks = self.prepare_masks()
        self.trig_masks = trig_masks

        for seed, mask in trig_masks.items():
            total_mask = total_mask | mask
            npass = np.sum(mask)
            eff = npass / len(mask)
            rate = eff * 2760 * 11246 / 1e3
            table.append(f"{seed},{npass},{eff},{rate}\n")
            print(seed.ljust(50), ":\t%8i\t%.5f\t%.1f" % (npass, eff, rate))

        ## total
        npass = np.sum(total_mask)
        eff = npass / len(total_mask)
        rate = eff * 2760 * 11246 / 1e3

        tot_str = "Total:".ljust(50) + "\t%8i\t%.5f\t%.1f" % (npass, eff, rate)
        table.append(f"Total,{npass},{eff},{rate}\n")
        table.append(f"Total nev,{len(total_mask)},,\n")
        print((len(tot_str) + 5) * "-")
        print(tot_str)

        print("Total nev: %i" % len(total_mask))

        return table

    def dump_masks(self):
        """
        Function that dumps to file the masks produced by `prepare_masks`.
        """
        if hasattr(self, "trig_masks"):
            os.makedirs(f"{self.table_outdir}", exist_ok=True)
            fname = (
                f"{self.table_outdir}/{self.table_fname}_{self.version}_masks.parquet"
            )
            print(f"Dumping masks to parquet in: {fname}")

            ak.to_parquet(ak.zip(self.trig_masks), fname)
        else:
            print("No masks created! Run `prepare_masks` first.")

    def dump_table(self, table):
        """
        Function that dumps to file the table produced by `make_table`.
        """
        os.makedirs(f"{self.table_outdir}", exist_ok=True)
        f = open(f"{self.table_outdir}/{self.table_fname}_{self.version}.csv", "w")
        for line in table:
            f.write(line)
        f.close()
