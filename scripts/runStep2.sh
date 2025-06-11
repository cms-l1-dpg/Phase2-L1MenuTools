VERSION=$1

object_performance configs/$VERSION/object_performance/jets_sc8_trigger.yaml
object_performance configs/$VERSION/object_performance/jets_ext_trigger.yaml
rate_table configs/$VERSION/rate_table/step2_cfg.yml
rate_plots configs/$VERSION/rate_plots/jets_sc8.yaml

