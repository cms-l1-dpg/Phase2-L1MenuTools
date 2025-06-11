VERSION=$1
RERUN=$2

cp configs/V49nano_151pre3/rate_table/step2_cfg.yml configs/$VERSION/rate_table/.
cp configs/V49nano_151pre3/rate_table/step2_menu_cfg.yml configs/$VERSION/rate_table/.
cp configs/V49nano_151pre3/object_performance/jets_ext_trigger.yaml configs/$VERSION/object_performance/.
cp configs/V49nano_151pre3/object_performance/jets_sc8_trigger.yaml configs/$VERSION/object_performance/.
cp configs/V49nano_151pre3/rate_plots/jets_sc8.yaml configs/$VERSION/rate_plots/.

grep -rl "V49nano_151pre3" configs/$VERSION/object_performance | xargs sed -i "s/V49nano_151pre3/$VERSION/g"
grep -rl "V49nano_151pre3" configs/$VERSION/rate_plots | xargs sed -i "s/V49nano_151pre3/$VERSION/g"
grep -rl "V49nano_151pre3" configs/$VERSION/rate_table | xargs sed -i "s/V49nano_151pre3/$VERSION/g"

if [[ $RERUN == "TRUE" ]]; then
    object_performance configs/$VERSION/object_performance/jets_sc8_trigger.yaml
    object_performance configs/$VERSION/object_performance/jets_ext_trigger.yaml
    rate_table configs/$VERSION/rate_table/step2_cfg.yml
    rate_plots configs/$VERSION/rate_plots/jets_sc8.yaml
fi

