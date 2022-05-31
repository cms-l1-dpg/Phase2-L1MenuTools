To run the rates for firmware based emulators under 123x, do:

> python rates_emulator_123x.py --outdir testRates

This creates a file rates.py under directory testRates

To run the offline rate plots, do

> python ratePlots_validation123x.py --indir testRates --outdir "your own directory" --tag "here a tag for the plots" 

For online plots, add option --online.

For testing the rate plotting, just do

> 
> python ratePlots_validation123x.py --indir ratesEmu_123x_2 --outdir "your own directory" --tag "here a tag for the plots" 

The script ratePlots_L1TDR.py is used to compute the rates for L1 TDR results. This can be used to make a plot too, but personally I used this to fetch the rates (and saved them to rates_L1TDR/rates.py).
