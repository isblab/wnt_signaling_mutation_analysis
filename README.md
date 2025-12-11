# Mutation analysis for proteins in Wnt signaling

Analyzing structural effects of mutations involved in WNT signaling.

## Requirements
- ChimeraX
- IMP_Toolbox (https://github.com/isblab/IMP_Toolbox)
- Python 3.12+
- See `requirements.txt` for required Python packages

## Workflow

> [!NOTE]
> All the following steps assumes that you are in the `scripts/` directory.

### Mutations of interest

- Mutations of interest

  | Proteins | Mutation | AF missense score |
  |----------|----------|-------------------|
  | FZD4     | L485F    | 0.9392            |
  | WLS      | W234C    | 0.9935            |
  | WLS      | M354T    | 0.7048            |

- The above mutations were selected based on the Alpha-missense cutoff score
  for pathogenicity.
- Alpha-missense scores were obtained from the following link.
  ```
  "https://alphafold.ebi.ac.uk/files/AF-<UNIPROT_ID>-F1-aa-substitutions.csv"
  ```

### Find best structures from PDB

- Prepare the config file at `../input/config.yaml` with the following
  content:

  ```yaml
  protein_uniprot_map:
    WNT2: P09544
    FZD4: Q9ULV1
    WLS: Q5T9L3
  ```

  ```bash
  python scripts/fetch_best_structures.py \
      --input input/config.yaml \
      --output output/best_structures.csv \
      --overwrite
  ```

- Best structures chosen are follows:

  | Protein | UniProt ID | PDB ID | Chain ID | Resolution (Å) |
  |---------|------------|--------|----------|----------------|
  | WLS     | Q5T9L3     | 7DRT   | B        | 2.2            |
  | FZD4    | Q9ULV1     | 6BD4   | A        | 2.4            |
  | WNT2    | P09544     | -      | -        | -              |

- The structures were chosen based on the resolution and coverage of the protein sequence.
- WNT2 does not have any experimental structure available in PDB as of November 2025.

### Preparing input files for Arpeggio and Missense3D-TM web server

- Make a directory to store the processed PDB files.

  ```bash
  mkdir -p ../output/processed_structures/
  ```

- Open ChimeraX and run the following commands in the ChimeraX CLI:
  Change the path to the script accordingly.

  ```
  runscript /path/to/scripts/preprocess.cxc
  ```

- This will generate the PDB files required for Arpeggio web server in the
  `../output/processed_structures/` directory.

### Generating mutant structures using DDMut

- Use the `get_mutant_structure.py` script to generate mutant structures
  using DDMut API (https://biosig.lab.uq.edu.au/ddmut/api).

  ```bash
  python scripts/get_mutant_structure.py \
      --pdb_path ./output/processed_structures/6bd4_hydrogenated.pdb \
      --mutation L485F \
      --chain_id A \
      --output_dir ./output/ddmut \
      --suffix 6BD4 \
      --wait_time 120 \
      --save_pdb
  ```

- Change the `--pdb_path`, `--mutation`, `--chain_id`, `--output_dir`,
  `--suffix`, and `--job_id` arguments accordingly.

- Alternatively, use the web server at
  `https://biosig.lab.uq.edu.au/ddmut/` to get the mutant structures.

### Generating mutant structures using Missense3D-TM (deprecated)

- Upload the prepared PDB files to the Missense3D-TM web server
  (https://missense3d.bc.ic.ac.uk/) to get the mutant structures.

- Download and extract the zipped results. You will find the mutant PDB files in
  the `SCWRL/` directory inside the extracted folder as `<MUTATION>_<filename>.pdb`
  if you uploaded the wild-type structure as `<filename>.pdb`.

### Processing mutant structures

- Prepare a ChimeraX script `postprocess.cxc` to postprocess the
  downloaded mutant PDB files. See the `scripts/postprocess.cxc` file for
  reference.

> [!IMPORTANT]
> This step is necessary because Arpeggio does always not properly add hydrogens
> to the structures. And also, we want to clean up the structures by removing
> non-protein atoms and cleaning alt-loc atoms.

- Run the postprocessing script in ChimeraX CLI as follows:

  ```
  runscript /path/to/scripts/postprocess.cxc
  ```

- This will generate input PDB files required for Arpeggio in the directory
  `output/processed_structures`.

### Analyzing inter-atomic interactions using Arpeggio

- Set up the Arpeggio docker image by following the instructions at
  [Using the public Docker image (Arpeggio)](https://github.com/harryjubb/arpeggio?tab=readme-ov-file#using-the-public-docker-image).

- We use docker version of Arpeggio to analyze inter-atomic interactions. Run
  the following command.

  ```bash
  python arpeggio_docker_wrapper.py \
      -i ../input/config.yaml \
      -o ../output/arpeggio_docker_results/ \
      -p ../output/processed_structures/
  ```

- You will find the Arpeggio results in the specified output directory.
  i.e., `../output/arpeggio_docker_results/`.

> [!NOTE]
> You need `sudo` privileges to run the docker command.

> [!CAUTION]
> Analysis of all possible interactions may take a long time.
> You may provide selection as follows to only analyze interactions involving
> the mutated residue:
> - For FZD4, provide selection: `/A/485/`
> - For WLS, provide selection: `/B/234/` and `/B/354/`
>
> See the `input/config.yaml` file for reference.

### Analyzing changes in inter-atomic interactions

- Run the following command to analyze changes in inter-atomic interactions
  between wild-type and mutant structures.

  ```bash
  python arpeggio_analysis_wrapper.py \
      -i ../input/config.yaml \
      -r 6bd4_hydrogenated \
      -a ../output/arpeggio_docker_results/ \
      -l residue \
      -o ../output/ \
      -c
  ```

- `r` flag represents `result_head` which is the directory name in the
  `../output/arpeggio_docker_results/` containing the Arpeggio results.

- `l` flag represents the analysis level. It can be `atom` or `residue`.

- You will find the analysis results (csv file) in the specified output directory.
  i.e., `../output/pairwise_interactions`.

- If you used `-c` flag, you will also get ChimeraX `cxc` files to visualize the
  inter-atomic interactions.