import sys
import argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from src.experiments import run_all_experiments

def main():
    parser = argparse.ArgumentParser(description='CSE-307 Term Paper: Learning-Augmented Disk Scheduler Selector')
    parser.add_argument('--cylinders', type=int, default=200, help='Total disk cylinders (default: 200)')
    parser.add_argument('--window-size', type=int, default=15, help='Request window size (default: 15)')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for reproducibility (default: 42)')
    parser.add_argument('--results-dir', type=str, default='results', help='Directory to save figures and CSVs')
    args = parser.parse_args()
    results = run_all_experiments(total_cylinders=args.cylinders, window_size=args.window_size, seed=args.seed, results_dir=args.results_dir)
    print('\n[SUCCESS] Term paper experiments executed cleanly and verified.')
if __name__ == '__main__':
    main()
