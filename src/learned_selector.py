import random
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple, Optional
from src.schedulers import SCHEDULERS, evaluate_all, SchedulingResult
from src.workload import WorkloadGenerator
from src.features import extract_window_features, features_to_vector, FEATURE_NAMES
from src.models import RandomForestClassifier, DecisionTreeClassifier, compute_calibration_curve

@dataclass
class WindowDecision:
    window_idx: int
    head_start: int
    head_end: int
    requests: List[int]
    features: Dict[str, float]
    predicted_scheduler: str
    confidence: float
    probabilities: Dict[str, float]
    actual_best_scheduler: str
    is_correct: bool
    seek_by_scheduler: Dict[str, int]
    selected_seek: int
    oracle_seek: int
    workload_type: str
    phase: int

class LearnedSchedulerSelector:

    def __init__(self, total_cylinders: int=200, model_type: str='random_forest', window_size: int=15, seed: int=42):
        self.total_cylinders = total_cylinders
        self.window_size = window_size
        self.seed = seed
        self.model_type = model_type
        if model_type == 'decision_tree':
            self.model = DecisionTreeClassifier(max_depth=6, min_samples_split=4)
        else:
            self.model = RandomForestClassifier(n_estimators=20, max_depth=6, seed=seed)
        self.is_trained = False
        self.training_metadata: Dict[str, Any] = {}

    def generate_training_data(self, samples_per_type: int=300) -> Tuple[List[List[float]], List[str], List[Dict[str, Any]]]:
        gen = WorkloadGenerator(total_cylinders=self.total_cylinders, seed=self.seed)
        X = []
        y = []
        records = []
        types = ['sequential', 'random', 'bursty']
        for w_type in types:
            for _ in range(samples_per_type):
                head = random.randint(0, self.total_cylinders - 1)
                direction = random.choice(['up', 'down'])
                if w_type == 'sequential':
                    reqs = gen.generate_sequential(self.window_size, start_cylinder=head)
                elif w_type == 'random':
                    reqs = gen.generate_random(self.window_size)
                else:
                    reqs = gen.generate_bursty_clustered(self.window_size)
                results = evaluate_all(reqs, head, self.total_cylinders, direction)
                seeks = {name: res.total_seek_distance for name, res in results.items()}
                min_seek = min(seeks.values())
                candidates = [name for name, seek in seeks.items() if seek == min_seek]
                best_sched = candidates[0]
                if len(candidates) > 1:
                    for pref in ['SSTF', 'SCAN', 'C-SCAN', 'FCFS']:
                        if pref in candidates:
                            best_sched = pref
                            break
                feat_dict = extract_window_features(reqs, head, self.total_cylinders, direction)
                vec = features_to_vector(feat_dict)
                X.append(vec)
                y.append(best_sched)
                records.append({'workload_type': w_type, 'head': head, 'direction': direction, 'requests': reqs, 'features': feat_dict, 'seeks': seeks, 'best_scheduler': best_sched})
        return (X, y, records)

    def train(self, samples_per_type: int=350) -> Dict[str, Any]:
        X, y, records = self.generate_training_data(samples_per_type=samples_per_type)
        self.model.fit(X, y)
        self.is_trained = True
        preds = self.model.predict(X)
        correct = sum((1 for p, act in zip(preds, y) if p == act))
        train_acc = correct / len(y)
        class_counts = {}
        for label in y:
            class_counts[label] = class_counts.get(label, 0) + 1
        feat_importances = dict(zip(FEATURE_NAMES, [round(f, 4) for f in self.model.feature_importances]))
        self.training_metadata = {'total_samples': len(y), 'train_accuracy': round(train_acc, 4), 'class_distribution': class_counts, 'feature_importances': feat_importances}
        return self.training_metadata

    def select(self, requests: List[int], current_head: int, direction: str='up') -> Tuple[str, float, Dict[str, float], Dict[str, float]]:
        if not self.is_trained:
            raise RuntimeError('Selector model must be trained before calling select()')
        feat_dict = extract_window_features(requests, current_head, self.total_cylinders, direction)
        vec = features_to_vector(feat_dict)
        probs = self.model.predict_proba_single(vec)
        best_sched = max(probs.keys(), key=lambda k: probs[k])
        confidence = probs[best_sched]
        return (best_sched, confidence, probs, feat_dict)

    def run_simulation(self, requests: List[int], initial_head: int=50, request_metadata: Optional[List[Dict[str, Any]]]=None) -> Dict[str, Any]:
        if not self.is_trained:
            self.train()
        num_windows = len(requests) // self.window_size
        head_positions = {'FCFS': initial_head, 'SSTF': initial_head, 'SCAN': initial_head, 'C-SCAN': initial_head, 'LEARNED': initial_head, 'ORACLE': initial_head}
        cumulative_seeks = {name: 0 for name in head_positions}
        window_decisions: List[WindowDecision] = []
        phase_seeks: Dict[int, Dict[str, int]] = {}
        for w_idx in range(num_windows):
            start_i = w_idx * self.window_size
            end_i = start_i + self.window_size
            win_reqs = requests[start_i:end_i]
            w_type = 'unknown'
            phase_num = 0
            if request_metadata and start_i < len(request_metadata):
                w_type = request_metadata[start_i].get('workload_type', 'unknown')
                phase_num = request_metadata[start_i].get('phase', 0)
            if phase_num not in phase_seeks:
                phase_seeks[phase_num] = {name: 0 for name in head_positions}
            window_seeks_from_learned_head = {}
            for name, fn in SCHEDULERS.items():
                res_indep = fn(win_reqs, head_positions[name], self.total_cylinders)
                cumulative_seeks[name] += res_indep.total_seek_distance
                head_positions[name] = res_indep.seek_sequence[-1]
                phase_seeks[phase_num][name] += res_indep.total_seek_distance
                res_from_learned = fn(win_reqs, head_positions['LEARNED'], self.total_cylinders)
                window_seeks_from_learned_head[name] = res_from_learned.total_seek_distance
            oracle_sched = min(window_seeks_from_learned_head.keys(), key=lambda k: window_seeks_from_learned_head[k])
            oracle_seek = window_seeks_from_learned_head[oracle_sched]
            cumulative_seeks['ORACLE'] += oracle_seek
            phase_seeks[phase_num]['ORACLE'] += oracle_seek
            current_head = head_positions['LEARNED']
            pred_sched, conf, probs, feats = self.select(win_reqs, current_head)
            sel_result = SCHEDULERS[pred_sched](win_reqs, current_head, self.total_cylinders)
            sel_seek = sel_result.total_seek_distance
            cumulative_seeks['LEARNED'] += sel_seek
            phase_seeks[phase_num]['LEARNED'] += sel_seek
            is_correct = sel_seek == oracle_seek or pred_sched == oracle_sched
            new_head = sel_result.seek_sequence[-1]
            head_positions['LEARNED'] = new_head
            window_decisions.append(WindowDecision(window_idx=w_idx, head_start=current_head, head_end=new_head, requests=win_reqs, features=feats, predicted_scheduler=pred_sched, confidence=conf, probabilities=probs, actual_best_scheduler=oracle_sched, is_correct=is_correct, seek_by_scheduler=window_seeks_from_learned_head, selected_seek=sel_seek, oracle_seek=oracle_seek, workload_type=w_type, phase=phase_num))
        y_true = [d.actual_best_scheduler for d in window_decisions]
        y_pred = [d.predicted_scheduler for d in window_decisions]
        confs = [d.confidence for d in window_decisions]
        correct_mask = [d.is_correct for d in window_decisions]
        calibration_stats = compute_calibration_curve(y_true, y_pred, confs, correct_mask=correct_mask)
        accuracy = sum((1 for d in window_decisions if d.is_correct)) / max(1, len(window_decisions))
        return {'cumulative_seeks': cumulative_seeks, 'phase_seeks': phase_seeks, 'window_decisions': window_decisions, 'accuracy': round(accuracy, 4), 'calibration': calibration_stats, 'total_windows': num_windows}
