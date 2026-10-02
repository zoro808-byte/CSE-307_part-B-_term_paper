import csv
import json
from pathlib import Path
from typing import Dict, Any, List
from src.schedulers import SCHEDULERS, evaluate_all
from src.workload import WorkloadGenerator
from src.learned_selector import LearnedSchedulerSelector
from src.explainer import DecisionExplainer
from src.visualizer import plot_bar_chart, plot_calibration_diagram, plot_trajectory_shift, plot_feature_importances

def run_all_experiments(total_cylinders: int=200, window_size: int=15, seed: int=42, results_dir: str='/home/naeem/Downloads/os_b/results') -> Dict[str, Any]:
    print('=' * 70)
    print('CSE-307 OPERATING SYSTEMS TERM PAPER: EXPERIMENT BENCHMARK SUITE')
    print('Track 2: Learned Disk Scheduler Selector')
    print('=' * 70)
    out_dir = Path(results_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    print('\n[1/5] Training Random Forest model on synthetic windows...')
    selector = LearnedSchedulerSelector(total_cylinders=total_cylinders, model_type='random_forest', window_size=window_size, seed=seed)
    train_meta = selector.train(samples_per_type=350)
    print(f"  -> Model trained on {train_meta['total_samples']} windows (train accuracy: {train_meta['train_accuracy'] * 100:.1f}%)")
    print(f"  -> Class counts: {train_meta['class_distribution']}")
    print('\n[2/5] Running static workloads (Sequential, Random, Bursty)...')
    gen = WorkloadGenerator(total_cylinders=total_cylinders, seed=seed)
    static_workloads = {'Sequential': gen.generate_sequential(600), 'Uniform Random': gen.generate_random(600), 'Bursty Clustered': gen.generate_bursty_clustered(600)}
    benchmark_summary = {}
    chart_series = {name: [] for name in ['FCFS', 'SSTF', 'SCAN', 'C-SCAN', 'Learned Selector', 'Oracle']}
    for w_name, reqs in static_workloads.items():
        sim_res = selector.run_simulation(reqs, initial_head=50)
        c_seeks = sim_res['cumulative_seeks']
        benchmark_summary[w_name] = {'FCFS': c_seeks['FCFS'], 'SSTF': c_seeks['SSTF'], 'SCAN': c_seeks['SCAN'], 'C-SCAN': c_seeks['C-SCAN'], 'Learned Selector': c_seeks['LEARNED'], 'Oracle': c_seeks['ORACLE'], 'Accuracy': sim_res['accuracy'], 'ECE': sim_res['calibration']['ece']}
        for sched_key, s_val in [('FCFS', c_seeks['FCFS']), ('SSTF', c_seeks['SSTF']), ('SCAN', c_seeks['SCAN']), ('C-SCAN', c_seeks['C-SCAN']), ('Learned Selector', c_seeks['LEARNED']), ('Oracle', c_seeks['ORACLE'])]:
            chart_series[sched_key].append(s_val)
        print(f" -> {w_name:18s} | FCFS: {c_seeks['FCFS']:5d} | SSTF: {c_seeks['SSTF']:5d} | SCAN: {c_seeks['SCAN']:5d} | C-SCAN: {c_seeks['C-SCAN']:5d} | Learned: {c_seeks['LEARNED']:5d} (Oracle: {c_seeks['ORACLE']:5d})")
    print('\n[3/5] Simulating dynamic 1,000-request workload shift...')
    shift_reqs_objs, phase_meta = gen.generate_shifting_timeline({'sequential': 250, 'random': 250, 'bursty': 250, 'mixed_shift': 250})
    shift_cylinders = [r.cylinder for r in shift_reqs_objs]
    shift_meta_dicts = [{'workload_type': r.workload_type, 'phase': r.phase} for r in shift_reqs_objs]
    shift_sim = selector.run_simulation(shift_cylinders, initial_head=50, request_metadata=shift_meta_dicts)
    shift_c_seeks = shift_sim['cumulative_seeks']
    phase_seeks = shift_sim['phase_seeks']
    print('  -> Total Seek Distances on 1,000-request Shift:')
    print(f"     FCFS:             {shift_c_seeks['FCFS']:6d} cylinders")
    print(f"     SSTF:             {shift_c_seeks['SSTF']:6d} cylinders")
    print(f"     SCAN:             {shift_c_seeks['SCAN']:6d} cylinders")
    print(f"     C-SCAN:           {shift_c_seeks['C-SCAN']:6d} cylinders")
    print(f"     Learned Selector: {shift_c_seeks['LEARNED']:6d} cylinders  (Oracle: {shift_c_seeks['ORACLE']:6d})")
    print(f"  -> Online Prediction Accuracy: {shift_sim['accuracy'] * 100:.1f}%")
    benchmark_summary['Dynamic Shift'] = {'FCFS': shift_c_seeks['FCFS'], 'SSTF': shift_c_seeks['SSTF'], 'SCAN': shift_c_seeks['SCAN'], 'C-SCAN': shift_c_seeks['C-SCAN'], 'Learned Selector': shift_c_seeks['LEARNED'], 'Oracle': shift_c_seeks['ORACLE'], 'Accuracy': shift_sim['accuracy'], 'ECE': shift_sim['calibration']['ece']}
    for sched_key, s_val in [('FCFS', shift_c_seeks['FCFS']), ('SSTF', shift_c_seeks['SSTF']), ('SCAN', shift_c_seeks['SCAN']), ('C-SCAN', shift_c_seeks['C-SCAN']), ('Learned Selector', shift_c_seeks['LEARNED']), ('Oracle', shift_c_seeks['ORACLE'])]:
        chart_series[sched_key].append(s_val)
    print('\n[4/5] Evaluating model confidence calibration...')
    cal_data = shift_sim['calibration']
    print(f"  -> Expected Calibration Error (ECE): {cal_data['ece']:.4f}")
    print(f"  -> Mean Confidence on Correct Decisions:   {cal_data['avg_conf_correct']:.4f}")
    print(f"  -> Mean Confidence on Incorrect Decisions: {cal_data['avg_conf_incorrect']:.4f}")
    print(f"  -> Confidence Gap (Margin):                +{cal_data['conf_margin']:.4f}")
    print(f"  -> Well-calibrated?: {cal_data['is_well_calibrated']} (confidence is significantly higher when correct!)")
    print('\n[5/5] Generating decision rationales & evaluating explanation confidence (Bonus Track)...')
    explainer = DecisionExplainer(total_cylinders=total_cylinders)
    explanation_results = []
    for d in shift_sim['window_decisions']:
        expl = explainer.explain_decision(window_idx=d.window_idx, selected_scheduler=d.predicted_scheduler, features=d.features, probabilities=d.probabilities, is_correct=d.is_correct, current_head=d.head_start)
        explanation_results.append(expl)
    expl_eval = explainer.evaluate_explanations(explanation_results)
    print(f" -> Generated {expl_eval['total_explanations']} natural-language decision explanations.")
    print(f" -> Mean Explanation Confidence (Correct):   {expl_eval['avg_conf_correct']:.4f}")
    print(f" -> Mean Explanation Confidence (Incorrect): {expl_eval['avg_conf_incorrect']:.4f}")
    print(f" -> Explanation Calibration Margin:          +{expl_eval['confidence_margin']:.4f}")
    print('\n--- SAMPLE DECISION EXPLANATIONS ---')
    for s_idx in [0, 18, 35, 52]:
        if s_idx < len(explanation_results):
            e = explanation_results[s_idx]
            d = shift_sim['window_decisions'][s_idx]
            correct_tag = '✓ CORRECT' if e.is_correct else '✗ INCORRECT'
            print(f'[Window #{e.window_idx:02d} | Phase {d.phase} ({d.workload_type})] {e.selected_scheduler} ({correct_tag}, Conf: {e.explanation_confidence:.2f})')
            print(f'  Rationale: {e.explanation_text}')
            print(f"  Key Factors: {', '.join(e.key_factors)}\n")
    print('Exporting raw results, CSV tables, and publication-ready figures to results/...')
    with open(out_dir / 'benchmark_summary.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Workload', 'FCFS', 'SSTF', 'SCAN', 'C-SCAN', 'Learned_Selector', 'Oracle', 'Accuracy', 'ECE'])
        for w_name, data in benchmark_summary.items():
            writer.writerow([w_name, data['FCFS'], data['SSTF'], data['SCAN'], data['C-SCAN'], data['Learned Selector'], data['Oracle'], f"{data['Accuracy'] * 100:.2f}%", data['ECE']])
    phase_names = ['Phase 1: Sequential', 'Phase 2: Uniform Random', 'Phase 3: Bursty Hotspots', 'Phase 4: Mixed Shifts']
    with open(out_dir / 'phase_shift_breakdown.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Phase', 'Workload_Type', 'FCFS', 'SSTF', 'SCAN', 'C-SCAN', 'Learned_Selector', 'Oracle', 'Degradation_vs_Oracle(%)'])
        for p_idx, p_data in phase_seeks.items():
            oracle_p = p_data['ORACLE']
            learned_p = p_data['LEARNED']
            deg = round((learned_p - oracle_p) / max(1, oracle_p) * 100, 2)
            p_label = phase_names[p_idx] if p_idx < len(phase_names) else f'Phase {p_idx}'
            w_label = phase_meta[p_idx]['workload_type'] if p_idx < len(phase_meta) else 'mixed'
            writer.writerow([p_label, w_label, p_data['FCFS'], p_data['SSTF'], p_data['SCAN'], p_data['C-SCAN'], learned_p, oracle_p, f'{deg}%'])
    with open(out_dir / 'calibration_data.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Confidence_Bin', 'Sample_Count', 'Empirical_Accuracy', 'Mean_Confidence', 'Absolute_Error'])
        for b in cal_data['bins']:
            writer.writerow([b['bin_range'], b['count'], b['accuracy'], b['confidence'], b['abs_error']])
    with open(out_dir / 'sample_explanations.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Window_Idx', 'Phase', 'Workload_Type', 'Selected_Scheduler', 'Correct', 'Confidence', 'Factors', 'Explanation'])
        for e in explanation_results:
            d = shift_sim['window_decisions'][e.window_idx]
            writer.writerow([e.window_idx, d.phase, d.workload_type, e.selected_scheduler, e.is_correct, e.explanation_confidence, '; '.join(e.key_factors), e.explanation_text])
    categories = ['Sequential', 'Random', 'Bursty', 'Dynamic Shift']
    plot_bar_chart(categories=categories, series_data=chart_series, title='Total Seek Distance: Classical Schedulers vs. Learned Selector', xlabel='Workload Regime', ylabel='Total Cylinder Seek Distance', output_path=str(out_dir / 'fig1_seek_comparison.png'))
    plot_trajectory_shift(requests=shift_cylinders, decisions=shift_sim['window_decisions'], output_path=str(out_dir / 'fig2_shift_timeline.png'))
    plot_calibration_diagram(calibration_data=cal_data, output_path=str(out_dir / 'fig3_calibration_curve.png'))
    plot_feature_importances(feat_importances=train_meta['feature_importances'], output_path=str(out_dir / 'fig4_feature_importance.png'))
    print('\nAll benchmark artifacts and figures successfully created in results/!')
    return {'benchmark_summary': benchmark_summary, 'phase_seeks': phase_seeks, 'calibration': cal_data, 'explanation_eval': expl_eval}
