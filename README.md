# CSE-307: Operating Systems — Term Paper (Section B)
## Track 2: Disk Scheduling — Learned Scheduler Selector

**Course:** CSE-307 (Operating Systems), Part B  
**Track:** Track 2 — Disk Scheduling: Learned Scheduler Selector  
**Paper PDF:** [`paper/term_paper.pdf`](paper/term_paper.pdf)  
**LaTeX Source:** [`paper/paper.tex`](paper/paper.tex)  

---

### Project Overview

For this term paper, I implemented and evaluated a **learning-augmented disk scheduler selector**. 

In classical operating systems, disk scheduling algorithms (FCFS, SSTF, SCAN, C-SCAN) are completely static. However, no single policy is optimal for every workload:
- **FCFS** is simple and fair, but seek times explode when requests are spread randomly across the disk platter.
- **SSTF** greedily minimizes head movement for nearby tracks, but it can easily starve requests that are far away.
- **SCAN** and **C-SCAN** guarantee bounded waiting times, but they force the head to sweep across the disk (often all the way to cylinder boundaries), which wastes unnecessary seek time when requests are tightly clustered.

To make things harder, real-world workloads are **non-stationary**—access patterns shift abruptly (e.g. streaming a file sequentially, followed by random database queries, followed by bursty index writes). 

Instead of hardcoding a single policy, I built an adaptive selector that inspects a sliding window of pending requests (e.g. $K=15$), extracts spatial and directional features (like track variance, platter span, head distance, and monotonicity), and predicts which classical algorithm will yield the lowest seek distance, along with a confidence score.

---

### What I Implemented

1. **Four Classical Schedulers (`src/schedulers.py`)**:
   - `FCFS`: Dispatches in exact arrival order.
   - `SSTF`: Dispatches nearest request to the current head.
   - `SCAN`: Elevator sweep in the current direction, reversing at boundary.
   - `C-SCAN`: Unidirectional sweep, returning directly to track 0 without servicing on return.
   - Verified against the textbook reference example from Silberschatz (*Operating System Concepts*, 10th ed., p. 456): on `[98, 183, 37, 122, 14, 124, 65, 67]` starting at head 53, my implementation yields exact textbook results (FCFS: 640, SSTF: 236, SCAN: 331, C-SCAN: 382).

2. **Synthetic Workload Generator with Dynamic Shift (`src/workload.py`)**:
   - Generates three canonical workload patterns: **Sequential** (stride 1–4, spatial locality), **Uniform Random** (independent uniform across disk), and **Bursty Clustered** (Gaussian hotspots around multiple centers).
   - Generates a continuous 1,000-request **dynamic shift timeline** (Phase 1: Sequential $\to$ Phase 2: Random $\to$ Phase 3: Bursty $\to$ Phase 4: Mixed).

3. **Window Feature Extractor (`src/features.py`)**:
   - Extracts 11 lightweight numerical features per request window: normalized variance ($\sigma^2$), span, mean distance from head, directional bias, monotonicity score, mean step size, and cluster density.

4. **Pure-Python Random Forest & Calibration (`src/models.py`, `src/learned_selector.py`)**:
   - Implemented a Random Forest ensemble in pure Python (no external dependencies required like `pip`, `scikit-learn`, etc. so the grader can run it immediately on any machine).
   - Outputs posterior class probabilities, winner confidence, and computes Expected Calibration Error (ECE).

5. **Bonus Track: Decision Explainer & Confidence (+10 Points) (`src/explainer.py`)**:
   - Produces natural-language rationales explaining *why* a particular algorithm was chosen (e.g. tight clustering vs. broad dispersion vs. directional sweep).
   - Computes a self-rated explanation confidence score and compares it against actual decision correctness.

6. **Automated Visualization & LaTeX Term Paper (`src/visualizer.py`, `paper/paper.tex`)**:
   - Generates 4 publication figures in `results/` using Pillow.
   - Typesets a 4-page IEEE-style PDF term paper saved at `paper/term_paper.pdf` via LaTeX (`paper/paper.tex` and `paper/references.bib`).

---

### Experimental Results

#### 1. Total Seek Distance Comparison

All runs evaluated on a 200-cylinder disk ($0-199$). Window size $K = 15$.

| Workload Type | FCFS | SSTF | SCAN | C-SCAN | **Learned Selector** | **Oracle (Ideal)** | Accuracy |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Sequential** (600 req) | 1,581 | 1,581 | 5,511 | 10,323 | **1,581** | 1,581 | **100.0%** |
| **Uniform Random** (600 req) | 38,841 | 7,898 | 9,524 | 15,080 | **7,634** | 7,576 | **95.0%** |
| **Bursty Clustered** (600 req) | 9,682 | 4,676 | 7,790 | 13,118 | **4,676** | 4,676 | **100.0%** |
| **Dynamic Shift** (1,000 req) | 29,705 | 8,561 | 13,015 | 21,148 | **8,561** | 8,396 | **93.9%** |

#### 2. What Happened Under the Shift and Why?

