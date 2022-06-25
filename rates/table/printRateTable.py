"""
This script can be used with or without arguments.
If a cfg and rate file are passed via arguments,
a rate table exculsively for that combination is
printed.
Otherwise a rate table with all the cfg/rate file
combination specified in CFG_RATE_COMBOS is
displayed.
"""
import argparse
from itertools import chain
import re


CFG_RATE_COMBOS = {
    "2022-Apr20-v5-baseline-noMu_FBE_noMu_L1TDRMET_mhtSeed_123x": {
        "cfg": "cfg/v10_TRIDAS_newThresholds_LHCCReview",
        "rates": "out/2022-Apr20-v5-baseline-noMu_FBE_noMu_L1TDRMET_mhtSeed_123x/thresholds/menu.csv"
    },
    "2020-05-26-BugFix_v10_TRIDAS_newThresholds_LHCCReview": {
        "cfg": "cfg/v10_TRIDAS_newThresholds_LHCCReview",
        "rates": "out/2020-05-26-MENU-LHCCReview-BugFix_v10_TRIDAS_newThresholds_LHCCReview/thresholds/menu.csv"
    },
}


PATH_NAME_MAP = {
    "L1_SingleTkMu": "Single TkMuon",
    "L1_DoubleTkMu": "Double TkMuon",
    "L1_SingleTkEle": "Single TkElectron",
    "L1_SingleTkEleIso": "Single TkIsoElectron",
    "L1_SingleTkPhoIso": "Single TkIsoPhoton",
    "L1_TkEleIso_EG": "TkIsoElectron-StaEG",
    "L1_DoubleTkEle": "Double TkElectron",
    "L1_DoubleTkPhoIso": "Double TkIsoPhoton",
    "L1_SinglePFTau": "Single CaloTau",
    "L1_PFTau_PFTau": "Double CaloTau",
    "L1_PFIsoTau_PFIsoTau": "Double PuppiTau",
    "L1_PFIsoTau_TkMu": "PuppiTau-TkMuon",
    "L1_TkEleIso_PFIsoTau": "TkIsoElectron-PuppiTau",
    "L1_PFIsoTau_PFMet": "PuppiTau-PuppiMET",
    "L1_SinglePfJet": "Single PuppiJet",
    "L1_DoublePFJet_dEtaMax": "DoublePuppiJet",
    "L1_PFHTT": "PuppiMHT",
    "L1_PFMet": "PuppiMET",
    "L1_PFHTT_QuadJet": "QuadPuppiJets-PuppiHT",
    "L1_TkMu_TkEleIso": "TkMuon-TkIsoElectron",
    "L1_TkMu_TkEle": "TkMuon-TkElectron",
    "L1_TkEle_TkMu": "TkElectron-TkMuon",
    "L1_TkMu_DoubleTkEle": "TkMuon-DoubleTkElectron",
    "L1_TkMu_PfHTT": "TkMuon-PuppiHt",
    "L1_TkMu_PfJet_dRMax_DoubleJet_dEtaMax": "TkMuon-PuppiJet-dRMax-DoublePuppiJet-dEtaMax",
    "L1_DoubleTkEle_PFHTT": "DoubleTkEleElectron-PuppiHT",
    "L1_TkEleIso_PFHTT": "TkIsoElectron-PuppiHT",
    "L1_TkEle_PFJet_dRMin": "TkElectron-PuppiJet-dRMin",
    "L1_DoublePFJet_MassMin": "Double PuppiJets",
    "L1_SingleEGEle": "Single StaEG",
    "L1_DoubleEGEle": "Double StaEG",
    "L1_DoubleTkMu0er1p5_SQ_OS_dR_Max1p4": "Double TkMuon 0er1p5_SQ_OS_dR_Max1p4",
    "L1_DoubleTkMu4_SQ_OS_dR_Max1p2": "Double TkMuon 4_SQ_OS_dR_Max1p",
    "L1_DoubleTkMu4p5er2p0_SQ_OS_Mass7to18": "Double TkMuon 4p5er2p0_SQ_OS_Mass7to18",
    "L1_DoubleTkMu_PfHTT": "DoubleTkMuon-PuppiHT",
    "L1_DoubleTkMu_PfJet_PfMet": "DoubleTkMuon-PuppiJet-PuppiETmiss",
    "L1_DoubleTkMu_TkEle": "DoubleTkMuon-TkElectron",
    "L1_TkMu_PfJet_PfMet": "TkMuon-PuppiJet-PuppiETmiss",
    "L1_TripleTkMu": "Triple TkMuon",
    "L1_TripleTkMu_5SQ_3SQ_0OQ_DoubleMu_5_3_SQ_OS_Mass_Max9": "Triple TkMuon 5SQ_3SQ_0OQ_DoubleMu_5_3_SQ_OS_Mass_Max9",
    "L1_TripleTkMu_5_3p5_2p5_OS_Mass_5to17": "Triple TkMuon 5_3p5_2p5_OS_Mass_5to17",
    "total menu": "Total",
}


