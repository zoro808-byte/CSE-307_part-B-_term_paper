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

echo -e "\n>>> 3. Compiling Term Paper PDF via LaTeX..."
if [ -f "./bin/tectonic" ]; then
    ./bin/tectonic -o paper paper/paper.tex
    cp paper/paper.pdf paper/term_paper.pdf
    rm -f paper/paper.pdf
elif command -v tectonic &> /dev/null; then
    tectonic -o paper paper/paper.tex
    cp paper/paper.pdf paper/term_paper.pdf
    rm -f paper/paper.pdf
elif command -v pdflatex &> /dev/null; then
    (cd paper && pdflatex -interaction=nonstopmode paper.tex > /dev/null 2>&1 && bibtex paper > /dev/null 2>&1 && pdflatex -interaction=nonstopmode paper.tex > /dev/null 2>&1 && pdflatex -interaction=nonstopmode paper.tex > /dev/null 2>&1 && cp paper.pdf term_paper.pdf && rm -f paper.pdf paper.aux paper.log paper.bbl paper.blg paper.out)
else
    echo "Note: LaTeX engine not detected in PATH. Pre-compiled 4-page paper is ready at paper/term_paper.pdf"
fi

echo -e "\n======================================================================"
echo " ALL TASKS COMPLETED SUCCESSFULLY!"
echo " - Raw Results & Figures: results/"
echo " - Submission PDF:        paper/term_paper.pdf"
echo " - LaTeX Source:          paper/paper.tex"
echo "======================================================================"
