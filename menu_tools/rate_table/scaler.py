import os, yaml
from glob import glob
from menu_config import MenuConfig


class Scaler:
    """
    Base class that takes as input the scalings computed
    in `objectPerformance` and aggregates all of them together
    to be used for the rates computation.
    """

    def __init__(self, cfg):
        self.cfg = MenuConfig(cfg)
        self.scalings_path = self.cfg.scalings_path
        self.scalings_file = self.cfg.scalings_file
        self.scalings_outdir = self.cfg.scalings_outdir
        self.do_scalings = self.cfg.do_scalings
        self.fnames = glob(f"{self.scalings_path}/*.txt")
        self.scaling_dict = {}
        self.init_log

    @property
    def init_log(self):
        print(
            f"::: The scalings file used is: {self.scalings_outdir}/{self.scalings_file} :::"
        )
        if (not os.path.isfile(f"{self.scalings_outdir}/{self.scalings_file}")) and (
            not self.do_scalings
        ):
            print(
                f"::: WARNING!! You are trying to use {self.scalings_outdir}/{self.scalings_file}, but the file does not exist! :::"
            )
            print(
                "::: WARNING!! Set do_scalings to True in config or specify a different location for the scalings file! :::"
            )
        if self.do_scalings:
            print(
                f"::: Will collect scalings from scratch and recreate {self.scalings_file} :::"
            )
            print(f"::: Will load scalings from {self.scalings_path} :::")
            print(f"::: Will dump scalings into {self.scalings_outdir} :::")

    def get_lines(self, fname):
        with open(fname) as f:
            lines = f.readlines()

        return lines

    def get_basename(self, fname):
        # TODO: Harmonize the naming of the scaligns in `objectPerformance`
        # so that we can drop this function.
        basename = os.path.basename(fname).replace(".txt", "")
        basename = (
            basename.replace("Turnon", "").replace("Trigger", "").replace("_", "")
        )

        return basename

    def eta_ranges(self, obj, suffix):
        """
        Wrapper function that defines the Barrel/Overlap/Endcap
        range definitions for different objects.
        """
        eta_range = None
        if obj == "Muons":
            if suffix == "Barrel":
                eta_range = (0, 0.83)
            elif suffix == "Overlap":
                eta_range = (0.83, 1.24)
            elif suffix == "Endcap":
                eta_range = (1.24, 2.5)
        else:
            if suffix == "Barrel":
                eta_range = (0, 1.5)
            elif suffix == "Endcap":
                eta_range = (1.5, 2.5)
            elif suffix == "Forward":
                eta_range = (2.5, 5)

        return eta_range

    def get_eta_range(self, fname):
        """
        Wrapper function that calls `eta_ranges`
        and returns the object and the relevant eta ranges
        for the various detector regions.
        """
        basename = self.get_basename(fname)

        for suffix in ["Barrel", "Endcap", "Overlap"]:
            if suffix in basename:
                obj = basename.split(suffix)[0]
                eta_range = self.eta_ranges(obj, suffix)

                if eta_range is None:
                    print("Not found! ", basename, obj)
                else:
                    return obj, suffix, eta_range

        return None

    def decode_scaling(self, line):
        """
        Function that parses the syntax used in the scaling.txt files
        and returns the slope and offset of the scaling law for each object.
        """
        line = line.replace(" ", "")
        items = line.split("::")

        obj = items[1][: -len("Scaling")]
        slope = float(
            items[2][len("args:=(offline);lambda:=") : items[2].find("*off") - 10]
        )
        offset = float(items[2][items[2].find("*off") + len("*offline") : -10])

        return obj, slope, offset

    @property
    def collect_scalings(self):
        """
        Property that collects the scalings for all the objects available
        and saves them to `self.scaling_dict`.
        This function works only if `do_scalings` is set to True in the config.
        """
        if not self.do_scalings:
            return
        for fname in self.fnames:
            r = self.get_eta_range(os.path.basename(fname))

            if r is None:
                objcat = None
                region = None
                eta_range = (None, None)
            else:
                objcat, region, eta_range = r

            lines = self.get_lines(fname)

            for line in lines:
                obj, slope, offset = self.decode_scaling(line)
                d = {
                    region: {
                        "eta_min": eta_range[0],
                        "eta_max": eta_range[1],
                        "offset": offset,
                        "slope": slope,
                    }
                }

                if obj in self.scaling_dict:
                    self.scaling_dict[obj].update(d)
                else:
                    self.scaling_dict[obj] = d

    @property
    def dump_scalings(self):
        """
        Property that dumps to file the content of `self.scaling_dict`.
        This function works only if `do_scalings` is set to True in the config.
        """
        if not self.do_scalings:
            return
        os.makedirs(f"{self.scalings_outdir}", exist_ok=True)
        with open(f"{self.scalings_outdir}/{self.scalings_file}", "w") as outfile:
            yaml.dump(self.scaling_dict, outfile, default_flow_style=False)
