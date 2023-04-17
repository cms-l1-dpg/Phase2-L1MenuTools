#!/afs/cern.ch/user/d/dhundhau/public/miniconda3/envs/py310/bin/python
import argparse
import os

import matplotlib.pyplot as plt
import mplhep as hep
import numpy as np
import yaml
import json

from plotter import Plotter

plt.style.use(hep.style.CMS)


class ComparisonCentral(Plotter):

    def __init__(self, cfg_plots_path):
        with open(cfg_plots_path, 'r') as f:
            self.cfg_plots = yaml.safe_load(f)
        self.cfgs = {}
        for plot_name, cfg_plot in self.cfg_plots.items():
            print (plot_name)
            self.cfgs[plot_name] = cfg_plot
            if not os.path.exists(cfg_plot['save_dir']): os.makedirs(cfg_plot['save_dir'])
            # self.plot_name = plot_name
        # self.cfg = self.cfg_plots[self.plot_name]
        # self.save_dir = self.cfg["save_dir"]
        # if not os.path.exists(self.save_dir): os.makedirs(self.save_dir)

    def _get_watermark(self,cfg):
       try:
           return cfg["watermark"]
       except KeyError:
           return " "

    def _get_files(self,cfg):
        try:
            return cfg["files"]
        except KeyError:
            print("You must specify the input files under the key 'files'!")

    def _get_plot(self, name):
        fname = open(name + ".json")
        dict_to_plot = json.load(fname)
        return dict_to_plot

    def _style_plot(self, cfg, fig, ax, legend_loc="upper right"):
        ax.axhline(1, ls=":", c="k")
        ax.legend(loc=legend_loc, frameon=False)
        ax.set_xlabel(rf"{cfg['xlabel']}")
        ylabel = cfg["ylabel"]
        ax.set_ylabel(rf"{ylabel}")
        ax.set_ylim(0.0, 1)
        ax.tick_params(direction="in")
        ax.text(0, -0.1, self._get_watermark(cfg),
                color="grey", alpha=0.2,
                fontsize=20,
                transform=ax.transAxes)
        fig.tight_layout()

    def run(self):
        for plot_name, cfg in self.cfgs.items():
            files = self._get_files(cfg)
            fig, ax =  self._create_new_plot()
            for file in files:
                fname = os.path.join(files[file]["dir"], file)
                test_object = files[file]["object"]
                dict_to_plot = self._get_plot(fname)

                label = dict_to_plot[test_object]["label"]
                if "label" in files[file]:
                    label = files[file]["label"]

                err_kwargs = dict_to_plot[test_object]["err_kwargs"]

                ax.errorbar(dict_to_plot[test_object]["xbins"],
                            dict_to_plot[test_object]["efficiency"],
                            yerr = dict_to_plot[test_object]["efficiency_err"],
                            label = label, **err_kwargs)

            self._style_plot(cfg, fig, ax)
            print ("Saving plot to : ",plot_name)
            plt.savefig(f"{cfg['save_dir']}/{plot_name}.png")
            plt.savefig(f"{cfg['save_dir']}/{plot_name}.pdf")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "cfg_plots",
        default="cfg_plots/bJetEff.yaml",
        help="Path of YAML file specifying the desired plots."
    )
    args = parser.parse_args()

    plotter = ComparisonCentral(args.cfg_plots)
    plotter.run()

