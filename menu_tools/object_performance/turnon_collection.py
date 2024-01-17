import re

import awkward as ak
import numpy as np
import vector

from menu_tools.object_performance.plot_config import PlotConfig
from menu_tools.object_performance.quality_obj import Quality, L1IsoCut
from menu_tools.utils import utils


vector.register_awkward()


class ArrayLoader():

    def __init__(self, turnon_collection):
        self.turnon_collection = turnon_collection

    def _transform_key(self, raw_key: str, obj: str):
        """
        This method serves to map the different
        NTuple branch names for quality and region
        to "quality"/"region".
        """
        key = raw_key.removeprefix(obj).lower()
        if "qual" in key:
            return "quality"
        else:
            return key

    def _map_region(self, test_array, obj: str):
        """
        This method serves to map a 'region' branch
        to the correct eta region in the detector.
        Needed from V25 after the barrel and endcap
        collections have been merged.
        """
        if 'hgc' in test_array.fields:
            test_array["region"] = (ak.where(abs(test_array["eta"]) > 1.479, 1, 0))

        return test_array

    def _load_array_from_parquet(self, obj: str):
        """
        Loads the specified parquet file
        into an ak array. The keys are
        transformed according to the logic
        in self._transform_key().
        """
        fname = (
            f"cache/{self.turnon_collection.cfg_plot.version_ref_object}/"
            f"{self.turnon_collection.cfg_plot.version_ref_object}_"
            f"{self.turnon_collection.cfg_plot.sample}_"
            f"{obj}.parquet"
        )
        array = ak.from_parquet(fname)
        array_dict = {
            self._transform_key(key, obj): array[key]
            for key in array.fields
        }
        if self.turnon_collection.cfg_plot.reference_trafo:
            array = ak.Array(array_dict)
        else:
            array = ak.zip(array_dict)
        return array

    def _load_ref_branches(self):
        """
        Load reference object.
        """
        ref_array = self._load_array_from_parquet(
            self.turnon_collection.cfg_plot.reference_object
        )
        ref_array = ak.with_name(ref_array, "Momentum4D")
        self.turnon_collection.ak_arrays["ref"] = ref_array

    def _load_test_branches(self):
        """
        Load test objects.
        """
        test_objects = self.turnon_collection.cfg_plot.test_objects
        for test_obj, obj_cfg in test_objects.items():
            obj_name = self.turnon_collection.cfg_plot.get_base_obj(test_obj)
            test_array = self._load_array_from_parquet(obj_name)
            test_array = ak.with_name(test_array, "Momentum4D")
            test_array = self._map_region(test_array, test_obj)
            self.turnon_collection.ak_arrays[test_obj] = test_array

    def load_arrays(self):
        """
        Load ak arrays from cache (parquet) files.
        """
        self._load_ref_branches()
        self._load_test_branches()


