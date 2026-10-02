import math
from typing import List, Dict, Any

def extract_window_features(requests: List[int], current_head: int, total_cylinders: int=200, current_direction: str='up') -> Dict[str, float]:
    k = len(requests)
    if k == 0:
        return {'mean_cylinder': float(current_head) / total_cylinders, 'variance': 0.0, 'std_dev': 0.0, 'span': 0.0, 'mean_dist_head': 0.0, 'directional_bias': 0.5, 'monotonicity': 0.0, 'mean_step_size': 0.0, 'uniqueness_ratio': 0.0, 'head_in_span': 0.0, 'current_dir_alignment': 0.5}
    mean_cyl = sum(requests) / k
    variance = sum(((r - mean_cyl) ** 2 for r in requests)) / k
    std_dev = math.sqrt(variance)
    min_cyl = min(requests)
    max_cyl = max(requests)
    span = (max_cyl - min_cyl) / max(1, total_cylinders - 1)
    mean_dist_head = sum((abs(r - current_head) for r in requests)) / (k * max(1, total_cylinders - 1))
    above_count = sum((1 for r in requests if r >= current_head))
    directional_bias = above_count / k
    if k >= 3:
        consecutive_same_dir = 0
        for i in range(1, k - 1):
            diff1 = requests[i] - requests[i - 1]
            diff2 = requests[i + 1] - requests[i]
            if diff1 >= 0 and diff2 >= 0 or (diff1 <= 0 and diff2 <= 0):
                consecutive_same_dir += 1
        monotonicity = consecutive_same_dir / (k - 2)
    else:
        monotonicity = 1.0
    if k >= 2:
        step_sum = sum((abs(requests[i] - requests[i - 1]) for i in range(1, k)))
        mean_step_size = step_sum / ((k - 1) * max(1, total_cylinders - 1))
    else:
        mean_step_size = 0.0
    unique_count = len(set(requests))
    uniqueness_ratio = unique_count / k
    if min_cyl <= current_head <= max_cyl:
        head_in_span = 1.0
    else:
        head_in_span = 0.0
    if current_direction == 'up':
        dir_alignment = directional_bias
    else:
        dir_alignment = 1.0 - directional_bias
    return {'mean_cylinder': round(mean_cyl / total_cylinders, 4), 'variance': round(variance / (total_cylinders / 2) ** 2, 4), 'std_dev': round(std_dev / (total_cylinders / 2), 4), 'span': round(span, 4), 'mean_dist_head': round(mean_dist_head, 4), 'directional_bias': round(directional_bias, 4), 'monotonicity': round(monotonicity, 4), 'mean_step_size': round(mean_step_size, 4), 'uniqueness_ratio': round(uniqueness_ratio, 4), 'head_in_span': head_in_span, 'current_dir_alignment': round(dir_alignment, 4)}
FEATURE_NAMES = ['mean_cylinder', 'variance', 'std_dev', 'span', 'mean_dist_head', 'directional_bias', 'monotonicity', 'mean_step_size', 'uniqueness_ratio', 'head_in_span', 'current_dir_alignment']

def features_to_vector(feat_dict: Dict[str, float]) -> List[float]:
    return [feat_dict[name] for name in FEATURE_NAMES]
