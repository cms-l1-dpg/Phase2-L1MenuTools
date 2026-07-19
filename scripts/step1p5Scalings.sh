regions="barrel endcap"
config="V50nano_170pre2"

#MUON

# thresholds="13 25 1 6 10 5 4"

# echo "Scaling for offline cuts used in muon seeds"
# for threshold in $thresholds; do
#     for region in $regions; do
# 	echo "Region is: $region, threshold is $threshold GeV"
# 	python menu_tools/utils/scaling_extractor.py outputs/V49nano_AR25/object_performance/scalings L1gmtTkMuon --offline $threshold --region $region
# 	echo
#     done
# done

# echo

## EGAMMA

# thresholds="42 18 14 30 15"

# echo "Scaling for offline cuts used in non-iso electron seeds"
# for threshold in $thresholds; do
#     for region in $regions; do
# 	echo "Region is: $region, threshold is $threshold GeV"
# 	python menu_tools/utils/scaling_extractor.py outputs/V49nano_AR25/object_performance/scalings L1tkElectron --id NoIso --offline $threshold --region $region
# 	echo
#     done
# done

# echo

# thresholds="35"

# echo "Scaling for offline cuts used in iso electron seeds"
# for threshold in $thresholds; do
#     for region in $regions; do
# 	echo "Region is: $region, threshold is $threshold GeV"
# 	python menu_tools/utils/scaling_extractor.py outputs/V49nano_AR25/object_performance/scalings L1tkElectron --id Iso --offline $threshold --region $region
# 	echo
#     done
# done

# echo

# thresholds="42 24 15"

# echo "Scaling for offline cuts used in iso electron seeds"
# for threshold in $thresholds; do
#     for region in $regions; do
# 	echo "Region is: $region, threshold is $threshold GeV"
# 	python menu_tools/utils/scaling_extractor.py outputs/V49nano_AR25/object_performance/scalings L1tkPhoton --id Iso --offline $threshold --region $region
# 	echo
#     done
# done

# echo

# thresholds="51 37 24"

# echo "Scaling for offline cuts used in standalone EG seeds"
# for threshold in $thresholds; do
#     for region in $regions; do
# 	echo "Region is: $region, threshold is $threshold GeV"
# 	python menu_tools/utils/scaling_extractor.py outputs/V49nano_AR25/object_performance/scalings L1EG --offline $threshold --region $region
# 	echo
#     done
# done

# echo

### TAU

# thresholds="153 92"

# echo "Scaling for offline cuts used in CaloTau seeds"
# for threshold in $thresholds; do
#     for region in $regions; do
# 	echo "Region is: $region, threshold is $threshold GeV"
# 	python menu_tools/utils/scaling_extractor.py outputs/V49nano_AR25/object_performance/scalings L1caloTau --offline $threshold --region $region
# 	echo
#     done
# done

# echo

# thresholds="58"

# echo "Scaling for offline cuts used in PUPPI Tau seeds"
# for threshold in $thresholds; do
#     for region in $regions; do
# 	echo "Region is: $region, threshold is $threshold GeV"
# 	python menu_tools/utils/scaling_extractor.py outputs/V49nano_AR25/object_performance/scalings L1nnPuppiTau --offline $threshold --region $region
# 	echo
#     done
# done

# echo

## JET HT

# thresholds="378"
# regions="inclusive"

# echo "Scaling for offline cuts used in HT sum seeds"
# for threshold in $thresholds; do
#     for region in $regions; do
# 	echo "Region is: $region, threshold is $threshold GeV"
# 	python menu_tools/utils/scaling_extractor.py outputs/V49nano_AR25/object_performance/scalings L1puppiJetSC4sums --id HT --offline $threshold --region $region
# 	echo
#     done
# done

# echo

# thresholds="228 78 160 198"
# regions="barrel endcap forwardHGC forwardHF"

# echo "Scaling for offline cuts used in jet seeds"
# for threshold in $thresholds; do
#     for region in $regions; do
# 	echo "Region is: $region, threshold is $threshold GeV"
# 	python menu_tools/utils/scaling_extractor.py outputs/V49nano_AR25/object_performance/scalings L1puppiJetSC4 --offline $threshold --region $region
# 	echo
#     done
# done

# echo

## MUON + EGAMMA

# thresholds="9"

# echo "Scaling for offline cuts used in muon seeds"
# for threshold in $thresholds; do
#     for region in $regions; do
# 	echo "Region is: $region, threshold is $threshold GeV"
# 	python menu_tools/utils/scaling_extractor.py outputs/V49nano_AR25/object_performance/scalings L1gmtTkMuon --offline $threshold --region $region
# 	echo
#     done
# done

# thresholds="24"

# echo "Scaling for offline cuts used in non-iso electron seeds"
# for threshold in $thresholds; do
#     for region in $regions; do
# 	echo "Region is: $region, threshold is $threshold GeV"
# 	python menu_tools/utils/scaling_extractor.py outputs/V49nano_AR25/object_performance/scalings L1tkElectron --id NoIso --offline $threshold --region $region
# 	echo
#     done
# done

thresholds="210"
regions="inclusive"

echo "Scaling for offline cuts used in HT sum seeds"
for threshold in $thresholds; do
    for region in $regions; do
	echo "Region is: $region, threshold is $threshold GeV"
	python menu_tools/utils/scaling_extractor.py outputs/V49nano_AR25/object_performance/scalings L1puppiMET --id default --offline $threshold --region $region
	echo
    done
done
