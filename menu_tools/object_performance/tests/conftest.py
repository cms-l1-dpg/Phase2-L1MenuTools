import os

import matplotlib.pyplot as plt
import pytest


@pytest.fixture
def legend_titles(monkeypatch: pytest.MonkeyPatch) -> dict[str, list[str]]:
    """Records, per figure saved with `plt.savefig`, the file name (without extension)
    and the legend titles of all its axes (and the figure's suptitle, if any).

    Returns a dict {file name: [titles]}; a figure saved as .png and .pdf is one entry.
    """
    seen: dict[str, list[str]] = {}
    savefig = plt.savefig

    def recording_savefig(fname, *args, **kwargs):
        fig = plt.gcf()
        titles = [
            leg.get_title().get_text()
            for ax in fig.axes
            if (leg := ax.get_legend()) is not None
        ]
        suptitle = getattr(fig, "_suptitle", None)
        if suptitle is not None:
            titles.append(suptitle.get_text())
        seen[os.path.splitext(os.path.basename(str(fname)))[0]] = titles
        return savefig(fname, *args, **kwargs)

    monkeypatch.setattr(plt, "savefig", recording_savefig)
    return seen


@pytest.fixture
def configs_in_cwd(tmp_path, monkeypatch):
    """Runs the test in an empty directory with a `configs` symlink (object labels are
    read from configs/<version>/objects relative to the working directory)."""
    run = tmp_path / "run"
    run.mkdir()
    configs = os.path.join(os.path.dirname(__file__), "..", "..", "..", "configs")
    monkeypatch.chdir(run)
    os.symlink(os.path.abspath(configs), "configs")
    return run
