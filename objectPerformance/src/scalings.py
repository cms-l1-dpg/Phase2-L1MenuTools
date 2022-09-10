#!/afs/cern.ch/user/d/dhundhau/public/miniconda3/envs/py310/bin/python
import numpy as np
from scipy.optimize import curve_fit

from turnon_collection import TurnOnCollection
import utils


class ScalingFunctions():
    """
    Scaling functions for a set of ScalingCollections.
    """

    def __init__(self):
        pass

    def _fit_linear_functions(self, scalings):
        params = {}
        for obj, thresh_points in scalings.items():
            xdata = [th for th, val in thresh_points.items() if val]
            ydata = [thresh_points[x] for x in xdata]
            if not ydata:
                return None
            popt, pcov = curve_fit(utils.scaling_func, xdata, ydata)
            params[obj] = popt
        return params

    def _get_scaling_thresholds(self, cfg_plot):
        if any("Muon" in x for x in cfg_plot["test_objects"]):
            return self.scaling_thresholds["Muon"]
        if any("Elec" in x or "Photon" in x for x in cfg_plot["test_objects"]):
            return self.scaling_thresholds["EG"]
        if any("HT" in x or "MET" in x for x in cfg_plot["test_objects"]):
            return self.scaling_thresholds["HT"]
        if any("Tau" in x for x in cfg_plot["test_objects"]):
            return self.scaling_thresholds["Tau"]
        if any("Jet" in x for x in cfg_plot["test_objects"]):
            return self.scaling_thresholds["Jet"]
        raise RuntimeError(
            "Failed to find thresholds in cfg_scaling_thresholds!"
        )


class ScalingCollection():
    """
    Collection of scaling values corresponding to one
    turnon_collection, i.e. for a single threhold but multiple
    objects.
    """

    def __init__(self, turnon_collection, method, plateau_pct=0.95):
        self.turnon_collection = turnon_collection
        self.method = method
        self.plateau_pct = 0.95

    def _find_percentage_point_naive(self, hist, bins, scaling_pct):
        for i, eff in enumerate(hist[:-2]):
            is_point = (
                eff < scaling_pct
                and hist[i + 1] > scaling_pct
                and hist[i + 2] > scaling_pct
            )
            if is_point:
                return bins[i + 1]

    def _find_percentage_point_tanh(self, hist, bins, scaling_pct):
        return 1

    def _find_percentage_point(self, hist, bins):
        if self.cfg_plots["scaling_method"].lower() == "tanh":
            return self._find_percentage_point_tanh(hist, bins)
        else:
            return self._compute_scalings_naive(hist, bins)

    def _compute_scalings(self, turnon_collection, scalings,
                          scaling_pct) -> dict:
        bins = turnon_collection.bins
        threshold = turnon_collection.threshold

        for obj in turnon_collection.hists:
            if obj == "ref":
                continue
            efficiency, _ = turnon_collection.get_efficiency(obj)
            percentage_point = self._find_percentage_point(
                efficiency,
                bins,
                scaling_pct
            )
            if percentage_point:
                scalings[obj][threshold] = percentage_point

        return scalings


if __name__ == "__main__":
    pass

