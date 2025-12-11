from IMP_Toolbox.utils import request_session, write_json, read_json
import argparse
import os
import shlex
import subprocess
import json

req_sess = request_session(max_retries=3)

DDMUT_URL = "https://biosig.lab.uq.edu.au/ddmut"

def submit_ddmut_job(
    pdb_path: str,
    mutation: str,
    chain_id: str,
    reverse_mutation: bool = False,
):
    """ Submit a DDMut job for a single mutation

    Args:

        pdb_path (str):
            Path to the PDB file

        mutation (str):
            Mutation in the format 'A123B' where A is the original residue,
            123 is the position, and B is the new residue

        chain_id (str):
            Chain ID in the PDB in which the mutation is to be made

        reverse_mutation (bool, optional):
            Whether to perform reverse mutation. Defaults to False.

    Returns:

        job_id (str):
            Job ID of the submitted DDMut job
    """

    ddmut_api_url = f"{DDMUT_URL}/api/prediction_single"

    # curl_cmd = (
    #     f'curl {ddmut_api_url} -X POST -i '
    #     f'-F "pdb_file=@{pdb_path}" '
    #     f'-F "mutation={mutation}" '
    #     f'-F "chain={chain_id}" '
    #     f'-F "reverse={str(reverse_mutation)}"'
    # )

    response = req_sess.post(
        ddmut_api_url,
        files={
            'pdb_file': open(pdb_path, 'rb')
        },
        data={
            'mutation': mutation,
            'chain': chain_id,
            'reverse': str(reverse_mutation)
        }
    )

    if response.status_code != 200:
        raise Exception(
            f"""DDMut job submission failed with status code
            {response.status_code}: {response.text}"""
        )

    job_id = response.json().get("job_id", None)

    return job_id

