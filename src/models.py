import math
import random
from typing import List, Tuple, Dict, Any, Optional

class TreeNode:

    def __init__(self, feature_idx: Optional[int]=None, threshold: Optional[float]=None, left: Optional['TreeNode']=None, right: Optional['TreeNode']=None, value: Optional[Dict[str, float]]=None, predicted_class: Optional[str]=None):
        self.feature_idx = feature_idx
        self.threshold = threshold
        self.left = left
        self.right = right
        self.value = value
        self.predicted_class = predicted_class

    @property
    def is_leaf(self) -> bool:
        return self.value is not None

class DecisionTreeClassifier:

    def __init__(self, max_depth: int=6, min_samples_split: int=5, max_features: Optional[int]=None):
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.max_features = max_features
        self.root: Optional[TreeNode] = None
        self.classes: List[str] = []
        self.feature_importances: List[float] = []

    def _gini(self, y: List[str]) -> float:
        n = len(y)
        if n == 0:
            return 0.0
        counts: Dict[str, int] = {}
        for label in y:
            counts[label] = counts.get(label, 0) + 1
        gini = 1.0 - sum(((c / n) ** 2 for c in counts.values()))
        return gini

    def _best_split(self, X: List[List[float]], y: List[str]) -> Tuple[Optional[int], Optional[float], float]:
        n_samples = len(y)
        if n_samples < self.min_samples_split:
            return (None, None, 0.0)
        n_features = len(X[0])
        current_gini = self._gini(y)
        best_gain = 0.0
        best_feat = None
        best_thresh = None
        feature_indices = list(range(n_features))
        if self.max_features and self.max_features < n_features:
            feature_indices = random.sample(feature_indices, self.max_features)
        for feat in feature_indices:
            values = sorted(set((X[i][feat] for i in range(n_samples))))
            if len(values) <= 1:
                continue
            thresholds = [(values[i] + values[i + 1]) / 2.0 for i in range(len(values) - 1)]
            if len(thresholds) > 20:
                step = len(thresholds) // 20
                thresholds = thresholds[::step]
            for thresh in thresholds:
                left_y = [y[i] for i in range(n_samples) if X[i][feat] <= thresh]
                right_y = [y[i] for i in range(n_samples) if X[i][feat] > thresh]
                if not left_y or not right_y:
                    continue
                w_left = len(left_y) / n_samples
                w_right = len(right_y) / n_samples
                gain = current_gini - (w_left * self._gini(left_y) + w_right * self._gini(right_y))
                if gain > best_gain:
                    best_gain = gain
                    best_feat = feat
                    best_thresh = thresh
        return (best_feat, best_thresh, best_gain)

    def _build_tree(self, X: List[List[float]], y: List[str], depth: int=0) -> TreeNode:
        n_samples = len(y)
        unique_classes = set(y)
        counts: Dict[str, int] = {}
        for label in y:
            counts[label] = counts.get(label, 0) + 1
        majority_class = max(counts.keys(), key=lambda c: counts[c])
        prob_dist = {}
        total_smoothed = n_samples + len(self.classes)
        for c in self.classes:
            prob_dist[c] = (counts.get(c, 0) + 1.0) / total_smoothed
        if depth >= self.max_depth or len(unique_classes) == 1 or n_samples < self.min_samples_split:
            return TreeNode(value=prob_dist, predicted_class=majority_class)
        best_feat, best_thresh, best_gain = self._best_split(X, y)
        if best_gain <= 1e-07 or best_feat is None:
            return TreeNode(value=prob_dist, predicted_class=majority_class)
        if best_feat is not None and best_feat < len(self.feature_importances):
            self.feature_importances[best_feat] += best_gain * n_samples
        left_idx = [i for i in range(n_samples) if X[i][best_feat] <= best_thresh]
        right_idx = [i for i in range(n_samples) if X[i][best_feat] > best_thresh]
        left_child = self._build_tree([X[i] for i in left_idx], [y[i] for i in left_idx], depth + 1)
        right_child = self._build_tree([X[i] for i in right_idx], [y[i] for i in right_idx], depth + 1)
        return TreeNode(feature_idx=best_feat, threshold=best_thresh, left=left_child, right=right_child, predicted_class=majority_class)

    def fit(self, X: List[List[float]], y: List[str]):
        self.classes = sorted(list(set(y)))
        n_features = len(X[0]) if X else 0
        self.feature_importances = [0.0] * n_features
        self.root = self._build_tree(X, y, depth=0)
        total_imp = sum(self.feature_importances)
        if total_imp > 0:
            self.feature_importances = [imp / total_imp for imp in self.feature_importances]

    def _predict_sample(self, node: TreeNode, x: List[float]) -> Dict[str, float]:
        if node.is_leaf:
            return node.value
        if x[node.feature_idx] <= node.threshold:
            return self._predict_sample(node.left, x)
        return self._predict_sample(node.right, x)

    def predict_proba_single(self, x: List[float]) -> Dict[str, float]:
        if self.root is None:
            raise ValueError('Model is not fitted yet.')
        return self._predict_sample(self.root, x)

    def predict_proba(self, X: List[List[float]]) -> List[Dict[str, float]]:
        return [self.predict_proba_single(x) for x in X]

    def predict(self, X: List[List[float]]) -> List[str]:
        probas = self.predict_proba(X)
        return [max(p.keys(), key=lambda k: p[k]) for p in probas]

