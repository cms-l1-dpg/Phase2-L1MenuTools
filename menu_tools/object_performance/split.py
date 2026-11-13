"""`split_by`: efficiencies and resolutions split by categories of a reference field.

A plot entry with

    split_by:
      field: status                  # field of the reference object (after the prefix)
      categories:                    # name (legend label) -> values of the field
        "1-prong": [0]
        "1-prong + $\\pi^0$s": [1, 2]
        "3-prong": [10]
        "3-prong + $\\pi^0$": [11]
      name: DM                       # file-name tag (default: by_<field>; "": none)
      layout: per_object             # per_object (default) or per_category
      summary_range: [60, 150]       # x range of the integrated efficiencies in the
                                     # fractions JSON (default: the whole binning)

gives, in addition to the usual (inclusive) outputs, one plot per test object with the
inclusive curve and one curve per category (`per_object`), or one plot per category
with all test objects (`per_category`), and a JSON table of the category fractions. A
reference object in none of the categories ("other") is only in the inclusive curve.

Path efficiencies (path_efficiency.py) are per event: the category is that of the
reference object at `rank`, or, with `objects: n`, the combination of the categories of
the n leading reference objects, e.g. with the categories "1-prong" and "3-prong" and
`objects: 2` the event categories "1-prong + 1-prong", "1-prong + 3-prong" and
"3-prong + 3-prong" (`event_categories`, `assign_events`); events with fewer than n
reference objects, or with one of them in no category, are "other".
See docs/object-performance.md#split-by-reference-categories-split_by.
"""
import itertools
import re
from typing import Any, Optional

import awkward as ak
import numpy as np

from menu_tools.utils import utils

OTHER = "other"
LAYOUTS = ("per_object", "per_category")


class SplitConfig:
    """The `split_by` block of a plot config."""

    def __init__(self, cfg: dict[str, Any], plot_name: Optional[str] = None) -> None:
        where = f"split_by of {plot_name}"
        if not isinstance(cfg, dict) or "field" not in cfg:
            raise ValueError(f"{where}: needs `field` and `categories`")
        cats = cfg.get("categories")
        if not isinstance(cats, dict) or not cats:
            raise ValueError(f"{where}: `categories` must be a non-empty mapping")
        self.field: str = str(cfg["field"])
        self.categories: dict[str, list] = {}
        for name, values in cats.items():
            if name == OTHER:
                raise ValueError(f"{where}: category name `{OTHER}` is reserved")
            if not isinstance(values, (list, tuple)):
                values = [values]
            if not values:
                raise ValueError(f"{where}: category `{name}` has no values")
            self.categories[str(name)] = list(values)
        all_values = [v for vals in self.categories.values() for v in vals]
        if len(set(all_values)) != len(all_values):
            raise ValueError(f"{where}: categories must not share values")
        self.name: str = str(cfg.get("name", f"by_{self.field}"))
        self.layout: str = str(cfg.get("layout", "per_object"))
        if self.layout not in LAYOUTS:
            raise ValueError(f"{where}: layout must be one of {LAYOUTS}")
        objects = cfg.get("objects")
        if objects is not None and (
            isinstance(objects, bool) or not isinstance(objects, int) or objects < 1
        ):
            raise ValueError(f"{where}: `objects` must be an integer >= 1")
        # path efficiency only: event category from the n leading reference objects
        self.objects: Optional[int] = objects
        rng = cfg.get("summary_range")
        self.summary_range: Optional[tuple[float, float]] = (
            (float(rng[0]), float(rng[1])) if rng is not None else None
        )

    @property
    def tag(self) -> str:
        """File-name tag: `_<name>`, empty for `name: ""`."""
        return f"_{self.name}" if self.name else ""

    def masks(self, values) -> dict[str, Any]:
        """Category name -> boolean mask (same structure as `values`)."""
        out = {}
        for name, cat_values in self.categories.items():
            mask = ak.zeros_like(values, dtype=bool)
            for v in cat_values:
                mask = mask | (values == v)
            out[name] = mask
        return out

    def assign(self, values: np.ndarray) -> np.ndarray:
        """Flat values -> category name per entry (`OTHER` if in none)."""
        values = np.asarray(values)
        out = np.full(len(values), OTHER, dtype=object)
        for name, cat_values in self.categories.items():
            out[np.isin(values, cat_values)] = name
        return out


