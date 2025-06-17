VERSION=$1
RERUN=$2

BASE=V45nano_151pre3_SC8Nano

cp configs/$BASE/object_performance/jets_trigger.yaml configs/$VERSION/object_performance/.
cp configs/$BASE/object_performance/jets_sc8_trigger.yaml configs/$VERSION/object_performance/.
cp configs/$BASE/object_performance/jets_ext_trigger.yaml configs/$VERSION/object_performance/.
cp configs/$BASE/object_performance/jets_matching.yaml configs/$VERSION/object_performance/.
cp configs/$BASE/object_performance/jets_matching_eta.yaml configs/$VERSION/object_performance/.
cp configs/$BASE/object_performance/jets_matching_wBTag.yaml configs/$VERSION/object_performance/.
cp configs/$BASE/object_performance/jets_matching_wCTag.yaml configs/$VERSION/object_performance/.
cp configs/$BASE/object_performance/jets_matching_wLightTag.yaml configs/$VERSION/object_performance/.
cp configs/$BASE/object_performance/jets_matching_wGTag.yaml configs/$VERSION/object_performance/.
cp configs/$BASE/object_performance/jets_sc8_matching.yaml configs/$VERSION/object_performance/.
cp configs/$BASE/object_performance/jets_sc8_matching_eta.yaml configs/$VERSION/object_performance/.
cp configs/$BASE/objects/jets.yaml configs/$VERSION/objects/.
cp configs/$BASE/rate_plots/jets.yaml configs/$VERSION/rate_plots/.
cp configs/$BASE/rate_table/step2_cfg.yml configs/$VERSION/rate_table/.
cp configs/$BASE/rate_table/step2_menu_cfg.yml configs/$VERSION/rate_table/.

grep -rl "$BASE" configs/$VERSION/object_performance | xargs sed -i "s/$BASE/$VERSION/g"
grep -rl "$BASE" configs/$VERSION/rate_plots | xargs sed -i "s/$BASE/$VERSION/g"
grep -rl "$BASE" configs/$VERSION/rate_table | xargs sed -i "s/$BASE/$VERSION/g"

if [[ $RERUN == "TRUE" ]]; then
    object_performance configs/$VERSION/object_performance/jets_matching.yaml
    object_performance configs/$VERSION/object_performance/jets_matching_eta.yaml
    object_performance configs/$VERSION/object_performance/jets_sc8_matching.yaml
    object_performance configs/$VERSION/object_performance/jets_sc8_matching_eta.yaml
    object_performance configs/$VERSION/object_performance/jets_matching_wBTag.yaml
    object_performance configs/$VERSION/object_performance/jets_matching_wCTag.yaml
    object_performance configs/$VERSION/object_performance/jets_matching_wLightTag.yaml
    object_performance configs/$VERSION/object_performance/jets_matching_wGTag.yaml
    object_performance configs/$VERSION/object_performance/jets_trigger.yaml
    object_performance configs/$VERSION/object_performance/jets_sc8_trigger.yaml
    object_performance configs/$VERSION/object_performance/jets_ext_trigger.yaml
    object_performance configs/$VERSION/object_performance/met_ht_mht.yaml
    rate_table configs/$VERSION/rate_table/step2_cfg.yml
    rate_plots configs/$VERSION/rate_plots/jets.yaml
fi

