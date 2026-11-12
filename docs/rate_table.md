# L1 Phase2 Menu Tools: Rate Table

The rates table can be produced using the following command:

    rate_table <path_to_config>.yml

where `<path_to_config>.yml` could be `configs/V29/rate_table/v29_cfg.yml`.
The config must contain the menu version and sample to be used as well as the path to the table
configuration. Additionally the file name of the output table is configurable,
but this is optional.

```yaml
version: "V29"
sample: "MinBias"
menu_config: "configs/V29/rate_table/v29_WITHMUONS_Final_clean_cfg.yml"
table_fname: "rates_full_Final"
```

For an example on how to construct the menu configuration file, see
`configs/V29/rate_table/v29_WITHMUONS_Final_clean_cfg.yml`.

The scalings for the objects in the menu table are applied automatically
and assume that the have been produced by running `object_performance`, which
saves them to `outputs/<version>/object_performance/scalings/`.

## LaTeX menu tables

`rate_table_tex` turns the CSVs written by `rate_table` into the LaTeX menu
table used for reviews and papers. Run it from the repository root on the same
config, with the same `--version`, as `rate_table`:

    rate_table_tex configs/V50nano/rate_table/step1p5_cfg.yml --version V50nano_170pre5 --png

This writes `v45_Step1p5Menu_V50nano_170pre5.tex`, `.pdf` and `.png` into
`outputs/V50nano_170pre5/rate_tables/`, next to the CSVs. Without options only
the `.tex` is written; `--compile` adds the `.pdf`, and `--png` adds a `.png`
cropped to the table (handy for web plot browsers; implies `--compile`, with
`--dpi` and `--no-crop` to adjust it). The PNG uses the first converter found
among `pdftoppm`, ghostscript, ImageMagick and PyMuPDF (`pip install pymupdf`).
`rate_table_tex --help` lists all options, grouped, with examples.

The `pdflatex` on `PATH` is used if it has all the packages the table needs;
otherwise the tool falls back to the TeX Live 2017 on cvmfs
(`/cvmfs/cms.cern.ch/external/tex/texlive/2017/bin/x86_64-linux`), which is
needed on lxplus, where the system TeX Live lacks `adjustbox`. Set
`RATE_TABLE_TEX_PDFLATEX=/path/to/pdflatex` to choose one explicitly.

### What goes into the table

* **The menu config.** Thresholds and the "additional requirements"
  (|η|, Δz, ΔR, Δη, invariant mass, charge, b-tag sum) are derived from the
  seed definitions and the object configs, so a retuned threshold needs no
  change to the layout. Thresholds that cut on the online `pt` instead of
  `offline_pt` are marked with † in the table.
* **A per-menu layout**, `<menu>_table_layout.yml` next to the menu config
  (or `table_layout:` in the rate table config, or `--layout`). It holds the
  title, section order, seed labels, rate columns and any overrides; see the
  docstring of `menu_tools/rate_table/latex_table.py` for all keys.
* **The rate CSVs.** By default the CSV is found from the config and
  `--version` (plus `--scalings`/`--signal`, as for `rate_table`). Rates for
  several pile-up scenarios go side by side: `pu_columns` in the layout lists
  them left to right, each with a suffix appended to `--version`, matching how
  separate PU runs are kept as their own versions. E.g.
  `{pu: 140, version_suffix: '_140PU'}` with `--version V50nano_170pre5` reads
  the CSV `rate_table` wrote for `--version V50nano_170pre5_140PU`, in
  `outputs/V50nano_170pre5_140PU/rate_tables/`. A missing extra CSV just drops
  that column; the output always goes next to the main CSV.

Other inputs: `--rates 140=a.csv --rates 200=b.csv` takes each column from an
explicit file, `--csv` sets the main CSV (the output then goes next to it), and
`--no-rates` renders the layout with empty rate columns, e.g. to check a new
layout. `-o` writes the `.tex` elsewhere, and `--body-only` writes just the
`table` environment for `\input` into another document (needs
`\usepackage{float}`, `adjustbox` and the macros from the generated preamble).

The object plateau column (the efficiency at which each object's turn-on
plateaus) and the "Total (+30%)" line are off by default; add `plateau` to
`columns` and set `total_rate_margin: 0.3` in the layout to show them.

### Layouts for new menus

    rate_table_tex configs/V50nano/rate_table/v0p0_cfg.yml --init \
        --inherit configs/V50nano/rate_table/step1p5_table_layout.yml

writes a skeleton layout and exits. Sections are taken from the comments above
each block of seeds in the menu config (e.g. `# Run 3 Pure Muons`), and
`--inherit` copies labels, overrides and sections from another layout for seeds
with the same name. The derived thresholds and requirements are written as
comments so they can be checked. `--title` sets the title and `--force`
overwrites an existing layout.

Seeds in the CSV but not in the layout still appear in the table, in a red
section at the end, and a warning is printed; seeds in the layout but not in
the menu are skipped. Cross masks that cannot be translated are reported and
left as `% NOTE` comments in the `.tex`, so set `requirements` for that seed
by hand.
