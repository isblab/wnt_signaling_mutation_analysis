# Mutation analysis for proteins in Wnt signaling

Analyzing structural effects of mutations involved in WNT signaling.

## Requirements/Dependencies
- [ChimeraX](https://www.cgl.ucsf.edu/chimerax/)
- [IMP_Toolbox](https://github.com/isblab/IMP_Toolbox)
- [Arpeggio (Docker version)](https://github.com/harryjubb/arpeggio?tab=readme-ov-file#using-the-public-docker-image)
- [PyMol](https://pymol.org/)
- [DDMut](https://biosig.lab.uq.edu.au/ddmut/api)
- Python 3.12+
- See `requirements.txt` for required Python packages

- Set up an alias for ChimeraX in your bash profile. Example:
  ```bash
  alias chimerax="flatpak run edu.ucsf.rbvi.ChimeraX"
  ```

## Workflow

> [!NOTE]
> All the following steps assumes that you are in the project root directory.
> (i.e. `wnt_signaling_mutation_analysis/`)

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

- Prepare the config file at `input/config.yaml` with the following
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

### Preparing input files for Arpeggio

- Make a directory to store the processed PDB files.

  ```bash
  mkdir -p output/processed_structures/
  ```

- Open ChimeraX and run the following commands in the ChimeraX CLI:
  Change the path to the script accordingly.

  ```
  cd /path/to/wnt_signaling_mutation_analysis
  runscript /path/to/scripts/preprocess.cxc
  ```

- This will generate the PDB files required for Arpeggio in the
  `./output/processed_structures/` directory.

### Generating mutant structures using DDMut

- Use the `get_mutant_structure.py` script to generate mutant structures
  using [DDMut API](https://biosig.lab.uq.edu.au/ddmut/api).

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

### Processing mutant structures

- Prepare a ChimeraX script `postprocess.cxc` to postprocess the
  downloaded mutant PDB files. See the `scripts/postprocess.cxc` file for
  reference.

> [!IMPORTANT]
> This step is necessary because Arpeggio may not properly add hydrogens
> to the structures. Additionally, we want to clean up the structures by removing
> non-protein atoms and cleaning alt-loc atoms.

- Run the postprocessing script in ChimeraX CLI as follows:

  ```
  cd /path/to/wnt_signaling_mutation_analysis
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
  python scripts/arpeggio_docker_wrapper.py \
      -i ./input/config.yaml \
      -o ./output/arpeggio_docker_results/ \
      -p ./output/processed_structures/
  ```

- You will find the Arpeggio results in the specified output directory.
  i.e., `output/arpeggio_docker_results/`.

> [!NOTE]
> You need `sudo` privileges to run the docker command.

### Analyzing changes in inter-atomic interactions

- Run the following command to analyze changes in inter-atomic interactions
  between wild-type and mutant structures.

  ```bash
  python scripts/arpeggio_analysis_wrapper.py \
      -i ./input/config.yaml \
      -r 6bd4_hydrogenated \
      -a ./output/arpeggio_docker_results/ \
      -l residue \
      -o ./output/ \
      -c
  ```

- `r` flag represents `result_head` which is the directory name in the
  `output/arpeggio_docker_results/` containing the Arpeggio results.

- `l` flag represents the analysis level. It can be `atom` or `residue`.

- You will find the analysis results (csv file) in the specified output directory.
  i.e., `output/pairwise_interactions`.

- If you used `-c` flag, you will also get ChimeraX `cxc` files to visualize the
  inter-atomic interactions.

### Figures

- Run the scripts in the `scripts/figures/` directory to generate figures
  for the analysis. Example:

  ```bash
  chimerax scripts/figures/figure_6BD4.cxc
  ```
  or in ChimeraX CLI:
  ```bash
  cd /path/to/wnt_signaling_mutation_analysis
  runscript scripts/figures/figure_6BD4.cxc
  ```

> [!TIP]
> You can modify and use `meta_wrapper.sh` script to run all these steps sequentially.

### References

- Cheng, J., Guido Novati, J. Pan, C. Bycroft, Akvilė Žemgulytė, T. Applebaum, A. Pritzel, Lai Hong Wong, Michał Zieliński, T. Sargeant, R.G. Schneider, A.W. Senior, J. Jumper, Demis Hassabis, P. Kohli, and Žiga Avsec. 2023. Accurate proteome-wide missense variant effect prediction with AlphaMissense. Science. 381. doi:https://doi.org/10.1126/science.adg7492.

- Jubb, H.C., A.P. Higueruelo, B. Ochoa-Montaño, W.R. Pitt, D.B. Ascher, and T.L. Blundell. 2017. Arpeggio: A Web Server for Calculating and Visualising Interatomic Interactions in Protein Structures. Journal of Molecular Biology. 429:365–371. doi:https://doi.org/10.1016/j.jmb.2016.12.004.

- Lomize, M.A., I.D. Pogozheva, H. Joo, H.I. Mosberg, and A.L. Lomize. 2011. OPM database and PPM web server: resources for positioning of proteins in membranes. Nucleic Acids Research. 40:D370–D376. doi:https://doi.org/10.1093/nar/gkr703.

- Meng, E.C., T.D. Goddard, E.F. Pettersen, G.S. Couch, Z.J. Pearson, J.H. Morris, and T.E. Ferrin. 2023. UCSF ChimeraX: Tools for Structure Building and Analysis. Protein Science: A Publication of the Protein Society. 32:e4792. doi:https://doi.org/10.1002/pro.4792.

- Zhou, Y., Q. Pan, Douglas, C.H.M. Rodrigues, and D.B. Ascher. 2023. DDMut: predicting effects of mutations on protein stability using deep learning. Nucleic Acids Research. 51. doi:https://doi.org/10.1093/nar/gkad472.

