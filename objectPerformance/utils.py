import operator
import warnings

import numpy as np
from scipy.stats import beta


def str_to_op(x: str):
    op_map = {
        '<': operator.lt,
        '<=': operator.le,
        '==': operator.eq,
        '!=': operator.ne,
        '>=': operator.ge,
        '>': operator.gt,
    }
    return op_map[x]


def clopper_pearson_err(x_hist, n_hist, alpha=1-0.68, warn="ignore"):
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

