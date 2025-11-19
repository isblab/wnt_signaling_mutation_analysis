import os
import yaml
import argparse
import pandas as pd
from arpeggio_result_parser import (
    parse_ari,
    parse_contacts,
    parse_ri,
    parse_rings,
)
from chimerax_interaction_visualizer import (
    add_contacts,
    add_rings,
    add_ri,
    add_ari,
)
from arpeggio_constants import (
    CHOSEN_ARI_TYPES,
    CHOSEN_CONTACT_TYPES,
    CHOSEN_CLASHES,
    PI_PI_STACKING_TYPES,
    INTERACTION_DF_COLS
)

def get_interactions(
    ri_df: pd.DataFrame | None = None,
    contacts_df: pd.DataFrame | None = None,
    ari_df: pd.DataFrame | None = None,
    contact_level: str = "residue",
) -> pd.DataFrame:
    """ Combine interactions from contacts, ri, and ari dataframes.

    Args:

        ri_df (pd.DataFrame | None, optional):
            Ring-ring interactions dataframe.

        contacts_df (pd.DataFrame | None, optional):
            Atomic interactions dataframe.

        ari_df (pd.DataFrame | None, optional):
            Atom-ring interactions dataframe.

        contact_level (str, optional):
            Contact level: "atom" or "residue".

    Returns:

        pd.DataFrame:
            DataFrame containing combined interactions.
    """

    assert contact_level in INTERACTION_DF_COLS, (
        f"contact_level must be one of {list(INTERACTION_DF_COLS.keys())}."
    )

    combined_df = pd.DataFrame(columns=INTERACTION_DF_COLS[contact_level])

    if contacts_df is not None:

        contacts_df = contacts_df.reset_index(drop=True)
        combined_df = pd.concat(
            [
                combined_df,
                contacts_df.filter(INTERACTION_DF_COLS[contact_level])
            ],
            ignore_index=True
        )

        for idx, row in contacts_df.iterrows():
            detected_interactions = [
                interaction
                for interaction in CHOSEN_CONTACT_TYPES + CHOSEN_CLASHES
                if row[interaction] == '1'
            ]
            if len(detected_interactions) == 0:
                continue

            detected_interactions = ",".join(detected_interactions)
            combined_df.iloc[idx, -1] = detected_interactions

        combined_df = combined_df.dropna(
            subset=["interaction_type"]
        ).reset_index(drop=True)

    if ri_df is not None:

        ri_df = ri_df.reset_index(drop=True)
        if contact_level == "residue":
            ri_df["interaction_type"] = "PI-PI_STACKING"

        combined_df = pd.concat(
            [
                combined_df,
                ri_df.filter(INTERACTION_DF_COLS[contact_level])
            ],
            ignore_index=True
        )

    if ari_df is not None:

        ari_df = ari_df.reset_index(drop=True)
        combined_df = pd.concat(
            [
                combined_df,
                ari_df.filter(INTERACTION_DF_COLS[contact_level])
            ],
            ignore_index=True
        )

    combined_df = combined_df.drop_duplicates().reset_index(drop=True)

    return combined_df


