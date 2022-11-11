#!/afs/cern.ch/user/d/dhundhau/public/miniconda3/envs/py310/bin/python
from progress.bar import IncrementalBar
from scipy.optimize import curve_fit

from plot_config import PlotConfig
from turnon_collection import TurnOnCollection
import utils


class ScalingFunctions():
    """
    Scaling functions for a set of ScalingCollections.
    """

    def __init__(self, scalings):
        self.scalings = scalings

    def _fit_linear_functions(self):
        params = {}
        for obj, thresh_points in self.scalings.items():
            xdata = [th for th, val in thresh_points.items() if val]
            ydata = [thresh_points[x] for x in xdata]
            if not ydata:
                return None
            popt, pcov = curve_fit(utils.scaling_func, xdata, ydata)
            params[obj] = popt
        self.fit_function_params = params

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
    scaling plot. This requires the input of multiple
    turnon_collections, i.e. a single threshold but multiple
    objects.
    """

    def __init__(self,
                 cfg: PlotConfig,
                 method: str,
                 plateau_pct: float = 0.95):
        self.cfg = cfg
        self.method = method
        self.plateau_pct = plateau_pct
        self.scalings = {x: {} for x in self.cfg["test_objects"]}
        self.fit_function_params = None

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
                self.scalings[obj][threshold] = percentage_point

    def create_scalings(self):
        cfg_plot = self.cfg_plot

        thds = self._get_scaling_thresholds(cfg_plot)
        bar = IncrementalBar("Progress", max=len(thds))
        for threshold in thds:
            bar.next()
            turnon_collection = TurnOnCollection(cfg_plot, threshold)
            turnon_collection.create_hists()
            self._compute_scalings(turnon_collection)

        bar.finish()
        self._fit_linear_functions()


if __name__ == "__main__":
    pass
