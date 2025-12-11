from IMP_Toolbox.utils import request_session
import argparse
import os

req_sess = request_session(max_retries=3)

def get_opm_pdb(pdb_id: str) -> bytes:
    """ Fetches the PDB structure of a membrane protein from the OPM database
    with membrane boundaries.

    Args:
        pdb_id (str): PDB ID of the protein.

    Returns:
        bytes: Content of the PDB file.
    """

    opm_pdb_url = f"https://biomembhub.org/shared/opm-assets/pdb/{pdb_id.lower()}.pdb"

    response = req_sess.get(opm_pdb_url)

    if response.status_code != 200:
        raise Exception(
            f"""Fetching structure from OPM database failed with status code
            {response.status_code}: {response.content}"""
        )

    return response.content


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Fetch membrane protein structure from OPM database."
    )
    parser.add_argument(
        "-p",
        "--pdb_id",
        type=str,
        required=False,
        default="6bd4",
        help="PDB ID of the membrane protein to fetch from OPM.",
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        type=str,
        required=False,
        default="./output/opm_structures",
        help="Path to save the fetched PDB structure.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing files.",
    )
    args = parser.parse_args()

    pdb_content = get_opm_pdb(args.pdb_id)

    os.makedirs(args.output_dir, exist_ok=True)

    opm_pdb_path = os.path.join(
        args.output_dir,
        f"{args.pdb_id}_opm.pdb"
    )

    if os.path.exists(opm_pdb_path) and not args.overwrite:
        print(
            f"""OPM structure for {args.pdb_id} already exists at {opm_pdb_path}.
            Use --overwrite to replace."""
        )
        exit(0)

    with open(opm_pdb_path, 'wb') as f:
        f.write(pdb_content)

    print(f"OPM structure for {args.pdb_id} saved to {opm_pdb_path}")