if __name__ == "__main__":

    args = argparse.ArgumentParser()

    args.add_argument(
        "-i",
        "--input_config",
        type=str,
        required=False,
        default="../input/config.yaml",
        help="Path to the input configuration file.",
    )
    args.add_argument(
        "-r",
        "--result_head",
        type=str,
        required=False,
        default="6bd4_hydrogenated",
        help="Head of the result files.",
    )
    args.add_argument(
        "-a",
        "--arpeggio_dir",
        type=str,
        required=False,
        default="../output/arpeggio_docker_results/",
        help="Directory containing Arpeggio results.",
    )
    args.add_argument(
        "-l",
        "--level",
        type=str,
        required=False,
        default="atom",
        help="Contact level: atom or residue.",
    )
    args.add_argument(
        "-c",
        "--chimerax_commands",
        action="store_true",
        required=False,
        default=False,
        help="Whether to generate ChimeraX command files.",
    )
    args.add_argument(
        "-o",
        "--output_dir",
        type=str,
        required=False,
        default="../output/",
        help="Output directory.",
    )
    args = args.parse_args()

    ###########################################################################
    # Load input configuration
    ###########################################################################
    with open(args.input_config, 'r') as f:
        config = yaml.safe_load(f)

    arpeggio_results = config["arpeggio_results"]
    result_metadata = arpeggio_results.get(args.result_head, None)
    if result_metadata is None:
        raise ValueError(
            f"Result head {args.result_head} not found in input configuration."
        )

    # Residue selections that were used for Arpeggio
    selections = []
    for sel in result_metadata.get("selections", []):
        _, chain, res, _ = sel.split("/")
        selections.append((chain, res))
    res_selections = [res for _chain, res in selections]

    result_head = args.result_head
    arpeggio_dir = args.arpeggio_dir

    contacts_path = os.path.join(
        arpeggio_dir, result_head, f"{result_head}.contacts"
    )

    ###########################################################################
    # Parse Arpeggio result files
    ###########################################################################
    contacts_df = parse_contacts(
        file_path=contacts_path,
        split_atom_col=True
    )
    # print(contacts_df)

    ri_df = parse_ri(
        file_path=contacts_path.replace(".contacts", ".ri"),
        add_marker_id=True,
        split_residue_col=True
    )
    # print(ri_df)

    rings_df = parse_rings(
        file_path=contacts_path.replace(".contacts", ".rings"),
        add_marker_id=True,
        split_residue_col=True,
    )
    # print(rings_df)

    ari_df = parse_ari(
        file_path=contacts_path.replace(".contacts", ".ari"),
        split_atom_col=True,
        split_residue_col=True,
    )
    # print(ari_df)

    interactions_df = get_interactions(
        ri_df=ri_df,
        contacts_df=contacts_df,
        ari_df=ari_df,
        contact_level=args.level,
    )

    ###########################################################################
    # first residue is always the selected residue
    ###########################################################################
    interactions_df_ = pd.DataFrame(columns=interactions_df.columns)

    for idx, row in interactions_df.iterrows():

        if row["res_1"] in res_selections:
            interactions_df_ = pd.concat(
                [interactions_df_, pd.DataFrame([row])],
                ignore_index=True
            )

        elif row["res_2"] in res_selections:
            new_row = row.copy()
            new_row["chain_1"] = row["chain_2"]
            new_row["res_1"] = row["res_2"]
            new_row["chain_2"] = row["chain_1"]
            new_row["res_2"] = row["res_1"]
            if "atom_1" in row.index and "atom_2" in row.index:
                new_row["atom_1"] = row.get("atom_2", None)
                new_row["atom_2"] = row.get("atom_1", None)
            interactions_df_ = pd.concat(
                [interactions_df_, pd.DataFrame([new_row])],
                ignore_index=True
            )

    ###########################################################################
    # merge by residue pairs if information is required at residue level
    ###########################################################################
    if args.level == "residue":
        row_dict = {}
        for idx, row in interactions_df_.iterrows():

            key = (row["chain_1"], row["res_1"], row["chain_2"], row["res_2"])

            if key not in row_dict:
                row_dict[key] = set()

            for interaction in row["interaction_type"].split(","):
                row_dict[key].add(interaction)

        interactions_df = pd.DataFrame(columns=interactions_df_.columns)

        for key, interactions in row_dict.items():
            new_row = {
                "chain_1": key[0],
                "res_1": key[1],
                "chain_2": key[2],
                "res_2": key[3],
                "interaction_type": ",".join(sorted(interactions))
            }
            interactions_df = pd.concat(
                [interactions_df, pd.DataFrame([new_row])],
                ignore_index=True
            )

    ###########################################################################
    # Formatting and saving interactions dataframe
    ###########################################################################
    interactions_df = interactions_df.sort_values(
        by=INTERACTION_DF_COLS[args.level][:-1]
    ).reset_index(drop=True)

    total_interactions_type = (
        CHOSEN_CONTACT_TYPES + CHOSEN_CLASHES
        + CHOSEN_ARI_TYPES + ["PI-PI_STACKING"]
    )

    for interaction in total_interactions_type:
        interactions_df[interaction] = (
            interactions_df["interaction_type"].apply(
                lambda x: 1 if interaction in x.split(",") else 0
            )
        )

    del interactions_df["interaction_type"]

    interactions_df = interactions_df[
        INTERACTION_DF_COLS[args.level][:-1] + sorted(total_interactions_type)
    ]

    outpath = os.path.join(args.output_dir, "pairwise_interactions")
    os.makedirs(outpath, exist_ok=True)

    interactions_df.to_csv(
        os.path.join(outpath, f"{result_head}_interactions.csv"),
        index=False
    )
    print(f"Pairwise interactions saved in {os.path.abspath(outpath)}.")

    ###########################################################################
    # Generate ChimeraX command files
    ###########################################################################
    if not args.chimerax_commands:
        exit()

    outpath = os.path.join(args.output_dir, "input_to_chimerax")
    os.makedirs(outpath, exist_ok=True)

    add_rings(
        rings_df=rings_df,
        save_path=os.path.join(outpath, f"{result_head}_markers.cxc")
    )

    add_ri(
        ri_df=ri_df,
        save_path=os.path.join(outpath, f"{result_head}_ri.cxc")
    )

    add_contacts(
        contacts_df=contacts_df,
        save_path=os.path.join(outpath, f"{result_head}_contacts.cxc")
    )

    add_ari(
        ari_df=ari_df,
        save_path=os.path.join(outpath, f"{result_head}_ari.cxc")
    )

    print(f"ChimeraX command files saved in {os.path.abspath(outpath)}.")