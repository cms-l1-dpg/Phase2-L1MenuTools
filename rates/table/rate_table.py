#!/afs/cern.ch/user/d/dhundhau/public/miniconda3/envs/py310/bin/python
from scaler import Scaler
from menu import MenuConfigurator

path_to_scalings = "/eos/user/m/mbonanom/www/Postdoc/L1PhaseII/V29/scalings/"
scaler = Scaler(path_to_scalings)
scaler.collect_scalings
scaler.scaling_dict

menu_config = MenuConfigurator('scalings.yml', 'v29_WITHMUONS_Final_obj_dict.yml')
menu_config.make_table
