"""Sample labels of the performance plots.

Every performance plot shows the sample it was made on as its legend title, or as the
first line of it when the plot already has a legend title (e.g. the reference label):
"HH$\\rightarrow$bb$\\tau\\tau$ — Gen visible taus" if that fits on one line, else on
two lines. The labels come from `sample_labels.yaml` (next to this module), keyed by the
`sample:` of the plot config, with the raw key as fallback. Per plot entry:

    sample_label: "DY$\\rightarrow\\ell\\ell$, $m_{\\ell\\ell}$ > 50 GeV"  # override
    sample_label: false                                     # no sample label

The label only changes the figures: the JSON outputs are unchanged.
"""
import functools
import os
import re
from typing import Any, Optional

import yaml

SAMPLE_LABELS_FILE = os.path.join(os.path.dirname(__file__), "sample_labels.yaml")

# Legend titles longer than this (visible characters) are wrapped.
TITLE_WIDTH = 36
SEPARATOR = " — "

# A word of a title: a run of non-space characters, mathtext ($...$, spaces allowed
# inside) kept whole.
_WORD = re.compile(r"(?:\$[^$]*\$|[^\s$])+|\$")


@functools.lru_cache(maxsize=None)
def sample_labels() -> dict[str, str]:
    """The sample key -> label map of `sample_labels.yaml`."""
    with open(SAMPLE_LABELS_FILE) as f:
        labels = yaml.safe_load(f) or {}
    return {str(k): str(v) for k, v in labels.items()}


def pretty_sample(sample: str) -> str:
    """Label of the sample key `sample` (the key itself if it has no label)."""
    return sample_labels().get(sample, sample)


def resolve_sample_label(cfg: dict[str, Any]) -> Optional[str]:
    """Sample label of a plot config entry, None if there is none to show.

    `sample_label` (a string) overrides the label of `sample`; `sample_label: false`
    (or an empty string) turns it off; `true` / absent: the label of `sample`.
    """
    override = cfg.get("sample_label", True)
    if override is False or override is None or override == "":
        return None
    if override is not True:
        if not isinstance(override, str):
            raise ValueError(
                f"sample_label must be a string or false, got {override!r}"
            )
        return override
    sample = cfg.get("sample")
    if not sample:
        return None
    return pretty_sample(str(sample))


def visible_length(text: str) -> int:
    """Approximate number of characters `text` renders to: mathtext commands
    (`\\rightarrow`) count as one, `$`, braces, `^` and `_` as none."""
    text = re.sub(r"\\[A-Za-z]+\s*", "x", text)
    text = re.sub(r"\\(.)", r"\1", text)
    return len(re.sub(r"[${}^_]", "", text))


def wrap_title(text: str, width: int = TITLE_WIDTH) -> str:
    """`text` wrapped at spaces into lines of at most ~`width` visible characters;
    mathtext ($...$) is never split. Existing line breaks are kept."""
    out = []
    for paragraph in text.split("\n"):
        lines: list[str] = []
        for word in _WORD.findall(paragraph):
            if lines and visible_length(f"{lines[-1]} {word}") <= width:
                lines[-1] = f"{lines[-1]} {word}"
            else:
                lines.append(word)
        out.append("\n".join(lines))
    return "\n".join(out)


def legend_title(
    sample_label: Optional[str],
    title: Optional[str] = None,
    width: int = TITLE_WIDTH,
) -> Optional[str]:
    """Legend title with the sample label first: "<sample> — <title>" if that fits in
    `width`, else the sample label on its own line(s) above the (wrapped) title. None
    if both are empty."""
    parts = [p for p in (sample_label, title) if p]
    if not parts:
        return None
    if len(parts) == 2 and "\n" not in parts[1]:
        joined = SEPARATOR.join(parts)
        if visible_length(joined) <= width:
            return joined
    return "\n".join(wrap_title(p, width) for p in parts)