class RandomForestClassifier:

    def __init__(self, n_estimators: int=15, max_depth: int=6, min_samples_split: int=5, seed: int=42):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.seed = seed
        self.trees: List[DecisionTreeClassifier] = []
        self.classes: List[str] = []
        self.feature_importances: List[float] = []

    def fit(self, X: List[List[float]], y: List[str]):
        random.seed(self.seed)
        self.classes = sorted(list(set(y)))
        n_samples = len(X)
        n_features = len(X[0])
        max_feat = max(1, int(math.sqrt(n_features)))
        self.trees = []
        self.feature_importances = [0.0] * n_features
        for i in range(self.n_estimators):
            indices = [random.randint(0, n_samples - 1) for _ in range(n_samples)]
            sample_X = [X[idx] for idx in indices]
            sample_y = [y[idx] for idx in indices]
            tree = DecisionTreeClassifier(max_depth=self.max_depth, min_samples_split=self.min_samples_split, max_features=max_feat)
            tree.fit(sample_X, sample_y)
            self.trees.append(tree)
            for f_idx, imp in enumerate(tree.feature_importances):
                self.feature_importances[f_idx] += imp
        total_imp = sum(self.feature_importances)
        if total_imp > 0:
            self.feature_importances = [imp / total_imp for imp in self.feature_importances]

    def predict_proba_single(self, x: List[float]) -> Dict[str, float]:
        aggregated = {c: 0.0 for c in self.classes}
        for tree in self.trees:
            probs = tree.predict_proba_single(x)
            for c, p in probs.items():
                aggregated[c] += p
        n = len(self.trees)
        return {c: round(prob / n, 4) for c, prob in aggregated.items()}

    def predict_proba(self, X: List[List[float]]) -> List[Dict[str, float]]:
        return [self.predict_proba_single(x) for x in X]

    def predict(self, X: List[List[float]]) -> List[str]:
        probas = self.predict_proba(X)
        return [max(p.keys(), key=lambda k: p[k]) for p in probas]

def compute_calibration_curve(y_true: List[str], y_pred: List[str], confidences: List[float], n_bins: int=5, correct_mask: Optional[List[bool]]=None) -> Dict[str, Any]:
    bins = [i / n_bins for i in range(n_bins + 1)]
    bin_data = []
    total_samples = len(confidences)
    ece = 0.0
    if correct_mask is None:
        correct_mask = [t == p for t, p in zip(y_true, y_pred)]
    for i in range(n_bins):
        low = bins[i]
        high = bins[i + 1]
        indices = [idx for idx, c in enumerate(confidences) if low <= c < high or (i == n_bins - 1 and low <= c <= high)]
        bin_count = len(indices)
        if bin_count > 0:
            correct_count = sum((1 for idx in indices if correct_mask[idx]))
            accuracy = correct_count / bin_count
            avg_confidence = sum((confidences[idx] for idx in indices)) / bin_count
            error = abs(accuracy - avg_confidence)
            ece += bin_count / total_samples * error
        else:
            accuracy = 0.0
            avg_confidence = (low + high) / 2.0
            error = 0.0
        bin_data.append({'bin_idx': i, 'bin_range': f'{low:.1f}-{high:.1f}', 'count': bin_count, 'accuracy': round(accuracy, 4), 'confidence': round(avg_confidence, 4), 'abs_error': round(abs(accuracy - avg_confidence), 4) if bin_count > 0 else 0.0})
    correct_confidences = [c for idx, c in enumerate(confidences) if correct_mask[idx]]
    incorrect_confidences = [c for idx, c in enumerate(confidences) if not correct_mask[idx]]
    avg_conf_correct = sum(correct_confidences) / len(correct_confidences) if correct_confidences else 0.0
    avg_conf_incorrect = sum(incorrect_confidences) / len(incorrect_confidences) if incorrect_confidences else 0.0
    return {'bins': bin_data, 'ece': round(ece, 4), 'avg_conf_correct': round(avg_conf_correct, 4), 'avg_conf_incorrect': round(avg_conf_incorrect, 4), 'conf_margin': round(avg_conf_correct - avg_conf_incorrect, 4), 'is_well_calibrated': avg_conf_correct > avg_conf_incorrect}
