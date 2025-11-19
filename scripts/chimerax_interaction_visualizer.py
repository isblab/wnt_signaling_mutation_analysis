import warnings
import os
import pandas as pd
from string import Template
from arpeggio_constants import (
    CHOSEN_CONTACT_TYPES,
    MARKER_COMMAND,
    PBOND_ATTRIBUTES,
    PBOND_COMMAND,
    MARKER_ATTRIBUTES,
    TRANSPARENCY_COMMAND,
    CHOSEN_CLASHES,
    CHOSEN_ARI_TYPES,
    MODEL_ID,
)

def save_commands_to_file(
    save_path: str,
    commands: list[str]
) -> None:
    """ Save a list of ChimeraX commands to a file.

    Args:

        save_path (str):
            Path to save the commands.

        commands (list[str]):
            List of ChimeraX commands to save.
    """

    if not os.path.exists(os.path.dirname(save_path)):
        warnings.warn(
            f"Directory does not exist: {os.path.dirname(save_path)}. \
            Creating a new directory."
        )
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

    with open(save_path, 'w') as f:
        for command in commands:
            f.write(command + "\n")

def add_contacts(
    contacts_df: pd.DataFrame | None = None,
    save_path: str | None = None,
    add_selections: bool = True,
):
    """ Generate ChimeraX commands to add pseudobonds for atomic contacts.

    Args:

        contacts_df (pd.DataFrame):
            DataFrame containing inter-atomic contact information.

        save_path (str | None, optional):
            Path to save the commands. If None, returns the commands as a list.

        add_selections (bool, optional):
            Whether to add selection commands for the interacting residues.

    Returns:

        list[str] | None:
            List of ChimeraX commands if save_path is None, else None.
    """

    if contacts_df is None or contacts_df.empty:
        warnings.warn("No contacts found.")
        return []

    command_template = Template(PBOND_COMMAND)
    transparency_template = Template(TRANSPARENCY_COMMAND)
    # model_id = 1
    commands = []
    sub_model_ids = {}
    sub_model_id = 1

    for _, row in contacts_df.iterrows():

        atom1_spec = f"{MODEL_ID}/{row['chain_1']}:{row['res_1']}@{row['atom_1']}"
        atom2_spec = f"{MODEL_ID}/{row['chain_2']}:{row['res_2']}@{row['atom_2']}"

        if add_selections:
            sel_cmd = f"sel add #{atom1_spec.split("@")[0]}#{atom2_spec.split('@')[0]}"
            if sel_cmd not in commands:
                commands.append(sel_cmd)

        detected_interactions = [
            interaction for interaction in CHOSEN_CONTACT_TYPES + CHOSEN_CLASHES
            if row[interaction] == '1'
        ]

        for interaction in detected_interactions:

            if interaction not in sub_model_ids:
                sub_model_ids[interaction] = sub_model_id
                sub_model_id += 1

            command = command_template.substitute(
                spec1=atom1_spec,
                spec2=atom2_spec,
                bond_color=PBOND_ATTRIBUTES.get(
                    interaction, PBOND_ATTRIBUTES["default"]
                    ).get("color", "yellow"),
                bond_radius=PBOND_ATTRIBUTES.get(
                    interaction, PBOND_ATTRIBUTES["default"]
                    ).get("radius", 0.1),
                bond_name=interaction,
                bond_dashes=PBOND_ATTRIBUTES.get(
                    interaction, PBOND_ATTRIBUTES["default"]
                    ).get("dashes", 6),
            )
            commands.append(command)

            command = transparency_template.substitute(
                model_id=f"{MODEL_ID}.{sub_model_ids.get(interaction, sub_model_id)}",
                target_spec="p",
                transparency=PBOND_ATTRIBUTES.get(
                    interaction, PBOND_ATTRIBUTES["default"]
                    ).get("transparency", 0),
            )
            commands.append(command)

    if save_path:
        save_commands_to_file(save_path, commands)

    return commands

def add_rings(
    rings_df: pd.DataFrame | None = None,
    save_path: str | None = None,
    add_selections: bool = True,
) -> list[str] | None:
    """ Generate ChimeraX commands to add markers at ring centroids.

    Args:

        rings_df (pd.DataFrame):
            DataFrame containing ring information.

        save_path (str | None, optional):
            Path to save the commands. If None, returns the commands as a list.

        add_selections (bool, optional):
            Whether to add selection commands aromatic residues.

    Returns:

        list[str] | None:
            List of ChimeraX commands if save_path is None, else None.
    """

    if rings_df is None or rings_df.empty:
        warnings.warn("No rings found.")
        return []

    command_template = Template(MARKER_COMMAND)
    commands = []

    for _, row in rings_df.iterrows():
        x, y, z = row["ring_centroid"].split(",")
        command = command_template.substitute(
            marker_model_id=MARKER_ATTRIBUTES["model_id"],
            x=x,
            y=y,
            z=z,
            marker_color=MARKER_ATTRIBUTES["color"],
            marker_radius=MARKER_ATTRIBUTES["radius"],
        )
        commands.append(command)

        if add_selections:
            chain_id = row["chain"]
            res_id = row["res"]
            sel_cmd = f"sel add #{MODEL_ID}/{chain_id}:{res_id}"
            if sel_cmd not in commands:
                commands.append(sel_cmd)

    commands.append(
        f"rename #{MARKER_ATTRIBUTES['model_id']} ring_centroids"
    )

    if save_path:
        save_commands_to_file(save_path, commands)

    return commands