def event_categories(split: SplitConfig) -> list[str]:
    """Names of the event categories: the categories (`objects` unset or 1), or the
    unordered combinations of `objects` categories in declaration order, joined by
    " + "."""
    n = split.objects or 1
    if n == 1:
        return list(split.categories)
    return [
        " + ".join(c)
        for c in itertools.combinations_with_replacement(split.categories, n)
    ]


def assign_events(split: SplitConfig, values, n: int = 1) -> np.ndarray:
    """Event category per event from `values`, the split field of the reference objects
    per event (jagged, leading first): the combination of the categories of the first
    `n` objects (`event_categories`). `OTHER` for events with fewer than `n` objects or
    with one of them in no category."""
    names = list(split.categories)
    counts = ak.to_numpy(ak.num(values, axis=1))
    padded = ak.to_numpy(ak.fill_none(ak.pad_none(values, n, clip=True), np.nan))
    padded = np.asarray(padded, dtype=float).reshape(len(counts), n)
    # category index per object, len(names) for "other" / missing
    idx = np.full(padded.shape, len(names), dtype=int)
    for i, cat_values in enumerate(split.categories.values()):
        idx[np.isin(padded, np.asarray(cat_values, dtype=float))] = i
    idx.sort(axis=1)
    out = np.full(len(counts), OTHER, dtype=object)
    ok = (counts >= n) & (idx[:, -1] < len(names))
    for row in np.unique(idx[ok], axis=0):
        sel = ok & np.all(idx == row, axis=1)
        out[sel] = " + ".join(names[i] for i in row)
    return out


def safe_name(key: str) -> str:
    """A curve key or category name as a file-name part (e.g. `hltHpsPFTau:default`
    -> `hltHpsPFTau-default`, `1-prong + $\\pi^0$s` -> `1-prong_pi0s`)."""
    key = re.sub(r"[\\${}^]", "", key.replace(":", "-"))
    return re.sub(r"[^A-Za-z0-9.\-]+", "_", key).strip("_")


def category_counts(values: np.ndarray, split: SplitConfig) -> dict[str, Any]:
    """Counts and fractions of the categories (and `other`) in the flat `values`."""
    names = split.assign(values)
    n = int(len(names))
    out: dict[str, Any] = {"n": n, "categories": {}}
    for cat in list(split.categories) + [OTHER]:
        k = int(np.sum(names == cat))
        out["categories"][cat] = {"n": k, "fraction": k / n if n else None}
    return out


def integrated_efficiency(
    num_hist: np.ndarray,
    den_hist: np.ndarray,
    bins: np.ndarray,
    x_range: Optional[tuple[float, float]] = None,
) -> dict[str, Any]:
    """Numerator / denominator summed over the bins whose centre is in `x_range`.

    Clopper-Pearson (68%) errors.
    """
    centres = 0.5 * (bins[1:] + bins[:-1])
    sel = np.ones(len(centres), dtype=bool)
    if x_range is not None:
        sel = (centres >= x_range[0]) & (centres <= x_range[1])
    k = int(np.sum(np.asarray(num_hist)[sel]))
    n = int(np.sum(np.asarray(den_hist)[sel]))
    if n == 0:
        return {"n_num": k, "n_den": n, "efficiency": None, "err": [None, None]}
    err = utils.clopper_pearson_err([k], [n])
    return {
        "n_num": k,
        "n_den": n,
        "efficiency": k / n,
        "err": [float(err[0][0]), float(err[1][0])],
    }