def get_ddmut_result(
    job_id: str,
    wait_time: int = 0
):
    """ Retrieve the result of a DDMut job

    Args:

        job_id (str):
            Job ID of the DDMut job

        wait_time (int, optional):
            Time to wait (in seconds) before retrieving the result

    Returns:
        result (dict):
            Result of the DDMut job
    """

    ddmut_result_url = f"{DDMUT_URL}/api/prediction_single"

    curl_cmd = f'curl {ddmut_result_url} -X GET -F "job_id={job_id}"'
    curl_cmd = shlex.split(curl_cmd)

    if wait_time > 0:
        print(f"Waiting for {wait_time} seconds before retrieving DDMut result...")
        import time
        time.sleep(wait_time)

    process = subprocess.Popen(
        curl_cmd,
        shell=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        print(f'{ddmut_result_url}/{job_id}')
        raise Exception(
            f"DDMut result retrieval failed with error: {stderr.decode('utf-8')}"
            "Check the above URL for more details."
        )

    # result = stdout.decode('utf-8')
    result = json.loads(stdout.decode('utf-8'))

    return result

def get_ddmut_pse_session(
    job_id: str,
    chain_id: str,
    mutation: str,
    which: str = "mt",
):
    """ Retrieve the PyMOL session file for a DDMut job

    Args:

        job_id (str):
            Job ID of the DDMut job

        chain_id (str):
            Chain ID in the PDB

        mutation (str):
            Mutation in the format 'A123B' where A is the original residue,
            123 is the position, and B is the new residue

        which (str, optional):
            Which structure to retrieve ('mt' for mutant, 'wt' for wild-type)

    Returns:

        pse_session (bytes):
            Content of the PyMOL session file
    """

    ddmut_pse_url = (
        f"{DDMUT_URL}/download_pymol_session/{job_id}/{chain_id}/{mutation}/{which}"
    )
    print(f"Fetching pymol session from {ddmut_pse_url}")

    response = req_sess.get(ddmut_pse_url)
    if response.status_code != 200:
        raise Exception(
            f"""DDMut pse session retrieval failed with status code
            {response.status_code}: {response.text}"""
        )
    pse_session = response.content

    return pse_session

def pse_to_pdb(pse_file_path: str):
    """ Save the PDB file from a PyMOL session file

    Args:

        pse_file_path (str):
            Path to the PyMOL session file
    """

    assert os.path.exists(pse_file_path); (
        f"""{pse_file_path} does not exist.
        Use `get_ddmut_pse_session` to fetch the PyMOL session first."""
    )

    pymol_cmd = (
        f"pymol -cq {pse_file_path} "
        f"-d 'save {pse_file_path.replace('.pse', '.pdb')}'"
    )
    process = subprocess.Popen(
        shlex.split(pymol_cmd),
        shell=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    _stdout, stderr = process.communicate()

    if process.returncode != 0:
        raise Exception(
            f"""Saving PDB from PyMOL session failed with error:
            {stderr.decode('utf-8')}"""
        )
    else:
        print(f"Saved PDB file to {pse_file_path.replace('.pse', '.pdb')}")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Get mutant structure using DDMut"
    )
    parser.add_argument(
        "--pdb_path",
        type=str,
        required=False,
        default="./output/processed_structures/6bd4_hydrogenated.pdb",
        help="Path to the PDB file of the wild-type structure",
    )
    parser.add_argument(
        "--mutation",
        type=str,
        required=False,
        default="L485F",
        help="Mutation in the format 'A123B' where A is the original residue, \
            123 is the position, and B is the new residue",
    )
    parser.add_argument(
        "--chain_id",
        type=str,
        required=False,
        default="A",
        help="Chain ID where the mutation is located",
    )
    parser.add_argument(
        "--reverse",
        action="store_true",
        help="Whether to perform reverse mutation (mutant to wild-type)",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="./output/ddmut",
        help="Path to save the PyMOL session file",
    )
    parser.add_argument(
        "--suffix",
        type=str,
        default="6BD4",
        help="Suffix for output files",
    )
    parser.add_argument(
        "--job_id",
        type=str,
        required=False,
        default=None,
        help="DDMut job ID to retrieve results for",
    )
    parser.add_argument(
        "--wait_time",
        type=int,
        required=False,
        default=120,
        help="Time to wait (in seconds) before retrieving DDMut result",
    )
    parser.add_argument(
        "--save_pdb",
        action="store_true",
        help="Whether to save the mutant PDB file (requires PyMOL)",
    )

    args = parser.parse_args()

    ###########################################################################
    # Submit DDMut job if job_id is not provided
    ###########################################################################
    if args.job_id is None:

        wait_time = 120  # seconds
        job_id = submit_ddmut_job(
            pdb_path=args.pdb_path,
            mutation=args.mutation,
            chain_id=args.chain_id,
            reverse_mutation=args.reverse,
        )

        print(f"Submitted DDMut job with ID: {job_id}")

    else:
        wait_time = 0
        job_id = args.job_id

    ###########################################################################
    # Fetch and save the DDMut result
    ###########################################################################
    ddmut_result_path = os.path.join(
        args.output_dir,
        f"ddmut_{job_id}_{args.suffix}_{args.mutation}_result.json"
    )

    if not os.path.exists(ddmut_result_path):
        result = get_ddmut_result(job_id, wait_time)
        write_json(ddmut_result_path, result)

    else:
        result = read_json(ddmut_result_path)

    print(f"DDMut result: {result}")

    ###########################################################################
    # Fetch and save the PyMOL session file for the mutant structure
    ###########################################################################
    pse_file_path = os.path.join(
        args.output_dir,
        f"ddmut_{job_id}_{args.suffix}_{args.mutation}_mutant.pse"
    )

    if not os.path.exists(pse_file_path):

        pse_session = get_ddmut_pse_session(
            job_id=job_id,
            chain_id=args.chain_id,
            mutation=args.mutation,
            which="mt",
        )

        os.makedirs(args.output_dir, exist_ok=True)

        with open(pse_file_path, "wb") as f:
            f.write(pse_session)

        print(f"Saved DDMut mutant PyMOL session to {pse_file_path}")

    else:
        print(f"DDMut mutant PyMOL session already exists at {pse_file_path}")

    ###########################################################################
    # Save the mutant PDB file
    ###########################################################################
    if args.save_pdb:
        pse_to_pdb(pse_file_path)