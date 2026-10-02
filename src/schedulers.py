from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Any

@dataclass
class SchedulingResult:
    algorithm: str
    total_seek_distance: int
    seek_sequence: List[int]
    step_seeks: List[int]
    average_seek_distance: float
    wait_times: List[int]
    variance_wait_time: float

    def to_dict(self) -> Dict[str, Any]:
        return {'algorithm': self.algorithm, 'total_seek_distance': self.total_seek_distance, 'average_seek_distance': round(self.average_seek_distance, 2), 'variance_wait_time': round(self.variance_wait_time, 2), 'sequence_length': len(self.seek_sequence)}

def _calculate_metrics(algorithm: str, sequence: List[int], original_requests: List[int]) -> SchedulingResult:
    if len(sequence) <= 1:
        return SchedulingResult(algorithm=algorithm, total_seek_distance=0, seek_sequence=sequence, step_seeks=[], average_seek_distance=0.0, wait_times=[0] * len(original_requests), variance_wait_time=0.0)
    step_seeks = [abs(sequence[i] - sequence[i - 1]) for i in range(1, len(sequence))]
    total_seek = sum(step_seeks)
    avg_seek = total_seek / max(1, len(original_requests))
    serviced_order = sequence[1:]
    wait_times = []
    temp_serviced = list(serviced_order)
    for req in original_requests:
        if req in temp_serviced:
            idx = temp_serviced.index(req)
            wait_times.append(idx)
        else:
            wait_times.append(len(serviced_order))
    mean_wait = sum(wait_times) / max(1, len(wait_times))
    variance_wait = sum(((w - mean_wait) ** 2 for w in wait_times)) / max(1, len(wait_times))
    return SchedulingResult(algorithm=algorithm, total_seek_distance=total_seek, seek_sequence=sequence, step_seeks=step_seeks, average_seek_distance=avg_seek, wait_times=wait_times, variance_wait_time=variance_wait)

def fcfs(requests: List[int], initial_head: int, total_cylinders: int=200, direction: str='up') -> SchedulingResult:
    sequence = [initial_head] + list(requests)
    return _calculate_metrics('FCFS', sequence, requests)

def sstf(requests: List[int], initial_head: int, total_cylinders: int=200, direction: str='up') -> SchedulingResult:
    if not requests:
        return _calculate_metrics('SSTF', [initial_head], requests)
    remaining = list(requests)
    sequence = [initial_head]
    current = initial_head
    while remaining:

        def distance_key(r):
            dist = abs(r - current)
            pref = 0 if direction == 'up' and r >= current or (direction == 'down' and r <= current) else 1
            return (dist, pref)
        closest = min(remaining, key=distance_key)
        sequence.append(closest)
        remaining.remove(closest)
        current = closest
    return _calculate_metrics('SSTF', sequence, requests)

def scan(requests: List[int], initial_head: int, total_cylinders: int=200, direction: str='up') -> SchedulingResult:
    if not requests:
        return _calculate_metrics('SCAN', [initial_head], requests)
    sequence = [initial_head]
    lower = sorted([r for r in requests if r < initial_head])
    upper = sorted([r for r in requests if r >= initial_head])
    if direction == 'up':
        sequence.extend(upper)
        if lower:
            sequence.append(total_cylinders - 1)
            sequence.extend(reversed(lower))
    else:
        sequence.extend(reversed(lower))
        if upper:
            sequence.append(0)
            sequence.extend(upper)
    return _calculate_metrics('SCAN', sequence, requests)

def c_scan(requests: List[int], initial_head: int, total_cylinders: int=200, direction: str='up') -> SchedulingResult:
    if not requests:
        return _calculate_metrics('C-SCAN', [initial_head], requests)
    sequence = [initial_head]
    lower = sorted([r for r in requests if r < initial_head])
    upper = sorted([r for r in requests if r >= initial_head])
    if direction == 'up':
        sequence.extend(upper)
        if lower:
            sequence.append(total_cylinders - 1)
            sequence.append(0)
            sequence.extend(lower)
    else:
        sequence.extend(reversed(lower))
        if upper:
            sequence.append(0)
            sequence.append(total_cylinders - 1)
            sequence.extend(reversed(upper))
    return _calculate_metrics('C-SCAN', sequence, requests)
SCHEDULERS = {'FCFS': fcfs, 'SSTF': sstf, 'SCAN': scan, 'C-SCAN': c_scan}

def evaluate_all(requests: List[int], initial_head: int, total_cylinders: int=200, direction: str='up') -> Dict[str, SchedulingResult]:
    return {name: fn(requests, initial_head, total_cylinders, direction) for name, fn in SCHEDULERS.items()}
