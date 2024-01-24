from scipy.optimize import curve_fit
import numpy as np

from menu_tools.object_performance.config import PerformancePlotConfig
from menu_tools.utils import utils


class ScalingCollection:
    """
    Collection of scaling values corresponding to one
    scaling plot. This requires the input of multiple
    turnon_collections, i.e. a single threshold but multiple
    objects.
    """

    def __init__(
        self, cfg: PerformancePlotConfig, method: str, plateau_pct: float = 0.95
    ):
        self.cfg = cfg
        self.method = method
        self.plateau_pct = plateau_pct
        self.scalings: dict[str, dict] = {x: {} for x in self.cfg["test_objects"]}
        self.fit_function_params = None

    def _find_percentage_point(self, hist, bins, scaling_pct):
        for i, eff in enumerate(hist[:-2]):
            is_point = (
                eff < scaling_pct
                and hist[i + 1] > scaling_pct
                and hist[i + 2] > scaling_pct
            )
            if is_point:
                return bins[i + 1]

    def _find_turnon_cut(self, graph_x, graph_y, Target):
        L = 0
        R = np.max(graph_x)

        while R - L > 0.0001:
            C = (L + R) / 2
            V = self._get_point_on_curve(C, graph_x, graph_y)

            if V < Target:
                L = C
            else:
                R = C

        return (R + L) / 2.0

    def _find_turnon_fit(self, function, popt, _min, _max, target):
        if (function(_min, *popt) > target) | (function(_max, *popt) < target):
            return -1000

        L = _min
        R = _max

        while R - L > 0.0001:
            C = (L + R) / 2
            V = function(C, *popt)

            if V < target:
                L = C
            else:
                R = C

        return (R + L) / 2

    @utils.ignore_warnings
    def _compute_value_of_tanh_at_threshold(self, efficiency, bins, threshold):
        xvals = np.array(bins)
        efficiency = np.array(efficiency)

        xvals = xvals[~np.isnan(efficiency)]
        efficiency = efficiency[~np.isnan(efficiency)]

        popt, pcov = curve_fit(utils.tanh, xvals, efficiency, p0=[1, 0])
        if np.inf in pcov:
            return None

        s_val = utils.arctanh(threshold, *list(popt))

        return s_val

    @utils.ignore_warnings
    def _compute_value_of_errf_at_threshold(self, efficiency, bins, scaling_pct):
        xvals = np.array(bins)
        efficiency = np.array(efficiency)

        xvals = xvals[~np.isnan(efficiency)]
        efficiency = efficiency[~np.isnan(efficiency)]

        popt, pcov = curve_fit(
            utils.errf, xvals, efficiency, p0=[0.02, 80, 20, 1, np.min(efficiency)]
        )

        s_val = self._find_turnon_fit(
            utils.errf,
            popt,
            np.min(xvals),
            np.max(xvals) * 10,
            scaling_pct * utils.errf(10000, *popt),
        )

        return s_val

    def _interpolate(self, H, K1, K2):
        A = np.ones(len(K1)) * (-K2)
        B = [k1i + 2 * K2 for k1i in K1]
        C = np.ones(len(K1)) * (-K2)
        D = []

        A[0] = 0
        C[-1] = 0

        D = [k1i * h1i for k1i, h1i in zip(K1, H)]

        D[0] = D[0] + K2 * 0
        D[-1] = D[-1] + K2 * 1

        for i in range(1, len(K1)):
            F = A[i] / B[i - 1]

            A[i] = A[i] - B[i - 1] * F
            B[i] = B[i] - C[i - 1] * F
            C[i] = C[i]
            D[i] = D[i] - D[i - 1] * F

        Y = np.ones(len(K1))
        Y[-1] = D[-1] / B[-1]

        for i in reversed(range(len(K1) - 2)):
            Y[i] = (D[i] - C[i] * Y[i + 1]) / B[i]

        return Y

    def _get_point_on_curve(self, x, graph_x, graph_y):
        if x < graph_x[0]:
            return 0

        if x >= graph_x[len(graph_x) - 1]:
            return 1

        xr = graph_x[0]
        yr = graph_y[0]
        for i in range(len(graph_x) - 1):
            xl = xr
            yl = yr
            xr = graph_x[i + 1]
            yr = graph_y[i + 1]
            if (x < xr) & (x >= xl):
                return yl + (yr - yl) / (xr - xl) * (x - xl)

        return -1

    def _compute_scalings_naive(
        self, turnon_collection, test_obj, scalings, scaling_pct
    ):
        bins = turnon_collection.bins
        bins = 0.5 * (bins[1:] + bins[:-1])
        threshold = turnon_collection.threshold

        for obj_key, gen_hist_trig in turnon_collection.hists.items():
            if (obj_key == "ref") | (obj_key != test_obj):
                continue
            efficiency, yerr = turnon_collection.get_efficiency(obj_key)

            xbins = bins
            xbins = xbins[~np.isnan(efficiency)]
            er_dn = yerr[0]
            er_up = yerr[1]
            er_dn = er_dn[~np.isnan(efficiency)]
            er_up = er_up[~np.isnan(efficiency)]
            efficiency = efficiency[~np.isnan(efficiency)]

            K1 = []
            for i in range(len(efficiency)):
                K1.append(1 / (er_dn[i] + er_up[i]) / (er_up[i] + er_dn[i]))

            percentage_point = self._find_turnon_cut(
                xbins, self._interpolate(efficiency, K1, 100), scaling_pct
            )
            if percentage_point:
                scalings[obj_key][threshold] = percentage_point

        return scalings

    def _compute_scalings_tanh(
        self, turnon_collection, test_obj, scalings, scaling_pct
    ):
        bins = turnon_collection.bins
        bins = 0.5 * (bins[1:] + bins[:-1])
        threshold = turnon_collection.threshold

        for obj_key, gen_hist_trig in turnon_collection.hists.items():
            if (obj_key == "ref") | (obj_key != test_obj):
                continue
            efficiency, _ = turnon_collection.get_efficiency(obj_key)
            percentage_point = self._compute_value_of_tanh_at_threshold(
                efficiency, bins, scaling_pct
            )
            if percentage_point:
                scalings[obj_key][threshold] = percentage_point

        return scalings

    def _compute_scalings_errf(
        self, turnon_collection, test_obj, scalings, scaling_pct
    ):
        bins = turnon_collection.bins
        bins = 0.5 * (bins[1:] + bins[:-1])
        threshold = turnon_collection.threshold

        for obj_key, gen_hist_trig in turnon_collection.hists.items():
            if (obj_key == "ref") | (obj_key != test_obj):
                continue
            efficiency, _ = turnon_collection.get_efficiency(obj_key)
            percentage_point = self._compute_value_of_errf_at_threshold(
                efficiency, bins, scaling_pct
            )
            if percentage_point:
                scalings[obj_key][threshold] = percentage_point

        return scalings

    def _compute_scalings(
        self, turnon_collection, test_obj, scalings, scaling_pct, method="tanh"
    ) -> dict:
        if method == "tanh":
            return self._compute_scalings_tanh(
                turnon_collection, test_obj, scalings, scaling_pct
            )
        if method == "errf":
            return self._compute_scalings_errf(
                turnon_collection, test_obj, scalings, scaling_pct
            )
        if method == "naive":
            return self._compute_scalings_naive(
                turnon_collection, test_obj, scalings, scaling_pct
            )
        else:
            raise ValueError(f"`{method}` is not a valid scaling method!")

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
