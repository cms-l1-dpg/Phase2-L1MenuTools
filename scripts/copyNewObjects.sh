VERSION=$1
RERUN=$2

cp configs/V45nano_NewObjects/object_performance/jets_trigger.yaml configs/$VERSION/object_performance/.
cp configs/V45nano_NewObjects/object_performance/jets_sc8_trigger.yaml configs/$VERSION/object_performance/.
cp configs/V45nano_NewObjects/object_performance/jets_ext_trigger.yaml configs/$VERSION/object_performance/.
cp configs/V45nano_NewObjects/object_performance/jets_matching.yaml configs/$VERSION/object_performance/.
cp configs/V45nano_NewObjects/object_performance/jets_matching_eta.yaml configs/$VERSION/object_performance/.
cp configs/V45nano_NewObjects/object_performance/jets_matching_wBTag.yaml configs/$VERSION/object_performance/.
cp configs/V45nano_NewObjects/object_performance/jets_matching_wCTag.yaml configs/$VERSION/object_performance/.
cp configs/V45nano_NewObjects/object_performance/jets_matching_wLightTag.yaml configs/$VERSION/object_performance/.
cp configs/V45nano_NewObjects/object_performance/jets_matching_wGTag.yaml configs/$VERSION/object_performance/.
cp configs/V45nano_NewObjects/objects/jets.yaml configs/$VERSION/objects/.
cp configs/V45nano_NewObjects/rate_plots/jets.yaml configs/$VERSION/rate_plots/.
cp configs/V45nano_NewObjects/rate_table/step2_menu_cfg.yml configs/$VERSION/rate_table/.

grep -rl "V45nano_NewObjects" configs/$VERSION/object_performance | xargs sed -i "s/V45nano_NewObjects/$VERSION/g"
grep -rl "V45nano_NewObjects" configs/$VERSION/rate_plots | xargs sed -i "s/V45nano_NewObjects/$VERSION/g"
grep -rl "V45nano_NewObjects" configs/$VERSION/rate_table | xargs sed -i "s/V45nano_NewObjects/$VERSION/g"

if [[ $RERUN == "TRUE" ]]; then
    object_performance configs/$VERSION/object_performance/jets_matching.yaml
    object_performance configs/$VERSION/object_performance/jets_matching_eta.yaml
    object_performance configs/$VERSION/object_performance/jets_matching_wBTag.yaml
    object_performance configs/$VERSION/object_performance/jets_matching_wCTag.yaml
    object_performance configs/$VERSION/object_performance/jets_matching_wLightTag.yaml
    object_performance configs/$VERSION/object_performance/jets_matching_wGTag.yaml
    object_performance configs/$VERSION/object_performance/jets_trigger.yaml
    object_performance configs/$VERSION/object_performance/jets_sc8_trigger.yaml
    object_performance configs/$VERSION/object_performance/jets_ext_trigger.yaml
    # rate_table configs/$VERSION/rate_table/step2_cfg.yml
    rate_plots configs/$VERSION/rate_plots/jets.yaml
fi

