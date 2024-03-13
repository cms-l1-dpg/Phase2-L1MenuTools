from typing import Any, Optional
import re

import awkward as ak
import numpy as np
import vector

from menu_tools.object_performance.config import PerformancePlotConfig
from menu_tools.utils import utils
from menu_tools.utils.objects import Object


vector.register_awkward()


class ArrayLoader:
    def __init__(self, turnon_collection, cfg_plot: PerformancePlotConfig):
        self.turnon_collection = turnon_collection
        self.cfg_plot = cfg_plot

    def _transform_key(self, raw_key: str, obj: str):
        """
        This method serves to map the different
        NTuple branch names for quality and region
        to "quality"/"region".
        """
        ## nano
        if ("_" in raw_key) and ("dr_0" not in raw_key):
            key = raw_key.removeprefix(obj).split("_")[-1]
        ## menu ntuples
        else:
            key = raw_key.removeprefix(obj).lower()

        if "qual" in key:
            return "quality"
        else:
            return key

    def _load_array_from_parquet(self, obj: str):
        """
        Loads the specified parquet file
        into an ak array. The keys are
        transformed according to the logic
        in self._transform_key().
        """
        fname = (
            f"cache/{self.cfg_plot.version}/"
            f"{self.cfg_plot.version}_"
            f"{self.cfg_plot.sample}_"
            f"{obj}.parquet"
        )
        array = ak.from_parquet(fname)
        array_dict = {self._transform_key(key, obj): array[key] for key in array.fields}
        if self.cfg_plot.reference_trafo and not obj.startswith("L1"):
            array = ak.Array(array_dict)
        else:
            array = ak.zip(array_dict)
        return array

    def _load_ref_branches(self) -> None:
        """
        Load reference object.
        """
        ref_array = self._load_array_from_parquet(self.cfg_plot.reference_object)
        ref_array = ak.with_name(ref_array, "Momentum4D")
        self.turnon_collection.ak_arrays["ref"] = ref_array

    def _load_test_branches(self) -> None:
        """
        Load test objects.
        """
        for obj in self.cfg_plot.test_object_instances:
            test_array = self._load_array_from_parquet(obj.nano_obj_name)
            test_array = ak.with_name(test_array, "Momentum4D")
            self.turnon_collection.ak_arrays[str(obj)] = test_array

    def load_arrays(self) -> None:
        """
        Load ak arrays from cache (parquet) files.
        """
        self._load_ref_branches()
        self._load_test_branches()


