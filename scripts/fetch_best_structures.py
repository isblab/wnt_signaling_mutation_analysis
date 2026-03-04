# Description: Fetch best structures for given proteins
# input: json file with protein names and uniprot ids ({protein_name: uniprot_id})
# output: csv and json files with best structures

import os
import yaml
from argparse import ArgumentParser
from IMP_Toolbox.structure.best_structure import (
    fetch_best_structures,
    make_best_structures_df,
)

CONFIG_FILE = "../input/config.yaml"
BEST_STRUCTURES_CSV = "../output/best_structures.csv"

if __name__ == "__main__":

    args = ArgumentParser()

    args.add_argument(
        "-i",
        "--input",
        type=str,
        required=False,
        default=CONFIG_FILE,
        help="Path to input yaml file containing proteins and their uniprot ids",
    )

    args.add_argument(
        "-o",
        "--output",
        type=str,
        required=False,
        default=BEST_STRUCTURES_CSV,
        help="Path to output csv file containing best structures",
    )

    args.add_argument(
        "--overwrite",
        action="store_true",
        required=False,
        default=False,
        help="Overwrite existing best structures",
    )

    args = args.parse_args()

    config_yaml = yaml.load(
        open(args.input),
        Loader=yaml.FullLoader
    )

    proteins_dict = config_yaml.get("protein_uniprot_map", None)
    uniprot_ids = list(proteins_dict.values())
    uniprot_ids = [u for u in uniprot_ids if u is not None]

    # bs = BestStructures(uniprot_ids=uniprot_ids)

    best_structures = fetch_best_structures(
        uniprot_ids=uniprot_ids,
        save_path=os.path.join(
            os.path.dirname(args.output),
            os.path.basename(args.output).replace(".csv", ".json")),
        overwrite=args.overwrite
    )

    df = make_best_structures_df(best_structures)
    df.to_csv(args.output, index=False)

    if os.path.exists(args.output) and not args.overwrite:
        print("Best structures already exist. Use --overwrite to overwrite.")
    else:
        print(f"Best structures saved to {os.path.abspath(args.output)}")