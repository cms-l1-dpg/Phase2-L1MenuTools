import awkward as ak
import numpy as np
import vector

from plot_config import PlotConfig
from quality_obj import Quality
import utils


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
        # TODO: implement proper mapping for all objects
        elif "hgc" in key.lower():
            return "region"
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
            "cache/"
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
        # Load test objects
        for test_obj in self.turnon_collection.cfg_plot.test_objects:
            test_array = self._load_array_from_parquet(
                test_obj
            )
            test_array = ak.with_name(test_array, "Momentum4D")
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
        self.threshold = threshold
        self.bins = []
        self.ak_arrays = {}
        self.hists = {}
        self._set_bins()

    def _set_bins(self):
        """
        Set bins according to configuration.
        """
        bin_width = self.cfg_plot.bin_width
        xmax = self.cfg_plot.bin_max
        xmin = self.cfg_plot.bin_min
        self.bins = np.linspace(xmin, xmax, int((xmax - xmin) / bin_width))

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
            matched_obj = ref_test["test"][suffix][pass_dR][pt_max][:, :, 0]
            self.ak_arrays["ref"]["dR_matched_" + test_obj] = matched_obj

    def _flatten_array(self, ak_array):
        """
        Returns a flattend array if the ak array is nested.
        If the ak array is already flat, the function returns
        the original array.
        """
        try:
            return ak.flatten(ak_array)
        except ValueError:
            return ak_array

    def _compute_MHT(self):
        """
        Returns MHT for the gen-level objects considered (typically jets).
        Cuts are not applied at this stage, as the `ak_array` passed to
        this function already has cuts applied in `_apply_reference_cuts`.
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

            quality = Quality(self.ak_arrays, test_obj)
            sel = ~getattr(quality, quality_id)
            self.ak_arrays[test_obj] = self.ak_arrays[test_obj][sel]

    def _apply_reference_iso_cuts(self, ref_cuts):
        """
        Applies configured cuts on reference isolation.
        """
        try:
            dR = ref_cuts["isolation"]["dR"]
            threshold = ref_cuts["isolation"]["threshold"]
            sel = self.ak_arrays["ref"][f"iso{threshold}_dR{dR}"]
            self.ak_arrays["ref"] = self.ak_arrays["ref"][sel]
        except KeyError:
            pass

    def _select_highest_pt_ref_object(self):
        sel_pt = ak.argmax(self.ak_arrays["ref"]["Pt"], axis=-1, keepdims=True)
        self.ak_arrays["ref"] = self.ak_arrays["ref"][sel_pt]
        self.ak_arrays["ref"] = ak.fill_none(self.ak_arrays["ref"], -999)

    def _apply_reference_cuts(self):
        """
        Applies configured cuts on reference objects.
        Should be applied before any matching.
        """
        if not (ref_cuts := self.cfg_plot.reference_cuts):
            self._select_highest_pt_ref_object()
            return

        for branch, cut_cfg in ref_cuts.items():
            if branch == "isolation":
                continue
            op = utils.str_to_op(cut_cfg["operator"])
            threshold = cut_cfg["threshold"]
            sel = op(abs(self.ak_arrays["ref"][branch]), threshold)
            self.ak_arrays["ref"] = self.ak_arrays["ref"][sel]

        self._select_highest_pt_ref_object()
        self._apply_reference_iso_cuts(ref_cuts)

    def _apply_test_obj_cuts(self):
        """
        Applies configured cuts on all configured
        test objects.
        Should be applied before any matching.
        """
        for test_obj in self.cfg_plot.test_objects:
            cuts = self.cfg_plot.get_object_cuts(test_obj)
            if not cuts:
                continue
            for branch, cut_cfg in cuts.items():
                op = utils.str_to_op(cut_cfg["operator"])
                threshold = cut_cfg["threshold"]
                sel = op(abs(self.ak_arrays[test_obj][branch]), threshold)
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

        self.hists["ref"] = np.histogram(
            self._flatten_array(self.ak_arrays["ref"][ref_field]),
            bins=self.bins
        )

    def _skim_to_hists_dR_matched(self):
        ref_field = self.cfg_plot.reference_field
        for test_obj, cfg in self.cfg_plot.test_objects.items():

            test_vals = self.ak_arrays["ref"]["dR_matched_" + test_obj]
            sel_threshold = test_vals > self.threshold
            ak_array = self.ak_arrays["ref"][sel_threshold]

            # Drop None and empty arrays
            sel_none = ~ak.is_none(ak_array[ref_field], axis=-1)
            sel_empty = ak.num(ak_array[ref_field]) > 0
            ak_to_plot = ak_array[ref_field][sel_none & sel_empty]
            ak_array = self._flatten_array(ak_to_plot)
            self.hists[test_obj] = np.histogram(
                ak.to_numpy(ak_array, allow_missing=True),
                bins=self.bins
            )

        ref_flat_np = ak.to_numpy(
            self._flatten_array(
                self.ak_arrays["ref"][ref_field]
            )
        )

        self.hists["ref"] = np.histogram(
            ref_flat_np,
            bins=self.bins
        )

    @property
    def xerr(self):
        ref_vals = self.hists["ref"][0]
        bin_width = self.cfg_plot.bin_width
        return np.ones_like(ref_vals) * bin_width / 2

    def get_efficiency(self, obj_key: str):
        ref_vals = self.hists["ref"][0]
        test_vals = self.hists[obj_key][0]

        eff = np.nan_to_num(test_vals / ref_vals, posinf=0)
        assert all(0 <= i <= 1 for i in eff)

        err = utils.clopper_pearson_err(test_vals, ref_vals)

        return eff, err

    def create_hists(self):
        self._load_arrays()
        self._apply_quality_cuts()
        self._apply_reference_cuts()
        self._apply_reference_trafo()
        self._apply_test_obj_cuts()
        if not self.cfg_plot.match_dR:
            self._skim_to_hists()
        else:
            self._match_test_to_ref()
            self._skim_to_hists_dR_matched()

