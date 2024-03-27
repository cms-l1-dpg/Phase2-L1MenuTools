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
