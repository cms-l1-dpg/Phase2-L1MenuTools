#!/afs/cern.ch/user/d/dhundhau/public/miniconda3/envs/py310/bin/python

import os, yaml
from glob import glob

class Scaler:
    def __init__(self, path_to_scalings):
        self.dir = path_to_scalings
        self.fnames = glob(f"{self.dir}/*.txt")
        self.scaling_dict = {}
#         self.scaling_file = None

    def get_lines(self, fname):
        with open(fname) as f:
            lines = f.readlines()

        return lines

    def get_basename(self, fname):
        basename = os.path.basename(fname).replace(".txt","")
        basename = basename.replace(
            "Turnon","").replace(
            "Trigger","").replace(
            "Matching","").replace(
            "_","")

        return basename

    def eta_ranges(self, obj, suffix):
        eta_range = None
        if obj == "Muons":
            if suffix == "Barrel":
                eta_range = (0,0.83)
            elif suffix == "Overlap":
                eta_range = (0.83,1.24)
            elif suffix == "Endcap":
                eta_range = (1.24,2.5)
        else:
            if suffix == "Barrel":
                eta_range = (0,1.5)
            elif suffix == "Endcap":
                eta_range = (1.5,2.5)
            elif suffix == "Forward":
                eta_range = (2.5,5)
        
        return eta_range
                
    def get_eta_range(self, fname):

        basename = self.get_basename(fname)
        
        for suffix in ["Barrel","Endcap","Overlap"]:
            if suffix in basename:
                obj = basename.split(suffix)[0]
                eta_range = self.eta_ranges(obj, suffix)
                                        
                if eta_range is None:
                    print("Not found! ", basename, obj)
                else:
                    return obj, suffix, eta_range
                
        return None

    def decode_scaling(self, line):
        line = line.replace(" ","")
        items = line.split("::")

        obj = items[1][:-len("Scaling")]
        slope = float(items[2][len("args:=(offline);lambda:="):items[2].find("*off")-10])
        offset = float(items[2][items[2].find("*off")+len("*offline"):-10])

        return obj,slope,offset

    @property
    def collect_scalings(self):
        for fname in self.fnames:
            r = self.get_eta_range(os.path.basename(fname))

            if r is None: 
                print(30*"#", r)
                objcat = None
                region = None
                eta_range = (None,None)
            else:
                objcat,region,eta_range = r
            
            lines = self.get_lines(fname)
            
            for line in lines:
                obj,slope,offset = self.decode_scaling(line)
                d = { region : {
                        "eta_min" : eta_range[0],
                        "eta_max" : eta_range[1],
                        "offset" : offset,
                        "slope" : slope
                    }
                }

                if obj in self.scaling_dict: self.scaling_dict[obj].update(d)
                else: self.scaling_dict[obj] = d
    
    @property
    def dump_scalings(self):
        with open('scalings.yml', 'w') as outfile:
            yaml.dump(self.scaling_dict,
                      outfile,
                      default_flow_style=False)