class TurnOnCollection():

    def __init__(self, cfg_plot, threshold):
        self.cfg_plot = PlotConfig(cfg_plot)
        self.version = self.cfg_plot.version_ref_object
        self.threshold = threshold
        self.ak_arrays = {}
        self.numerators = {"ref": {}, "test": {}}
        self.hists = {"ref": {}}

    @property
    def bins(self):
        """
        Set bins according to configuration.
        """
        bin_width = self.cfg_plot.bin_width
        xmax = self.cfg_plot.bin_max + 1e-5
        xmin = self.cfg_plot.bin_min
        return np.arange(xmin, xmax, bin_width)

    def _load_arrays(self):
        """
        Load ak arrays from cache (parquet) files.
        """
        loader = ArrayLoader(self)
        loader.load_arrays()

    def _match_test_to_ref(self):
        """
        Method for deltaR matching of test objects
        to reference objects.
        Selects highest pT deltaR-matched reco lepton.
        """
        for test_obj, obj_cfg in self.cfg_plot.test_objects.items():
            suffix = obj_cfg["suffix"].lower()
            ref_test = ak.cartesian(
                {"ref": self.ak_arrays["ref"],
                 "test": self.ak_arrays[test_obj]},
                nested=True
            )
            js, gs = ak.unzip(ref_test)
            dR = gs.deltaR(js)

            pass_dR = dR < self.cfg_plot.get_match_dR(test_obj)
            pt_max = ak.argmax(ref_test["test"]["pt"][pass_dR], axis=-1,
                               keepdims=True)
            if ("iso" not in suffix):
                self.numerators["ref"][test_obj] = ref_test["ref"][suffix][pass_dR][pt_max][:, :, 0]  # noqa
            self.numerators["test"][test_obj] = ref_test["test"][suffix][pass_dR][pt_max][:, :, 0]  # noqa

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
            ak.sum(_px[:, :], axis=-1, keepdims=True)**2
            + ak.sum(_py[:, :], axis=-1, keepdims=True)**2
        )
        return _mht

    def _reduce_to_per_event(self):
        """
        Reduces the test branches to a single number per event.
        This is needed to unify the structur of different MET objects
        for some of which one number per event is stored in the branches
        and for some of which one number per jet is stored.
        """
        for test_obj, cfg in self.cfg_plot.test_objects.items():
            field = cfg["suffix"].lower()
            try:
                self.ak_arrays[test_obj][field] = ak.max(
                    self.ak_arrays[test_obj][field],
                    axis=1
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
            self.ak_arrays["ref"]["HT"] = ak.sum(
                self.ak_arrays["ref"]["pt"],
                axis=-1
            )

        if trafo == "MHT":
            gen_mht = self._compute_MHT()
            self.ak_arrays["ref"]["MHT"] = gen_mht

        if trafo:
            self._reduce_to_per_event()

    def _apply_quality_cuts(self):
        """
        Function to implement quality criteria.
        Events not fulfilling L1 hardware quality
        criteria are filtered out.
        """
        for test_obj in self.cfg_plot.test_objects:
            if not (quality_id := self.cfg_plot.get_quality_id(test_obj)):
                return

            ## force quality bit to be int!
            self.ak_arrays[test_obj]["quality"] = ak.values_astype(self.ak_arrays[test_obj]["quality"], np.int32)

            quality = Quality(self.ak_arrays, test_obj)
            sel = ~getattr(quality, quality_id)
            self.ak_arrays[test_obj] = self.ak_arrays[test_obj][sel]

    def _apply_L1_isolation_cuts(self):
        """
        Function to implement isolation criteria.
        Events not fulfilling L1 Iso EE/BB quality
        criteria are filtered out.
        """
        for test_obj in self.cfg_plot.test_objects:
            iso_BB = self.cfg_plot.get_iso_BB(test_obj)
            iso_EE = self.cfg_plot.get_iso_EE(test_obj)
            l1_iso = self.cfg_plot.get_l1_iso(test_obj)

            if ((iso_BB == -1) & (iso_EE == -1)):
                continue

            isolation = L1IsoCut(self.ak_arrays, test_obj,
                                 iso_BB, iso_EE, l1_iso)
            sel = ~getattr(isolation, "ISO_EEBB")
            self.ak_arrays[test_obj] = self.ak_arrays[test_obj][sel]

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
            cut = re.sub(r"{([^&|]*)}",
                         r"self.ak_arrays['ref']['\1']",
                         cut)
            sel = eval(cut)
            self.ak_arrays["ref"] = self.ak_arrays["ref"][sel]

    def _apply_reference_cuts(self):
        """
        Applies configured cuts on reference objects. Should be
        applied before any matching and before the selection of
        the highest pT object.
        """
        if self.cfg_plot.reference_trafo:
            ref_object_cuts = self.cfg_plot.reference_object_cuts
            ref_event_cuts = self.cfg_plot.reference_event_cuts

            self._apply_list_of_reference_cuts(ref_object_cuts)
            return
        if "met" in self.cfg_plot.reference_object.lower():
            # TODO: Maybe we want to modify it and allow possible cuts on MET
            return

        ref_object_cuts = self.cfg_plot.reference_object_cuts
        ref_event_cuts = self.cfg_plot.reference_event_cuts

        self._apply_list_of_reference_cuts(ref_object_cuts)
        self._select_highest_pt_ref_object()
        self._apply_list_of_reference_cuts(ref_event_cuts)

    def _apply_test_obj_cuts(self):
        """
        Applies configured cuts on all configured
        test objects.
        Should be applied before any matching.
        """
        for test_obj in self.cfg_plot.test_objects:
            if not (cuts := self.cfg_plot.get_object_cuts(test_obj)):
                continue
            for cut in cuts:
                cut = re.sub(r"{([^&|]*)}",
                             r"self.ak_arrays[test_obj]['\1']",
                             cut)
                sel = eval(cut)
                self.ak_arrays[test_obj] = self.ak_arrays[test_obj][sel]

    def _skim_to_hists(self):
        ref_field = self.cfg_plot.reference_field
        if (trafo := self.cfg_plot.reference_trafo):
            ref_field = trafo

        for test_obj, cfg in self.cfg_plot.test_objects.items():
            field = cfg["suffix"].lower()
            sel = self.ak_arrays[test_obj][field] > self.threshold
            ak_array = self._flatten_array(
                self.ak_arrays["ref"][sel][ref_field]
            )
            self.hists[test_obj] = np.histogram(ak_array, bins=self.bins)

            self.hists["ref"][test_obj] = np.histogram(
                self._flatten_array(self.ak_arrays["ref"][ref_field]),
                bins=self.bins
            )

    def _remove_inner_nones_zeros(self, arr):
        sel_arr_not_none = ~ak.is_none(arr, axis=-1)
        sel_arr_not_zero = ak.num(arr) > 0
        sel = sel_arr_not_none & sel_arr_not_zero
        return arr[sel]

    def _skim_to_hists_dR_matched(self):
        ref_field = self.cfg_plot.reference_field

        ref_obj = self._remove_inner_nones_zeros(
            self.ak_arrays["ref"][ref_field]
        )

        for test_obj, cfg in self.cfg_plot.test_objects.items():
            sel_threshold = self.numerators["test"][test_obj] >= self.threshold
            numerator = self.numerators["ref"][test_obj][sel_threshold]
            numerator = self._remove_inner_nones_zeros(numerator)
            numerator = self._flatten_array(numerator, ak_to_np=True)

            # Create Test Object(s) Numpy Histogram
            self.hists[test_obj] = np.histogram(numerator, bins=self.bins)

            # Create Reference Numpy Histogram
            if self.threshold >= 0:
                ref_obj = self.numerators["ref"][test_obj]
                ref_obj = self._remove_inner_nones_zeros(ref_obj)
            ref_flat_np = self._flatten_array(ref_obj, ak_to_np=True)
            self.hists["ref"][test_obj] = np.histogram(ref_flat_np,
                                                       bins=self.bins)

    def _skim_to_hists_dR_matched_Iso(self):
        for test_obj, cfg in self.cfg_plot.test_objects.items():
            numerator = self.numerators["test"][test_obj]
            numerator = self._remove_inner_nones_zeros(numerator)
            numerator = self._flatten_array(numerator, ak_to_np=True)

            # Create Test Object(s) Numpy Histogram
            self.hists[test_obj] = np.histogram(numerator, bins=self.bins)

    def xerr(self, obj_key: str):
        ref_vals = self.hists["ref"][obj_key][0]
        bin_width = self.cfg_plot.bin_width
        return np.ones_like(ref_vals) * bin_width / 2

    @utils.ignore_warnings
    def get_efficiency(self, obj_key: str):
        ref_vals = self.hists["ref"][obj_key][0]
        test_vals = self.hists[obj_key][0]

        eff = test_vals / ref_vals
        assert all(0 <= i <= 1 or str(i) == "nan" for i in eff)

        err = utils.clopper_pearson_err(test_vals, ref_vals)

        return eff, err

    def _apply_cuts(self):
        # Apply cuts on reference objects
        self._apply_reference_cuts()
        self._apply_reference_trafo()
        # Apply cuts on test objects
        self._apply_quality_cuts()
        self._apply_L1_isolation_cuts()
        self._apply_test_obj_cuts()

    def create_hists(self):
        self._load_arrays()
        self._apply_cuts()
        if not self.cfg_plot.matching_configured:
            self._skim_to_hists()
        else:
            self._match_test_to_ref()
            if self.cfg_plot.iso_vs_eff_plot:
                self._skim_to_hists_dR_matched_Iso()
            else:
                self._skim_to_hists_dR_matched()
