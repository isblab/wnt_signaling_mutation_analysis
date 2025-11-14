# Mutation analysis for proteins in Wnt signaling pathway

Analyzing structural effects of mutations involved in WNT signaling.

## Requirements
- ChimeraX
- Python 3.12+
- See `requirements.txt` for required Python packages

## Workflow

### Mutations of interest

- Mutations of interest

| Proteins | Mutation | AF missense score |
|----------|----------|-------------------|
| FZD4     | L485F    | 0.9392            |
| WLS      | W234C    | 0.9935            |
| WLS      | M354T    | 0.7048            |

- The above mutations were selected based on the Alpha-missense cutoff score
  for pathogenicity.

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
    --input ../input/config.yaml \
    --output ../output/best_structures.csv \
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

### Preparing input files for Arpeggio web server

- Open ChimeraX and run the following commands in the ChimeraX CLI:
  Change the path to the script accordingly.

```
runscript /path/to/scripts/prepare_arpeggio_inputs.cxc
```

- This will generate the PDB files required for Arpeggio web server in the
  `../output/arpeggio_inputs/` directory.

- You will find one PDB file for WT and mutant each for FZD4 and WLS.
  For the mutants, the mutated residues are reoplaced using ChimeraX's
  `swapaa` command.

### Analyzing inter-atomic interactions using Arpeggio

- Upload the prepared PDB files to the Arpeggio web server
  (https://biosig.lab.uq.edu.au/arpeggioweb/) to analyze the inter-atomic
  interactions.

- > [!NOTE]
  > Analysis of all possible interactions may take a long time.
  > You may provide selection as follows to only analyze interactions involving
  > the mutated residue:
  > - For FZD4, provide selection: `/A/485/`
  > - For WLS, provide selection: `/B/234/` and `/B/354/`

- Download the results, extract and place them in the `../output/arpeggio_results/` directory.

### Analyzing changes in inter-atomic interactions