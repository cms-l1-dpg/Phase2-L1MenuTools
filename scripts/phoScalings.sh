regions="barrel endcap"

echo "Scaling for 12pT offline cut used for double iso photon seed"
for region in $regions; do
    echo "Region is: $region"
    python menu_tools/utils/scaling_extractor.py outputs/V49nano_AR25/object_performance/scalings L1tkPhoton --id Iso --offline 12 --region $region
done

echo
echo

# echo "Scaling for 230pT offline cut used for single-wide-jet seed"
# for region in $regions; do
#     echo "Region is: $region"
#     python menu_tools/utils/scaling_extractor.py outputs/V49nano_AR25/object_performance/scalings L1puppiJetSC8 --offline 230 --region $region
# done
