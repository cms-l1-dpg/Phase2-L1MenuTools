from datetime import timedelta
import glob
import operator
import time
from typing import Union
import warnings

import numpy as np
from scipy.stats import beta, norm
import uproot


def str_to_op(x: str):
    op_map = {
        "<": operator.lt,
        "<=": operator.le,
        "==": operator.eq,
        "!=": operator.ne,
        ">=": operator.ge,
        ">": operator.gt,
    }
    return op_map[x]


def clopper_pearson_err(x_hist, n_hist, alpha=1 - 0.68, warn="ignore"):
    yerr_lo = []
    yerr_hi = []
    with warnings.catch_warnings():
        warnings.simplefilter(warn)
        for x, n in zip(x_hist, n_hist):
            lo_bound = beta.ppf(alpha / 2, x, n - x + 1)
            yerr_lo.append(x / n - np.nan_to_num(lo_bound, nan=0.0))
            hi_bound = beta.ppf(1 - alpha / 2, x + 1, n - x)
            yerr_hi.append(np.nan_to_num(hi_bound, nan=1.0) - x / n)
    yerr = np.stack([yerr_lo, yerr_hi])
    return yerr


def get_pdg_id(particle: str):
    id_map = {
        "e": 11,
        "ele": 11,
        "electron": 11,
        "mu": 13,
        "muon": 13,
        "tau": 15,
        "photon": 22,
        "gamma": 22,
    }
    return id_map[particle.lower()]


def get_branches(ntuple_path: str, tree: str, obj: str):
    """
    Returns all branches that match the specified object
    in the given NTuple.
    """
    ntuple = glob.glob(ntuple_path)[0]
    with uproot.open(ntuple) as f:
        all_branches = f[tree].keys()
        if "GenTree" in tree:
            prefix = "Generator/"
        else:
            prefix = "L1PhaseII/"

    obj_branches = [x.removeprefix(prefix + obj) for x in all_branches if obj in x]

    return obj_branches


def scaling_func(x: Union[float, np.ndarray], a: float, b: float):
    if isinstance(x, np.ndarray):
        return a * x + b * np.ones_like(x)
    return a * x + b


def tanh(x: float, a: float, b: float):
    return 0.5 * np.tanh(a * x + b) + 0.5


def arctanh(x: float, a: float, b: float):
    return (np.arctanh(2 * x - 1) - b) / a


def errf(x: float, a: float, b: float, c: float, d: float, e: float):
    _cdf_front = norm.cdf(a * (x - b), 0, a * c)
    _exp_turnon = np.exp(-a * (x - b) + a * a * c * c / 2)
    _cdf_back = norm.cdf(a * (x - b), a * a * c * c, a * c) * (d - e) + e
    return _cdf_front - _exp_turnon * _cdf_back


##############
# Decorators #
##############


def ignore_warnings(func):
    def wrapper(*args, **kwargs):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return func(*args, **kwargs)

    return wrapper


def timer(task: str):
    def decorator(func):
        def wrapper(*args, **kwargs):
            print(f"{task} ...")
            t0 = time.time()
            result = func(*args, **kwargs)
            t1 = time.time()
            print(f"{task} completed in " f"{timedelta(seconds=round(t1 - t0, 0))}s")
            return result

        return wrapper

    return decorator
