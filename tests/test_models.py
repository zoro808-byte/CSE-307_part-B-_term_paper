import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.features import extract_window_features, features_to_vector
from src.models import DecisionTreeClassifier, RandomForestClassifier, compute_calibration_curve

def test_features_and_models():
    reqs = [50, 52, 55, 58, 60]
    feats = extract_window_features(reqs, current_head=48, total_cylinders=200)
    assert 'variance' in feats
    assert 'span' in feats
    vec = features_to_vector(feats)
    assert len(vec) == 11
    print('Features extracted successfully:', feats)
    X = [[0.1, 0.01, 0.1, 0.05, 0.02, 1.0, 1.0, 0.01, 1.0, 1.0, 1.0], [0.12, 0.01, 0.1, 0.06, 0.03, 1.0, 0.9, 0.01, 1.0, 1.0, 1.0], [0.5, 0.8, 0.9, 0.85, 0.4, 0.5, 0.2, 0.4, 1.0, 1.0, 0.5], [0.52, 0.78, 0.88, 0.82, 0.42, 0.48, 0.1, 0.38, 1.0, 1.0, 0.48]]
    y = ['SSTF', 'SSTF', 'SCAN', 'SCAN']
    rf = RandomForestClassifier(n_estimators=10, max_depth=4)
    rf.fit(X, y)
    preds = rf.predict(X)
    probas = rf.predict_proba(X)
    print('Predictions:', preds)
    for p in probas:
        prob_sum = sum(p.values())
        assert abs(prob_sum - 1.0) < 0.001, f'Probabilities do not sum to 1: {p}'
    y_true = ['SSTF', 'SSTF', 'SCAN', 'C-SCAN']
    y_pred = ['SSTF', 'SSTF', 'SCAN', 'SCAN']
    confs = [0.95, 0.9, 0.85, 0.6]
    cal = compute_calibration_curve(y_true, y_pred, confs, n_bins=3)
    print('Calibration metrics:', cal)
    assert cal['is_well_calibrated'] is True
    print('ALL MODEL & CALIBRATION TESTS PASSED!')
if __name__ == '__main__':
    test_features_and_models()
