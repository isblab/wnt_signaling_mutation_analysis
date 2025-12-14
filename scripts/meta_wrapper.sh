#!/usr/bin/bash
# alias chimerax="flatpak run edu.ucsf.rbvi.ChimeraX"
# you also need to have pymol installed and accessible via `pymol` for some scripts

start=`date +%s.%N`

source ~/.bashrc
source ~/.bash_profile
source ~/.bashrc
shopt -s expand_aliases

###############################################################################
# Find best structures for FZD4 and WLS
###############################################################################
python scripts/fetch_best_structures.py \
--input input/config.yaml \
--output output/best_structures.csv \
# --overwrite

echo -n -e "$(printf '*%.0s' {1..100}) \n"

if [ -d "output/processed_structures/" ]; then
    echo "Directory output/processed_structures/ already exists."
else
    echo "Creating directory output/processed_structures/."
    mkdir -p output/processed_structures/
fi

echo -n -e "$(printf '*%.0s' {1..100}) \n"

###############################################################################
# Preprocess structures using ChimeraX
###############################################################################
echo "Running ChimeraX preprocessing script..."
chimerax --nogui --silent --exit --script scripts/preprocess.cxc
echo "Preprocessing completed."

echo -n -e "$(printf '*%.0s' {1..100}) \n"

###############################################################################
# Generate mutant structures using DDMut
###############################################################################
echo "Generating mutant structures using DDMut..."

python scripts/get_mutant_structure.py \
--pdb_path ./output/processed_structures/6bd4_hydrogenated.pdb \
--mutation L485F \
--chain_id A \
--output_dir ./output/ddmut \
--suffix 6BD4 \
--wait_time 120 \
--job_id 17654363667596319 \
--save_pdb

python scripts/get_mutant_structure.py \
--pdb_path ./output/processed_structures/7drt_hydrogenated.pdb \
--mutation W234C \
--chain_id A \
--output_dir ./output/ddmut \
--suffix 7DRT \
--wait_time 120 \
--job_id 17654357466477585 \
--save_pdb

python scripts/get_mutant_structure.py \
--pdb_path ./output/processed_structures/7drt_hydrogenated.pdb \
--mutation M354T \
--chain_id A \
--output_dir ./output/ddmut \
--suffix 7DRT \
--wait_time 120 \
--job_id 17654360362068248 \
--save_pdb

echo "Mutant structure generation completed."

echo -n -e "$(printf '*%.0s' {1..100}) \n"

###############################################################################
# Postprocess mutant structures using ChimeraX
###############################################################################
echo "Running ChimeraX postprocessing script..."
chimerax --nogui --silent --exit --script scripts/postprocess.cxc
echo "Postprocessing completed."

echo -n -e "$(printf '*%.0s' {1..100}) \n"

###############################################################################
# Run Arpeggio for analysing inter-atomic interactions
###############################################################################
echo "Running Arpeggio Docker wrapper script..."
python scripts/arpeggio_docker_wrapper.py \
-i ./input/config.yaml \
-o ./output/arpeggio_docker_results/ \
-p ./output/processed_structures/
echo "Arpeggio analysis completed."

echo -n -e "$(printf '*%.0s' {1..100}) \n"

###############################################################################
# Run Arpeggio analysis wrapper to extract interactions in WT and mutant
###############################################################################
echo "Running Arpeggio analysis wrapper script..."
python scripts/arpeggio_analysis_wrapper.py \
-i ./input/config.yaml \
-r 6bd4_hydrogenated \
-a ./output/arpeggio_docker_results/ \
-l residue \
-o ./output/ \
-c

python scripts/arpeggio_analysis_wrapper.py \
-i ./input/config.yaml \
-r L485F_6bd4_hydrogenated \
-a ./output/arpeggio_docker_results/ \
-l residue \
-o ./output/ \
-c

python scripts/arpeggio_analysis_wrapper.py \
-i ./input/config.yaml \
-r 7drt_hydrogenated \
-a ./output/arpeggio_docker_results/ \
-l residue \
-o ./output/ \
-c

python scripts/arpeggio_analysis_wrapper.py \
-i ./input/config.yaml \
-r W234C_7drt_hydrogenated \
-a ./output/arpeggio_docker_results/ \
-l residue \
-o ./output/ \
-c

python scripts/arpeggio_analysis_wrapper.py \
-i ./input/config.yaml \
-r M354T_7drt_hydrogenated \
-a ./output/arpeggio_docker_results/ \
-l residue \
-o ./output/ \
-c

echo "Arpeggio interaction analysis completed."
echo -n -e "$(printf '*%.0s' {1..100}) \n"

###############################################################################
# Generate figure assets using ChimeraX
###############################################################################
chimerax --exit --script ./scripts/figure/figure_6BD4.cxc
chimerax --exit --script ./scripts/figure/figure_6BD4_full.cxc
chimerax --exit --script ./scripts/figure/figure_7DRT_1.cxc
chimerax --exit --script ./scripts/figure/figure_7DRT_2.cxc
chimerax --exit --script ./scripts/figure/figure_7DRT_full.cxc
chimerax --exit --script ./scripts/figure/figure_6BD4_L485F.cxc
chimerax --exit --script ./scripts/figure/figure_7DRT_W234C.cxc
chimerax --exit --script ./scripts/figure/figure_7DRT_M354T.cxc
echo "Figure assets created."

echo -n -e "$(printf '*%.0s' {1..100}) \n"
echo "All tasks completed."

end=`date +%s.%N`

runtime=$( echo "$end - $start" | bc -l )
echo "Total runtime: $runtime seconds"