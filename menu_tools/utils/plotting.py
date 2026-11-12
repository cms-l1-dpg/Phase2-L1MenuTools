import re

import matplotlib.axes
import matplotlib.text


def add_watermark(
    ax: matplotlib.axes.Axes,
    text: str,
    fontsize: float = 20,
    min_fontsize: float = 14,
) -> matplotlib.text.Text:
    """Add a faint watermark below the axes that can never resize them.

    The text is excluded from `tight_layout`, so a long watermark no longer
    squeezes the plot area. It shrinks to fit between the axes' left edge
    and the x-axis label, down to `min_fontsize`, and beyond that wraps onto
    extra lines, breaking after underscores or spaces.

    Call this after `fig.tight_layout()`, since the available width depends
    on where the axes end up.
    """
    fig = ax.figure
    wm = ax.text(
        0,
        -0.07,
        text,
        color="grey",
        alpha=0.2,
        fontsize=fontsize,
        transform=ax.transAxes,
        va="top",
    )
    wm.set_in_layout(False)

    renderer = fig.canvas.get_renderer()
    ax_left = ax.get_window_extent(renderer).x0
    pad = 0.02 * fig.bbox.width
    # The watermark shares a row with the right-aligned x-axis label, so it
    # may only use the space left of that label (or up to the figure edge).
    right = fig.bbox.width
    xlabel = ax.xaxis.label
    if xlabel.get_text():
        right = min(right, xlabel.get_window_extent(renderer).x0)
    available = right - ax_left - pad

    def width() -> float:
        return wm.get_window_extent(renderer).width

    if width() <= available:
        return wm

    # 0.97: text width does not scale exactly linearly with font size.
    wm.set_fontsize(max(min_fontsize, 0.97 * fontsize * available / width()))
    if width() <= available:
        return wm

    # Still too long at the minimum size: wrap greedily at "_" or " ".
    tokens = re.findall(r"[^_ ]+[_ ]?|[_ ]", text)
    lines = [""]
    for token in tokens:
        wm.set_text(lines[-1] + token)
        if lines[-1] and width() > available:
            lines.append(token)
        else:
            lines[-1] += token
    wm.set_text("\n".join(lines))
    return wm
