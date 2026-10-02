#!/usr/bin/env bash
set -e

echo "======================================================================"
echo " CSE-307 OPERATING SYSTEMS TERM PAPER: MASTER PIPELINE"
echo " Track 2: Learned Disk Scheduler Selector"
echo "======================================================================"

echo -e "\n>>> 1. Running Unit Tests (Textbook Verification)..."
python3 tests/test_schedulers.py
python3 tests/test_models.py

echo -e "\n>>> 2. Running Full Benchmarks & Generating Figures..."
python3 main.py

echo -e "\n>>> 3. Compiling Term Paper PDF..."
python3 paper/generate_pdf.py

echo -e "\n======================================================================"
echo " ALL TASKS COMPLETED SUCCESSFULLY!"
echo " - Raw Results & Figures: results/"
echo " - Submission PDF:        paper/term_paper.pdf"
echo " - LaTeX Source:          paper/paper.tex"
echo "======================================================================"
