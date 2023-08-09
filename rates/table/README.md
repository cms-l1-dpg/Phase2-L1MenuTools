# L1 Phase2 Menu Tools: Rate Table

The rates table can be produced using the following command:

    ./rate_table.py cfg/v29/v29_cfg.yml

where the `cfg` argument specifies the structure of the config file to be used.

An example of config can be found in `./cfg/v29_cfg.yml` and it is a `yaml` file
with the following structure:

	MenuV29:
	  version: "V29"
	  sample: "/eos/cms/store/group/dpg_trigger/comm_trigger/L1Trigger/alobanov/phase2/menu/ntuples/13X/v29_RelVal/RelValTTbar_14TeV/RelVal_13X_TT_200PU_crab_v29_13X_RelVal_FixGenTree/230710_081407/L1NtuplePhaseII_Step1_hadd.root"
	  menu_config: "cfg/v29/v29_16Seeds_Final_clean_cfg.yml"
	  scalings:
	      scalings_path: "/eos/user/m/mbonanom/www/Postdoc/L1PhaseII/V29/scalings/"
	      collect_scalings: False
	      scalings_outdir: "scalings_input/V29/"
	      scalings_file: "scalings.yml"
	  table:
	      table_fname: "rates_16Seeds_Final"
	      table_outdir: "rates_tables/V29"

The block above defines entirely a menu table (`MenuV29` in the example above).
Several blocks (with a different title) can be specified in the config if one wants to produce
rate tables for different menu configurations.

The other fields that can be specified are:
* `version`: specifies the version of the ntuples used;
* `sample`: specifies the sample to be used;
* `menu_config`: user-defined config of the menu seeds. See `cfg/v29/v29_16Seeds_Final_clean_cfg.yml` for an example. The current example replicates the menu config implemented in `cfg/v29/v29_16Seeds_Final`;
* `scalings`: this block defines the properties of the scalings file to be used. If `collect_scalings` is `False`,
the scalings file in `scalings_outdir` will be used (`scalings.yml` in the example above corresponds to the `v29` scalings used for AR). If `collect_scalings` is `True`, then the `Scaler` (cf `scaler.py`) class is used to create a new scalings file, with the name specified in `scalings_file` (which will be located in `scalings_outdir`), starting from the per-object `.txt` scalings saved under `scalings_path` (i.e. the output of the `objectPerformance` code);
* `table`: this block defines the properties of the rates table that will be dumped to a `.csv` file. The table will be saved under `table_outdir` with `table_fname` as name.