class TurnOnCollection:
    def __init__(
        self, cfg_plot: dict, threshold: float, plot_name: Optional[str] = None
    ):
        self.cfg_plot = PerformancePlotConfig(cfg_plot, plot_name)
        self.version = self.cfg_plot.version
        self.threshold = threshold
        self.ak_arrays: dict[str, Any] = {}
        self.numerators: dict[str, Any] = {"ref": {}, "test": {}}
        self.hists: dict[str, Any] = {"ref": {}}

    @property
    def test_objects(self) -> list[tuple[Object, str]]:
        """Instantiates all test objects.

        Returns:
            obj_args: list containig tuples of test objects and their x_args.
        """
        obj_args = []

        test_objects = self.cfg_plot.test_objects
        for obj_key, x_arg in test_objects.items():
            obj = Object(obj_key, self.cfg_plot.version)
            if "L1" in obj_key:
                obj_args.append((obj, x_arg))
            else:
                obj_args.append((obj, x_arg.lower()))

        return obj_args

    @property
    def bins(self) -> np.ndarray:
        """
        Set bins according to configuration.
        """
        bin_width = self.cfg_plot.bin_width
        xmax = self.cfg_plot.bin_max + 1e-5
        xmin = self.cfg_plot.bin_min
        return np.arange(xmin, xmax, bin_width)

    def _load_arrays(self) -> None:
        """
        Load ak arrays from cache (parquet) files.
        """
        loader = ArrayLoader(self, self.cfg_plot)
        loader.load_arrays()

    def _match_test_to_ref(self):
        """
        Method for deltaR matching of test objects
        to reference objects.
        Selects highest pT deltaR-matched reco lepton.
        """
        for test_obj, x_arg in self.test_objects:
            ref_test = ak.cartesian(
                {"ref": self.ak_arrays["ref"], "test": self.ak_arrays[str(test_obj)]},
                nested=True,
            )
            js, gs = ak.unzip(ref_test)
            dR = gs.deltaR(js)

            pass_dR = dR < test_obj.match_dR
            pt_max = ak.argmax(ref_test["test"]["pt"][pass_dR], axis=-1, keepdims=True)
            if "iso" not in x_arg.lower():
                self.numerators["ref"][str(test_obj)] = ref_test["ref"][x_arg][pass_dR][
                    pt_max
                ][:, :, 0]
            self.numerators["test"][str(test_obj)] = ref_test["test"][x_arg][pass_dR][
                pt_max
            ][:, :, 0]

    def _flatten_array(self, ak_array, ak_to_np=False):
        """
        Returns a flattend array if the ak array is nested.
        If the ak array is already flat, the function returns
        the original array.
        """
        try:
            arr = ak.flatten(ak_array)
        except ValueError:
            arr = ak_array

        if ak_to_np:
            return ak.to_numpy(arr)
        return arr

    def _compute_MHT(self):
        """
        Returns MHT for the gen-level objects considered (typically jets).
        Cuts are not applied at this stage, as the `ak_array` passed to
        this function already has cuts applied in `apply_reference_cuts`.
        `_mht` is an `ak.Array()` with one entry (MHT) per event.
        """
        _px = self.ak_arrays["ref"].px
        _py = self.ak_arrays["ref"].py
        _mht = np.sqrt(
            ak.sum(_px[:, :], axis=-1, keepdims=True) ** 2
            + ak.sum(_py[:, :], axis=-1, keepdims=True) ** 2
        )
        return _mht

    def _reduce_to_per_event(self):
        """
        Reduces the test branches to a single number per event.
        This is needed to unify the structur of different MET objects
        for some of which one number per event is stored in the branches
        and for some of which one number per jet is stored.
        """
        for test_obj, x_arg in self.test_objects:
            try:
                self.ak_arrays[str(test_obj)][x_arg] = ak.max(
                    self.ak_arrays[str(test_obj)][x_arg], axis=1
                )
            except ValueError:
                pass

    def _apply_reference_trafo(self):
        """
        Transforms the reference branch, e.g.
        by summing over jetPt to get the HT
        reference object.
        """
        if not (trafo := self.cfg_plot.reference_trafo):
            return

        if trafo == "HT":
            self.ak_arrays["ref"]["HT"] = ak.sum(self.ak_arrays["ref"]["pt"], axis=-1)

        if trafo == "MHT":
            gen_mht = self._compute_MHT()
            self.ak_arrays["ref"]["MHT"] = gen_mht

        if trafo:
            self._reduce_to_per_event()

    def _select_highest_pt_ref_object(self):
        """
        The raw cached arrays of the reference still contain
        multiple objects per event. This function selects the
        highest object in pt and should be called after all the
        reference cuts are applied.
        """
        sel_pt = ak.argmax(self.ak_arrays["ref"]["pt"], axis=-1, keepdims=True)
        self.ak_arrays["ref"] = self.ak_arrays["ref"][sel_pt]

    def _apply_list_of_reference_cuts(self, cut_list):
        for cut in cut_list:
            cut = re.sub(r"{([^&|]*)}", r"self.ak_arrays['ref']['\1']", cut)
            sel = eval(cut)
            self.ak_arrays["ref"] = self.ak_arrays["ref"][sel]
        if not isinstance(
            self.ak_arrays["ref"], vector.backends.awkward.MomentumArray4D
        ):
            self.ak_arrays["ref"] = ak.with_name(self.ak_arrays["ref"], "Momentum4D")

    def _apply_reference_cuts(self) -> None:
        """Applies configured cuts on reference objects.

        Should be applied before any matching and before the
        selection of the highest pT object.
        """
        if "met" in self.cfg_plot.reference_object.lower():
            # TODO: Maybe we want to modify it and allow possible cuts on MET
            return

        ref_object_cuts = self.cfg_plot.reference_object_cuts
        self._apply_list_of_reference_cuts(ref_object_cuts)

        if self.cfg_plot.reference_trafo:
            # In this case each event is reduced to a single value already
            return None

        self._select_highest_pt_ref_object()
        ref_event_cuts = self.cfg_plot.reference_event_cuts
        self._apply_list_of_reference_cuts(ref_event_cuts)

    def _apply_test_obj_cuts(self):
        """Applies configured cuts on all configured test objects.

        Should be applied before any matching.
        """
        for test_obj, _ in self.test_objects:
            if not test_obj.cuts:
                continue
            ## add dummy eta
            if "eta" not in self.ak_arrays[str(test_obj)].fields:
                self.ak_arrays[str(test_obj)]["eta"] = 0
            for (
                range_i,
                range_cuts,
            ) in test_obj.cuts.items():  # TODO: use the version from utils
                for cut in range_cuts:
                    cut = re.sub(
                        r"{([^&|]*)}", r"self.ak_arrays[str(test_obj)]['\1']", cut
                    )
                    eta_sel = (
                        abs(self.ak_arrays[str(test_obj)]["eta"])
                        >= test_obj.eta_ranges[range_i][0]
                    ) & (
                        abs(self.ak_arrays[str(test_obj)]["eta"])
                        < test_obj.eta_ranges[range_i][1]
                    )

                    sel = eval(cut) + ~eta_sel
                    self.ak_arrays[str(test_obj)] = self.ak_arrays[str(test_obj)][sel]

    def _skim_to_hists(self) -> None:
        """
        TODO!
        """
        ref_field = self.cfg_plot.reference_field
        if trafo := self.cfg_plot.reference_trafo:
            ref_field = trafo

        for test_obj, x_arg in self.test_objects:
            sel = self.ak_arrays[str(test_obj)][x_arg] > self.threshold
            if (self.ak_arrays["ref"].ndim == 1) and (sel.ndim == 2):
                sel = sel[:, 0]
            ak_array = self._flatten_array(self.ak_arrays["ref"][ref_field][sel])
            self.hists[str(test_obj)] = np.histogram(ak_array, bins=self.bins)

            self.hists["ref"][str(test_obj)] = np.histogram(
                self._flatten_array(self.ak_arrays["ref"][ref_field]), bins=self.bins
            )

    def _remove_inner_nones_zeros(self, arr):
        sel_arr_not_none = ~ak.is_none(arr, axis=-1)
        sel_arr_not_zero = ak.num(arr) > 0
        sel = sel_arr_not_none & sel_arr_not_zero
        return arr[sel]

    def _skim_to_hists_dR_matched(self):
        ref_field = self.cfg_plot.reference_field

        ref_obj = self._remove_inner_nones_zeros(self.ak_arrays["ref"][ref_field])

        for test_obj, _ in self.test_objects:
            sel_threshold = self.numerators["test"][str(test_obj)] >= self.threshold
            numerator = self.numerators["ref"][str(test_obj)][sel_threshold]
            numerator = self._remove_inner_nones_zeros(numerator)
            numerator = self._flatten_array(numerator, ak_to_np=True)

            # Create Test Object(s) Numpy Histogram
            self.hists[str(test_obj)] = np.histogram(numerator, bins=self.bins)

            # Create Reference Numpy Histogram
            if self.threshold >= 0:
                ref_obj = self.numerators["ref"][str(test_obj)]
                ref_obj = self._remove_inner_nones_zeros(ref_obj)
            ref_flat_np = self._flatten_array(ref_obj, ak_to_np=True)
            self.hists["ref"][str(test_obj)] = np.histogram(ref_flat_np, bins=self.bins)

    def _skim_to_hists_dR_matched_Iso(self):
        for test_obj, _ in self.test_objects:
            numerator = self.numerators["test"][str(test_obj)]
            numerator = self._remove_inner_nones_zeros(numerator)
            numerator = self._flatten_array(numerator, ak_to_np=True)

            # Create Test Object(s) Numpy Histogram
            self.hists[str(test_obj)] = np.histogram(numerator, bins=self.bins)

    def xerr(self, obj: Object):
        ref_vals = self.hists["ref"][str(obj)][0]
        bin_width = self.cfg_plot.bin_width
        return np.ones_like(ref_vals) * bin_width / 2

    @utils.ignore_warnings
    def get_efficiency(self, obj: Object):
        ref_vals = self.hists["ref"][str(obj)][0]
        test_vals = self.hists[str(obj)][0]

        eff = test_vals / ref_vals
        assert all(0 <= i <= 1 or str(i) == "nan" for i in eff)

        err = utils.clopper_pearson_err(test_vals, ref_vals)

        return eff, err

    def _apply_cuts(self):
        # Apply cuts on test objects
        self._apply_test_obj_cuts()

        # Apply cuts on reference objects
        self._apply_reference_cuts()
        self._apply_reference_trafo()

    def create_hists(self):
        self._load_arrays()
        self._apply_cuts()
        if not self.cfg_plot.matching:
            self._skim_to_hists()
        else:
            self._match_test_to_ref()
            if self.cfg_plot.iso_vs_eff_plot:
                self._skim_to_hists_dR_matched_Iso()
            else:
                self._skim_to_hists_dR_matched()
