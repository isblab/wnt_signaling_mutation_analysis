from string import Template
import argparse
import yaml
import os
import warnings
from arpeggio_constants import DOCKER_BASE_COMMAND, DOCKER_CONTAINER_PATH

if __name__ == "__main__":

    args = argparse.ArgumentParser(
        description="Run Arpeggio Docker container on a given PDB file."
    )
    args.add_argument(
        "-i",
        "--input_config",
        type=str,
        required=False,
        default="../input/config.yaml",
        help="Path to the YAML configuration file."
    )
    args.add_argument(
        "-o",
        "--output_dir",
        type=str,
        required=False,
        default=f"../output/arpeggio_docker_results",
        help="Path to the output directory to store results."
    )
    args.add_argument(
        "-p",
        "--processed_structures_dir",
        type=str,
        required=False,
        default=f"../output/processed_structures",
        help="Path to the directory containing processed PDB structures."
    )
    args = args.parse_args()

    docker_base_command = Template(DOCKER_BASE_COMMAND)
    container_path = DOCKER_CONTAINER_PATH

    ###########################################################################
    # Load input configuration
    ###########################################################################
    with open(args.input_config, 'r') as f:
        config = yaml.safe_load(f)

    arpeggio_results = config["arpeggio_results"]
    docker_result_dir = os.path.abspath(args.output_dir)


    for result_head, result_metadata in arpeggio_results.items():

        path_to_mount = os.path.join(docker_result_dir, result_head)

        processed_struct_path = os.path.join(
            os.path.abspath(args.processed_structures_dir), f"{result_head}.pdb"
        )
        if not os.path.isfile(processed_struct_path):
            warnings.warn(
                f"Processed structure file not found for \
                {result_head}: {processed_struct_path}. Skipping."
            )

        os.makedirs(path_to_mount, exist_ok=True)
        # copy processed structure to mount path
        target_path = os.path.join(path_to_mount, f"{result_head}.pdb")
        os.system(f"cp {processed_struct_path} {target_path}")

        docker_command = docker_base_command.substitute(
            path_to_mount=path_to_mount,
            container_path=container_path,
            input_pdb_path=os.path.join(container_path, f"{result_head}.pdb"),
        )

        arpeggio_sel = " ".join(result_metadata.get("selections", [])) or ""
        if arpeggio_sel:
            docker_command = docker_command.strip() + f" -s {arpeggio_sel}"

        print(f"Running Docker command for {result_head}:\n{docker_command}\n")
        os.system(docker_command)

