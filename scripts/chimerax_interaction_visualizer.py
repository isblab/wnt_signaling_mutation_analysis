from string import Template
import pandas as pd
import warnings
from arpeggio_constants import (
    CHOSEN_CONTACT_TYPES,
    MARKER_COMMAND,
    PBOND_ATTRIBUTES,
    PBOND_COMMAND,
    MARKER_ATTRIBUTES,
    TRANSPARENCY_COMMAND,
    CHOSEN_CLASHES,
    CHOSEN_ARI_TYPES,
)

def save_commands_to_file(save_path: str, commands: list[str]) -> None:
    """ Save a list of ChimeraX commands to a file.

    Args:

        save_path (str):
            Path to save the commands.

        commands (list[str]):
            List of ChimeraX commands to save.
    """

    with open(save_path, 'w') as f:
        for command in commands:
            f.write(command + "\n")

def add_rings(
    rings_df: pd.DataFrame | None = None,
    save_path: str | None = None
) -> list[str] | None:
    """ Generate ChimeraX commands to add markers at ring centroids.

    Args:

        rings_df (pd.DataFrame):
            DataFrame containing ring information.

        save_path (str | None, optional):
            Path to save the commands. If None, returns the commands as a list.

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

    commands.append(
        f"rename #{MARKER_ATTRIBUTES['model_id']} ring_centroids"
    )

    if save_path is None:
        return commands

    save_commands_to_file(save_path, commands)

def add_ri(
    ri_df: pd.DataFrame | None = None,
    save_path: str | None = None
) -> list[str] | None:
    """ Generate ChimeraX commands to add pseudobonds for ring interactions.

    Args:

        ri_df (pd.DataFrame):
            DataFrame containing ring interaction information.

        save_path (str | None, optional):
            Path to save the commands. If None, returns the commands as a list.

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
    sub_model_ids = {}
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
            bond_color=PBOND_ATTRIBUTES.get(bond_name, PBOND_ATTRIBUTES["default"])["color"],
            bond_radius=PBOND_ATTRIBUTES.get(bond_name, PBOND_ATTRIBUTES["default"])["radius"],
            bond_name=bond_name,
            bond_dashes=PBOND_ATTRIBUTES.get(bond_name, PBOND_ATTRIBUTES["default"])["dashes"],
        )
        commands.append(command)
        command = transparency_template.substitute(
            transparency=PBOND_ATTRIBUTES.get(bond_name, PBOND_ATTRIBUTES["default"])["transparency"],
            model_id=f"{MARKER_ATTRIBUTES["model_id"]}.{sub_model_ids[bond_name]}",
            target_spec="p"
        )
        commands.append(command)

    # print(sub_model_ids)

    if save_path is None:
        return commands

    save_commands_to_file(save_path, commands)

def add_contacts(
    contacts_df: pd.DataFrame | None = None,
    save_path: str | None = None
):
    """ Generate ChimeraX commands to add pseudobonds for atomic contacts.

    Args:

        contacts_df (pd.DataFrame):
            DataFrame containing inter-atomic contact information.

        save_path (str | None, optional):
            Path to save the commands. If None, returns the commands as a list.

    Returns:

        list[str] | None:
            List of ChimeraX commands if save_path is None, else None.
    """

    if contacts_df is None or contacts_df.empty:
        warnings.warn("No contacts found.")
        return []

    command_template = Template(PBOND_COMMAND)
    transparency_template = Template(TRANSPARENCY_COMMAND)
    model_id = 1
    commands = []
    sub_model_ids = {}
    sub_model_id = 1
    for _, row in contacts_df.iterrows():
        atom1_spec = f"{model_id}/{row['chain_1']}:{row['res_1']}@{row['atom_1']}"
        atom2_spec = f"{model_id}/{row['chain_2']}:{row['res_2']}@{row['atom_2']}"
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
                bond_color=PBOND_ATTRIBUTES.get(interaction, PBOND_ATTRIBUTES["default"])["color"],
                bond_radius=PBOND_ATTRIBUTES.get(interaction, PBOND_ATTRIBUTES["default"])["radius"],
                bond_name=interaction,
                bond_dashes=PBOND_ATTRIBUTES.get(interaction, PBOND_ATTRIBUTES["default"])["dashes"],
            )
            commands.append(command)
            command = transparency_template.substitute(
                transparency=PBOND_ATTRIBUTES.get(interaction, PBOND_ATTRIBUTES["default"])["transparency"],
                model_id=f"{model_id}.{sub_model_ids.get(interaction, sub_model_id)}",
                target_spec="p"
            )
            commands.append(command)

    # print(sub_model_ids)

    if save_path is None:
        return commands

    save_commands_to_file(save_path, commands)

def add_ari(
    ari_df: pd.DataFrame | None = None,
    save_path: str | None = None
):
    """ Generate ChimeraX commands to add pseudobonds for atom-ring interactions.

    Args:

        ari_df (pd.DataFrame):
            DataFrame containing atom-ring interaction information.

        save_path (str | None, optional):
            Path to save the commands. If None, returns the commands as a list.

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
                interaction, PBOND_ATTRIBUTES["default"]
                ).get("color", "yellow"),
            bond_radius=PBOND_ATTRIBUTES.get(
                interaction, PBOND_ATTRIBUTES["default"]
                ).get("radius", 0.1),
            bond_dashes=PBOND_ATTRIBUTES.get(
                interaction, PBOND_ATTRIBUTES["default"]
                ).get("dashes", 6),
        )
        commands.append(command)

        command = transparency_template.substitute(
            model_id=f"{model_id}.{sub_model_ids[interaction]}",
            target_spec="p",
            transparency=PBOND_ATTRIBUTES.get(
                interaction, PBOND_ATTRIBUTES["default"]
                ).get("transparency", 0),
        )
        commands.append(command)

    # print(sub_model_ids)

    if save_path is None:
        return commands

    save_commands_to_file(save_path, commands)