def add_ri(
    ri_df: pd.DataFrame | None = None,
    save_path: str | None = None,
    add_selections: bool = True,
) -> list[str] | None:
    """ Generate ChimeraX commands to add pseudobonds for ring interactions.

    Args:

        ri_df (pd.DataFrame):
            DataFrame containing ring interaction information.

        save_path (str | None, optional):
            Path to save the commands. If None, returns the commands as a list.

        add_selections (bool, optional):
            Whether to add selection commands for the interacting residues.

    Returns:

        list[str] | None:
            List of ChimeraX commands if save_path is None, else None.
    """

    if ri_df is None or ri_df.empty:
        warnings.warn("No ring interactions found.")
        return []

    command_template = Template(PBOND_COMMAND)
    transparency_template = Template(TRANSPARENCY_COMMAND)
    commands = []
    sub_model_ids = {} # each interaction type gets its own idx
    sub_model_id = 1

    for _, row in ri_df.iterrows():

        marker1_id = row["marker_id_1"]
        marker2_id = row["marker_id_2"]
        marker1_spec = f"{MARKER_ATTRIBUTES["model_id"]}/M:{marker1_id}@M"
        marker2_spec = f"{MARKER_ATTRIBUTES["model_id"]}/M:{marker2_id}@M"
        bond_name = row["interaction_type"]

        if bond_name not in sub_model_ids:
            sub_model_ids[bond_name] = sub_model_id
            sub_model_id += 1

        command = command_template.substitute(
            spec1=marker1_spec,
            spec2=marker2_spec,
            bond_color=PBOND_ATTRIBUTES.get(
                bond_name, PBOND_ATTRIBUTES["ri"]
            )["color"],
            bond_radius=PBOND_ATTRIBUTES.get(
                bond_name, PBOND_ATTRIBUTES["ri"]
            )["radius"],
            bond_name=bond_name,
            bond_dashes=PBOND_ATTRIBUTES.get(
                bond_name, PBOND_ATTRIBUTES["ri"]
            )["dashes"],
        )
        commands.append(command)

        if add_selections:
            chain1 = row["chain_1"]
            res1 = row["res_1"]
            chain2 = row["chain_2"]
            res2 = row["res_2"]
            sel_cmd = f"sel add #{MODEL_ID}/{chain1}:{res1}#{MODEL_ID}/{chain2}:{res2}"
            if sel_cmd not in commands:
                commands.append(sel_cmd)

        command = transparency_template.substitute(
            model_id=f"{MARKER_ATTRIBUTES["model_id"]}.{sub_model_ids[bond_name]}",
            target_spec="p",
            transparency=PBOND_ATTRIBUTES.get(
                bond_name, PBOND_ATTRIBUTES["ri"]
                )["transparency"],
        )
        commands.append(command)

    if save_path:
        save_commands_to_file(save_path, commands)

    return commands

def add_ari(
    ari_df: pd.DataFrame | None = None,
    save_path: str | None = None,
    add_selections: bool = True,
):
    """ Generate ChimeraX commands to add pseudobonds for atom-ring interactions.

    Args:

        ari_df (pd.DataFrame):
            DataFrame containing atom-ring interaction information.

        save_path (str | None, optional):
            Path to save the commands. If None, returns the commands as a list.

        add_selections (bool, optional):
            Whether to add selection commands for the interacting residues.

    Returns:

        list[str] | None:
            List of ChimeraX commands if save_path is None, else None.
    """

    if ari_df is None or ari_df.empty:
        warnings.warn("No atom-ring interactions found.")
        return []

    command_template = Template(PBOND_COMMAND)
    transparency_template = Template(TRANSPARENCY_COMMAND)
    model_id = 1
    commands = []
    sub_model_ids = {}
    sub_model_id = 1

    for _, row in ari_df.iterrows():
        atom_spec = f"{model_id}/{row['chain_1']}:{row['res_1']}@{row['atom_1']}"
        ring_marker_id = row["marker_id"]
        ring_spec = f"{MARKER_ATTRIBUTES["model_id"]}/M:{ring_marker_id}@M"
        interaction = row["interaction_type"]
        assert interaction in CHOSEN_ARI_TYPES, (
            f"Unexpected interaction type '{interaction}' found in ARI data."
        )
        if interaction not in sub_model_ids:
            sub_model_ids[interaction] = sub_model_id
            sub_model_id += 1

        command = command_template.substitute(
            spec1=atom_spec,
            spec2=ring_spec,
            bond_name=interaction,
            bond_color=PBOND_ATTRIBUTES.get(
                interaction, PBOND_ATTRIBUTES["ari"]
                ).get("color", "yellow"),
            bond_radius=PBOND_ATTRIBUTES.get(
                interaction, PBOND_ATTRIBUTES["ari"]
                ).get("radius", 0.1),
            bond_dashes=PBOND_ATTRIBUTES.get(
                interaction, PBOND_ATTRIBUTES["ari"]
                ).get("dashes", 6),
        )
        commands.append(command)

        if add_selections:
            chain1 = row["chain_1"]
            res1 = row["res_1"]
            chain2 = row["chain_2"]
            res2 = row["res_2"]
            sel_cmd = f"sel add #{MODEL_ID}/{chain1}:{res1}#{MODEL_ID}/{chain2}:{res2}"
            if sel_cmd not in commands:
                commands.append(sel_cmd)

        command = transparency_template.substitute(
            model_id=f"{model_id}.{sub_model_ids[interaction]}",
            target_spec="p",
            transparency=PBOND_ATTRIBUTES.get(
                interaction, PBOND_ATTRIBUTES["ari"]
                ).get("transparency", 0),
        )
        commands.append(command)

    if save_path:
        save_commands_to_file(save_path, commands)

    return commands