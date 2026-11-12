cp configs/V47nano_151pre3/objects/jets.yaml configs/V49nano_151pre3/objects/jets.yaml
cp configs/V47nano_L1EGupdate2/objects/jets.yaml configs/V49nano_L1EGupdate2/objects/jets.yaml

cp configs/V47nano_151pre3/object_performance/jets_trigger.yaml configs/V49nano_151pre3/object_performance/jets_trigger.yaml
cp configs/V47nano_L1EGupdate2/object_performance/jets_trigger.yaml configs/V49nano_L1EGupdate2/object_performance/jets_trigger.yaml

cp configs/V47nano_151pre3/rate_plots/jets.yaml configs/V49nano_151pre3/rate_plots/jets.yaml
cp configs/V47nano_L1EGupdate2/rate_plots/jets.yaml configs/V49nano_L1EGupdate2/rate_plots/jets.yaml

grep -rl "V47nano" configs/V49nano_151pre3 | xargs sed -i 's/V47nano/V49nano/g'
grep -rl "V47nano" configs/V49nano_L1EGupdate2 | xargs sed -i 's/V47nano/V49nano/g'
