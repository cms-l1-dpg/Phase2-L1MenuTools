regions="barrel endcap forwardHGC forwardHF"

echo "Scaling for 200pT offline cut used for di-wide-jet seed"
for region in $regions; do
    echo "Region is: $region"
    python menu_tools/utils/scaling_extractor.py outputs/V49nano_AR25/object_performance/scalings L1puppiJetSC8 --offline 200 --region $region
done

echo
echo

echo "Scaling for 230pT offline cut used for single-wide-jet seed"
for region in $regions; do
    echo "Region is: $region"
    python menu_tools/utils/scaling_extractor.py outputs/V49nano_AR25/object_performance/scalings L1puppiJetSC8 --offline 230 --region $region
done
