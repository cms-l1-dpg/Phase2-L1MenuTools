regions="barrel endcap"

echo "Scaling for 90 GeV offline cut used for di-calo-tau seed"
for region in $regions; do
    echo "Region is: $region"
    python menu_tools/utils/scaling_extractor.py outputs/V49nano_AR25/object_performance/scalings L1caloTau --offline 90 --region $region
    echo
done

echo
echo

echo "Scaling for 52 GeV offline cut used for di-nnPuppi-tau seed"
for region in $regions; do
    echo "Region is: $region"
    python menu_tools/utils/scaling_extractor.py outputs/V49nano_AR25/object_performance/scalings L1nnPuppiTau --offline 52 --region $region
    echo
done
