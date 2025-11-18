import os
import argparse
import yaml
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
    PI_PI_STACKING_TYPES
)


def get_interactions(
    ri_df: pd.DataFrame | None = None,
    contacts_df: pd.DataFrame | None = None,
    ari_df: pd.DataFrame | None = None,
    contact_level: str = "residue",
) -> pd.DataFrame:

    columns = [
        "chain_1",
        "res_1",
        "atom_1",
        "chain_2",
        "res_2",
        "atom_2",
        "interaction_type"
    ]

    combined_df = pd.DataFrame(columns=columns)

    if contacts_df is not None:

        contacts_df = contacts_df.reset_index(drop=True)

        combined_df = pd.concat(
            [
                combined_df,
                contacts_df[list(set(contacts_df.columns) & set(columns))]
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
                ri_df[list(set(ri_df.columns) & set(columns))]
            ],
            ignore_index=True
        )

    if ari_df is not None:

        ari_df = ari_df.reset_index(drop=True)

        combined_df = pd.concat(
            [
                combined_df,
                ari_df[list(set(ari_df.columns) & set(columns))]
            ],
            ignore_index=True
        )

    if contact_level == "residue":
        combined_df = combined_df.drop(columns=["atom_1", "atom_2"])
        combined_df = combined_df.drop_duplicates().reset_index(drop=True)

    return combined_df

def get_arpeggio_file(
    arpeggio_dir: str,
    result_head: str,
    file_extension: str,
) -> str:

    return os.path.join(
        arpeggio_dir, result_head, f"{result_head}.{file_extension}"
    )


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
        "-h",
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
    args = args.parse_args()

    with open(args.input_config, 'r') as f:
        config = yaml.safe_load(f)

    arpeggio_results = config["arpeggio_results"]

    result_metadata = arpeggio_results.get(args.result_head, None)
    if result_metadata is None:
        raise ValueError(
            f"Result head {args.result_head} not found in input configuration."
        )

    selections = []
    for sel in result_metadata.get("selections", []):
        _, chain, res, _ = sel.split("/")
        selections.append((chain, res))

    SEL_RES = [res for chain, res in selections]

    proteins = result_metadata.get("proteins", [])
    result_head = args.result_head

    # result_head = "6bd4_hydrogenated"
    # result_head = "L485F_6bd4_hydrogenated"

    # result_head = "7drt_hydrogenated"
    # result_head = "W234C_7drt_hydrogenated"
    # result_head = "M354T_7drt_hydrogenated"

    # SEL_RES = ["485"]
    # SEL_RES = ["234", "354"]

    arpeggio_dir = args.arpeggio_dir

    contacts_path = get_arpeggio_file(
        arpeggio_dir=arpeggio_dir,
        result_head=result_head,
        file_extension="contacts"
    )

    contacts_df = parse_contacts(file_path=contacts_path, split_atom_col=True)
    # print(contacts_df.head())

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
        contact_level="residue"
    )

    # first residue = selected residue
    interactions_df_ = pd.DataFrame(columns=interactions_df.columns)

    for idx, row in interactions_df.iterrows():

        if row["res_1"] in SEL_RES:
            interactions_df_ = pd.concat(
                [interactions_df_, pd.DataFrame([row])],
                ignore_index=True
            )

        elif row["res_2"] in SEL_RES:
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

    # merge by residue pairs
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

    interactions_df = interactions_df.sort_values(
        by=["chain_1", "res_1", "chain_2", "res_2"]
    ).reset_index(drop=True)

    total_interactions_type = list(set(
        interaction
        for sublist in interactions_df["interaction_type"].str.split(",").tolist()
        for interaction in sublist
    ))

    total_interactions_type = (
        CHOSEN_CONTACT_TYPES + CHOSEN_CLASHES
        + CHOSEN_ARI_TYPES + ["PI-PI_STACKING"]
    )

    # add these as columns with 0/1 values
    for interaction in total_interactions_type:
        interactions_df[interaction] = interactions_df["interaction_type"].apply(
            lambda x: 1 if interaction in x.split(",") else 0
        )
    del interactions_df["interaction_type"]

    interactions_df = interactions_df[[
        "chain_1",
        "res_1",
        "chain_2",
        "res_2",
    ] + sorted(total_interactions_type)]

    interactions_df.to_csv(
        f"../output/pairwise_interactions/{result_head}_interactions.csv",
        index=False
    )
    # exit()

    # add_rings(
    #     rings_df=rings_df,
    #     save_path=f"../output/input_to_chimerax/{result_head}_markers.cxc"
    # )

    # add_ri(
    #     ri_df=ri_df,
    #     save_path=f"../output/input_to_chimerax/{result_head}_ri.cxc"
    # )

    add_contacts(
        contacts_df=contacts_df,
        save_path=f"../output/input_to_chimerax/{result_head}_contacts.cxc"
    )