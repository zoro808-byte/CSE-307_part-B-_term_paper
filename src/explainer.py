from dataclasses import dataclass
from typing import Dict, Any, List, Tuple

@dataclass
class ExplanationResult:
    window_idx: int
    selected_scheduler: str
    explanation_text: str
    explanation_confidence: float
    is_correct: bool
    key_factors: List[str]

class DecisionExplainer:

    def __init__(self, total_cylinders: int=200):
        self.total_cylinders = total_cylinders

    def explain_decision(self, window_idx: int, selected_scheduler: str, features: Dict[str, float], probabilities: Dict[str, float], is_correct: bool, current_head: int) -> ExplanationResult:
        factors = []
        reasons = []
        var = features.get('variance', 0.0)
        span = features.get('span', 0.0)
        mean_dist = features.get('mean_dist_head', 0.0)
        dir_bias = features.get('directional_bias', 0.5)
        mono = features.get('monotonicity', 0.0)
        step_sz = features.get('mean_step_size', 0.0)
        model_conf = probabilities.get(selected_scheduler, 0.5)
        sorted_probs = sorted(probabilities.values(), reverse=True)
        prob_margin = sorted_probs[0] - sorted_probs[1] if len(sorted_probs) > 1 else 0.5
        if selected_scheduler == 'SSTF':
            if var < 0.15 or span < 0.25:
                reasons.append(f'Requests are tightly clustered in cylinder space (span={span * 100:.1f}%, normalized var={var:.3f}), minimizing greedy nearest-neighbor seek penalties.')
                factors.append('Tight Spatial Clustering')
            if mean_dist < 0.2:
                reasons.append(f'The current head (at cylinder {current_head}) is situated close to the request cluster centroid.')
                factors.append('Head-to-Cluster Proximity')
            if not reasons:
                reasons.append('Greedy nearest-request dispatch yields the shortest local trajectory across the pending queue.')
                factors.append('Local Proximity Minimization')
        elif selected_scheduler == 'SCAN':
            if span > 0.4:
                reasons.append(f'Requests span broadly across the platter ({span * 100:.1f}% of disk), where elevator sweeping prevents severe back-and-forth oscillations characteristic of FCFS and SSTF.')
                factors.append('Broad Platter Dispersion')
            if dir_bias > 0.65 or dir_bias < 0.35:
                majority_side = 'above' if dir_bias > 0.5 else 'below'
                reasons.append(f'Substantial directional bias ({dir_bias * 100:.0f}% of requests {majority_side} head) favors continuous sweep.')
                factors.append('Directional Sweep Alignment')
            if not reasons:
                reasons.append('Elevator sweep balances boundary traversal while avoiding starvation and seek thrashing.')
                factors.append('Elevator Optimization')
        elif selected_scheduler == 'C-SCAN':
            if span > 0.6:
                reasons.append(f'Requests are widely dispersed with extreme cylinder differences (span={span * 100:.1f}%). Circular sweeping provides uniform bounding of worst-case response times.')
                factors.append('Platter-Wide Uniformity')
            if dir_bias < 0.3 or dir_bias > 0.7:
                reasons.append('Heavy concentration near boundaries makes single-direction circular return highly efficient.')
                factors.append('Boundary Asymmetry')
            if not reasons:
                reasons.append('Unidirectional circular sweeps eliminate reverse-direction latency penalties for newly arriving requests.')
                factors.append('Circular Regularity')
        elif mono > 0.7 or step_sz < 0.1:
            reasons.append(f'Arrival sequence exhibits strong natural monotonicity (mono={mono * 100:.0f}%, step size={step_sz:.3f}), so FIFO dispatch naturally aligns with platter geometry with minimal reordering gains.')
            factors.append('Natural Sequential Stream')
        else:
            reasons.append('Arrival order is already quasi-monotonic; preserving order prevents reordering latency.')
            factors.append('Preserved Arrival Order')
        explanation_text = ' '.join(reasons)
        factor_alignment = min(1.0, len(factors) / 2.0)
        heuristic_score = 0.5 * model_conf + 0.3 * factor_alignment + 0.2 * prob_margin
        heuristic_confidence = min(0.99, max(0.4, round(heuristic_score, 3)))
        return ExplanationResult(window_idx=window_idx, selected_scheduler=selected_scheduler, explanation_text=explanation_text, explanation_confidence=heuristic_confidence, is_correct=is_correct, key_factors=factors)

    def evaluate_explanations(self, explanations: List[ExplanationResult]) -> Dict[str, Any]:
        if not explanations:
            return {}
        correct_confs = [e.explanation_confidence for e in explanations if e.is_correct]
        incorrect_confs = [e.explanation_confidence for e in explanations if not e.is_correct]
        avg_conf_correct = sum(correct_confs) / len(correct_confs) if correct_confs else 0.0
        avg_conf_incorrect = sum(incorrect_confs) / len(incorrect_confs) if incorrect_confs else 0.0
        return {'total_explanations': len(explanations), 'correct_count': len(correct_confs), 'incorrect_count': len(incorrect_confs), 'avg_conf_correct': round(avg_conf_correct, 4), 'avg_conf_incorrect': round(avg_conf_incorrect, 4), 'confidence_margin': round(avg_conf_correct - avg_conf_incorrect, 4), 'is_calibrated': avg_conf_correct > avg_conf_incorrect}
