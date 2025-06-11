VERSION=$1

if [ -f outputs/$VERSION/object_performance/scalings/ElectronsTriggerBarrel_L1EG:default:barrel.yaml ]; then
   echo "Found separate electron L1EG scalings, now updating"
   # stash photon EG
   mv outputs/$VERSION/object_performance/scalings/L1EG:default:barrel.yaml outputs/$VERSION/object_performance/scalings/PhotonsTrigger_Barrel_L1EG:default:barrel.yaml
   mv outputs/$VERSION/object_performance/scalings/L1EG:default:endcap.yaml outputs/$VERSION/object_performance/scalings/PhotonsTrigger_Endcap_L1EG:default:endcap.yaml

   # move electrons
   mv outputs/$VERSION/object_performance/scalings/ElectronsTriggerBarrel_L1EG:default:barrel.yaml outputs/$VERSION/object_performance/scalings/L1EG:default:barrel.yaml
   mv outputs/$VERSION/object_performance/scalings/ElectronsTriggerEndcap_L1EG:default:endcap.yaml outputs/$VERSION/object_performance/scalings/L1EG:default:endcap.yaml

   # rerun EG rates and menu
   rate_plots configs/$VERSION/rate_plots/eg.yaml
   rate_table configs/$VERSION/rate_table/step1_cfg.yml
else
   echo "Separate electron L1EG scalings don't exist, please check"
fi