- **Sequential Phase**: FCFS and SSTF performed equally well (1,581 cylinders). Classical SCAN and C-SCAN degraded heavily (5,511 and 10,323 cylinders). This happens because classical SCAN semantics require sweeping all the way to cylinder 199 before reversing; on a tightly localized sequence, this causes massive wasted seek distance.
- **Random Phase**: FCFS suffered catastrophic thrashing (38,841 cylinders, nearly 5x worse than SSTF). The Learned Selector achieved 7,634 cylinders, beating fixed static schedulers and closely matching the Oracle (7,576).
- **Bursty Phase**: SSTF and the Learned Selector cut seek distance by **51.7% compared to FCFS** and **39.9% compared to SCAN**.
- **Continuous 1,000-Request Shift**: The Learned Selector dynamically adapted to each phase, achieving **8,561 cylinders**. That is a **71.2% seek reduction vs. FCFS** and **34.2% reduction vs. SCAN**, within **1.9% of the Oracle lower bound**.

#### 3. Is the Confidence Score Well-Calibrated?

The brief asks:
> *"Whether the classifier's confidence score is actually higher on the cases it gets right — i.e., is it well calibrated?"*

**Yes, the results confirm that the confidence score is well-calibrated:**
- **Mean Confidence on Correct Decisions:** `91.93%` (0.9193)
- **Mean Confidence on Incorrect Decisions:** `79.14%` (0.7914)
- **Confidence Calibration Gap (Margin):** `+12.79%` (+0.1279)
- **Expected Calibration Error (ECE):** `0.0711`

When the model is confident ($\ge 90\%$), its empirical accuracy is very high. When an edge case occurs (e.g. at phase transitions), the confidence score drops significantly to ~79%. This is valuable in an OS kernel because low confidence can serve as a safety trigger to revert to starvation-free SCAN.

#### 4. Bonus Track: Decision Explanations & Self-Rated Confidence

Here are sample explanations generated by the explainer module during the timeline shift:
- **Window #00 (Sequential):** Selected **SSTF** (Correct, Conf: 0.99)  
  *Rationale:* Requests are tightly clustered in cylinder space (span=21.1%, normalized var=0.017), minimizing greedy nearest-neighbor seek penalties. Current head is close to cluster centroid.
- **Window #18 (Random):** Selected **SSTF** (Suboptimal, Conf: 0.60)  
  *Rationale:* Greedy nearest-request dispatch yields the shortest local trajectory across the pending queue.
- **Window #35 (Bursty):** Selected **SSTF** (Correct, Conf: 0.84)  
  *Rationale:* Greedy nearest-request dispatch yields shortest local trajectory; head situated close to active cluster centroid.

**Explanation Calibration Result:**
- Mean Explanation Confidence when correct: **0.8425**
- Mean Explanation Confidence when incorrect: **0.7485**
- Calibration Margin: **+0.0940** (+9.4% higher confidence when correct)

---

### Project Structure

```text
os_b/
├── README.md                      # This report file
├── main.py                        # Main runner for all experiments
├── run_experiments.sh             # 1-click execution script
├── src/
│   ├── schedulers.py              # FCFS, SSTF, SCAN, C-SCAN implementations
│   ├── workload.py                # Synthetic workload generators & shift timeline
│   ├── features.py                # 11-feature window extractor
│   ├── models.py                  # Random Forest & ECE calibration calculation
│   ├── learned_selector.py        # Meta-scheduler selector & online simulation
│   ├── explainer.py               # Bonus track: Natural language rationale generator
│   └── visualizer.py              # Chart generator using Pillow
├── tests/
│   ├── test_schedulers.py         # Unit tests checking textbook reference values
│   └── test_models.py             # Feature and model unit tests
├── results/
│   ├── benchmark_summary.csv      # Raw summary table across all workloads
│   ├── phase_shift_breakdown.csv  # Detailed phase-by-phase seek numbers
│   ├── calibration_data.csv       # Calibration bin table
│   ├── sample_explanations.csv    # Natural language explanations log
│   ├── fig1_seek_comparison.png   # Seek distance bar chart
│   ├── fig2_shift_timeline.png    # Workload shift timeline trajectory plot
│   ├── fig3_calibration_curve.png # Reliability diagram
│   └── fig4_feature_importance.png# Feature importance chart
└── paper/
    ├── term_paper.pdf             # 4-page compiled IEEE term paper PDF
    ├── paper.tex                  # Formal LaTeX paper source
    ├── references.bib             # Bibliography file
    ├── fig1_seek_comparison.png   # Benchmark seek comparison chart
    ├── fig2_shift_timeline.png    # Workload shift timeline trajectory plot
    ├── fig3_calibration_curve.png # Reliability diagram
    └── fig4_feature_importance.png# Feature importance chart
```

---

### How to Run

The codebase is 100% self-contained and uses standard Python 3 with PIL/Pillow for figures. No external ML packages are required.

```bash
# Clone or navigate to the directory
cd os_b

# Option 1: Run the full master script (runs tests, benchmarks, regenerates charts & compiles LaTeX paper)
bash run_experiments.sh

# Option 2: Run benchmarks directly
python3 main.py

# Option 3: Run unit tests
python3 tests/test_schedulers.py
python3 tests/test_models.py

# Option 4: Recompile the term paper PDF via LaTeX
./bin/tectonic -o paper paper/paper.tex && cp paper/paper.pdf paper/term_paper.pdf && rm -f paper/paper.pdf
```

---

### AI Assistance Disclosure

As stated in the course brief:
> *"Using an AI coding assistant (ChatGPT, Claude, Copilot, etc.) for implementation help is allowed, but the experimental design, results, and analysis must be your own. Briefly disclose any AI assistance used in your README."*

- **AI Tools Used:** ChatGPT, Gemini.
- **How I Used It:** I used the assistant to help Pillow drawing coordinates, and double-column LaTeX layout formatting.
