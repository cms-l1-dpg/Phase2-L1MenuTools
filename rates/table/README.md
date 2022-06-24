# Rate table for the Phase-2 L1 Trigger Menu 
To run the rate table, for example for the L1 TDR results, do
```
python run.py cfg/v10_TRIDAS_newThresholds_LHCCReview
```

For the firmware-based emulators under 123x, utilise `FBE_noMu_L1TDRMET_mhtSeed_123x` (`FBE_noMu_L1TDRMET_mhtSeed_123x_singleJetEta5` only includes forward region for the singleJet seed).
  
To display the rates in an easy-to-read format, run
```
python3 printRateTable.py -c cfg/v10_TRIDAS_newThresholds_LHCCReview -r out/2020-05-26-MENU-LHCCReview-BugFix_v10_TRIDAS_newThresholds_LHCCReview/thresholds/menu.csv
```
You can also edit the `CFG_RATE_COMBOS` dictionary at the top of
the file and run the script without any arguments `python3 printRateTable.py`.
This way multiple rate tables can be compared quickly. 