def parseArguments() -> dict:
    """
    Parses command line arguments for 'cfg'
    and 'rates' files and returns them.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--cfg', default="", type=str, help='cfg file')
    parser.add_argument('-r', '--rates', default="", type=str, help='csv file with rates')
    args = parser.parse_args()

    if args.cfg and args.rates:
        return {"Rates": 
            {"cfg": args.cfg, "rates": args.rates}
        }
    return CFG_RATE_COMBOS


class RateTablePrinter():
    
    def __init__(self, cfg_rate_dict):
        self.cfg_rate_dict = cfg_rate_dict

    def _pad(self, s, n_pad: int):
        """
        Applies a padding of n_pad whitespaces
        to the object s. s has to have a __str__
        method.
        """
        s = str(s)
        n_pad = n_pad - len(s)
        return s + n_pad * ' ' + '|'

    def _getPaths(self, cfg_path: str):
        """
        Parses the paths out of the cfg file
        given as an argument.
        """
        paths = []
        with open(cfg_path, 'r') as f:
            paths = [l.split('::')[1].strip() for l in f if l.startswith("trigger")]
        paths.append("total menu")
        return paths

    def _getRates(self, rates_path: str, paths: list) -> dict:
        """
        Returns the rates corresponding to the cfg paths.
        """
        rate_dict = {}
        with open(rates_path, 'r') as f:
            for line in f:
                if (path := re.search("^\w+(\smenu)?", line).group(0)) in paths:
                    pathrate = re.search("\d+.\d+$", line).group(0)
                    rate_dict[path] = float(pathrate)
        return rate_dict

    def _printTable(self, paths_rates: dict):
        """
        Prints paths and rates as a table.
        """
        nested_list_of_paths = [list(x) for x in paths_rates.values()]
        list_of_paths = list(dict.fromkeys(chain.from_iterable(nested_list_of_paths)))
        object_names = list(map(lambda x: PATH_NAME_MAP[x], list_of_paths))

        n_chars_first_col = max(list(map(lambda x: len(x), object_names))) + 2
        n_chars_other_col = max(list(map(lambda x: len(x), paths_rates.keys()))) + 2
        total_length = (n_chars_first_col
            + n_chars_other_col * len(list(paths_rates.keys()))
            + 2 * (len(paths_rates) + 2) - 1)

        # Print Header
        print('-' * total_length)
        rate_headings = [self._pad(x, n_chars_other_col) for x in paths_rates]
        print('|', self._pad("L1 Trigger Seeds", n_chars_first_col), *rate_headings)
        print('|' + '-' * (total_length - 2) + '|')

        # Print Body
        list_of_paths.append(list_of_paths.pop(list_of_paths.index("total menu")))
        for path in list_of_paths:
            if "total" in path:
                print('-' * total_length)

            rate_numbers = []
            for rname in paths_rates:
                try:
                    n = round(paths_rates[rname][path], 2)
                except KeyError:
                    n = '-'
                rate_numbers.append(
                    self._pad(
                      n,
                      n_chars_other_col
                    )
                )
            print('|', self._pad(PATH_NAME_MAP[path], n_chars_first_col), *rate_numbers)
        totals_plus = [self._pad(float(x[:-1]) + 54, n_chars_other_col) for x in rate_numbers]
        print('|', self._pad("Total + 54kHz", n_chars_first_col), *totals_plus)

        print('-' * total_length)

    def printRateTable(self):
        paths_rates = {
            rname: {} for rname in self.cfg_rate_dict.keys()
        }
        for rname, fpaths in self.cfg_rate_dict.items():
            paths = self._getPaths(fpaths["cfg"])
            rate_dict = self._getRates(fpaths["rates"], paths)
            paths_rates[rname] = rate_dict
        self._printTable(paths_rates)


if __name__ == "__main__":
    cfg_rates_dict = parseArguments()
    printer = RateTablePrinter(cfg_rates_dict)
    printer.printRateTable()

