import argparse


def pad(s, n_pad: int):
    """
    Applies a padding of n_pad whitespaces
    to the object s. s has to have a __str__
    method.
    """
    s = str(s)
    n_pad = n_pad - len(s)
    return s + n_pad * ' '


def parseArguments():
    """
    Parses command line arguments for 'cfg'
    and 'rates' files and returns them.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--cfg', type=str, help='cfg file', required=True)
    parser.add_argument('-r', '--rates', type=str, help='csv file with rates', required=True)
    return parser.parse_args()


def getPaths(cfg_path: str):
    """
    Parses the paths out of the cfg file
    given as an argument.
    """
    paths = []
    with open(cfg_path, 'r') as f:
        for line in f:
            if "Set:" in line:
                paths.append(line)
            if line.startswith("trigger"):
                paths.append(line.split('::')[1].strip())
    return paths


def getRates(rates_path: str, paths: list):
    """
    Returns the rates corresponding to the cfg paths.
    """
    paths_with_rates = []
    rates = []
    with open(rates_path, 'r') as f:
        for path in paths:
            if "Set:" in path:
                print(path)
                continue
            for line in f:
                if path == line.split(':')[0].strip():
                    pathrate = line.replace(':', ' :').split(':')[1].split()[2]
                    rates.append(float(pathrate))
                    paths_with_rates.append(path)
            f.seek(0)
    return paths_with_rates, rates


def printTable(paths: list, rates: list):
    """
    Prints paths and rates as a table.
    """
    max_path_length = max(list(map(lambda x: len(x), paths)))
    total_length = max_path_length + 12
    print('-' * total_length)
    print('|', pad("Path", max_path_length + 2), pad("Rate", total_length - max_path_length - 6) + '|')
    print('|' + '-' * (total_length - 2) + '|')
    for path, rate in zip(paths, rates):
        print('|', pad(path, max_path_length + 2), pad(round(rate, 1), 5), '|')
    print('-' * total_length)


if __name__ == "__main__":
    args = parseArguments()
    paths = getPaths(args.cfg)
    paths, rates = getRates(args.rates, paths)
    printTable(paths, rates)

