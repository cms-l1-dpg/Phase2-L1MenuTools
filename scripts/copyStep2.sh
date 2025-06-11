VERSION=$1

cp configs/V44nano/rate_table/step2_cfg.yml configs/$VERSION/rate_table/.
cp configs/V44nano/rate_table/step2_menu_cfg.yml configs/$VERSION/rate_table/.
cp configs/V44nano/object_performance/jets_ext_trigger.yaml configs/$VERSION/object_performance/.
cp configs/V44nano/rate_plots/jets_sc8.yaml configs/$VERSION/rate_plots/.

grep -rl "V44nano" configs/$VERSION/object_performance | xargs sed -i "s/V44nano/$VERSION/g"
grep -rl "V44nano" configs/$VERSION/rate_plots | xargs sed -i "s/V44nano/$VERSION/g"
grep -rl "V44nano" configs/$VERSION/rate_table | xargs sed -i "s/V44nano/$VERSION/g"
grep -rl "v44_" configs/$VERSION/rate_table | xargs sed -i "s/v44_/v45_/g"

object_performance configs/$VERSION/object_performance/jets_sc8_trigger.yaml
object_performance configs/$VERSION/object_performance/jets_ext_trigger.yaml
rate_table configs/$VERSION/rate_table/step2_cfg.yml
rate_plots configs/$VERSION/rate_plots/jets_sc8.yaml

