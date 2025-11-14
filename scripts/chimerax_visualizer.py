from string import Template
import pandas as pd

def add_ring_centroids(
    rings_df: pd.DataFrame,
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

    command_template = Template(
        "marker #$marker_model_id position $x,$y,$z color $marker_color radius $marker_radius"
    )
    marker_model_id = "2"
    marker_color = "white"
    marker_radius = 0.1
    commands = []
    for _, row in rings_df.iterrows():
        x, y, z = row["ring_centroid"].split(",")
        command = command_template.substitute(
            marker_model_id=marker_model_id,
            x=x,
            y=y,
            z=z,
            marker_color=marker_color,
            marker_radius=marker_radius
        )
        commands.append(command)

    if save_path is None:
        return commands

    with open(save_path, 'w') as f:
        for command in commands:
            f.write(command + "\n")

def add_ring_interactions(
    ri_df: pd.DataFrame,
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

    command_template = Template(
        "pbond #$marker1_spec#$marker2_spec color $bond_color radius $bond_radius name $bond_name dashes $bond_dashes"
    )
    marker_model_id = 2
    bond_color = "yellow"
    bond_radius = 0.3
    bond_dashes = 30
    commands = []
    for _, row in ri_df.iterrows():
        marker1_id = row["marker_id_1"]
        marker2_id = row["marker_id_2"]
        marker1_spec = f"{marker_model_id}/M:{marker1_id}@M"
        marker2_spec = f"{marker_model_id}/M:{marker2_id}@M"
        bond_name = row["interaction_type"]
        command = command_template.substitute(
            marker1_spec=marker1_spec,
            marker2_spec=marker2_spec,
            bond_color=bond_color,
            bond_radius=bond_radius,
            bond_name=bond_name,
            bond_dashes=bond_dashes
        )
        commands.append(command)

    if save_path is None:
        return commands

    with open(save_path, 'w') as f:
        for command in commands:
            f.write(command + "\n")