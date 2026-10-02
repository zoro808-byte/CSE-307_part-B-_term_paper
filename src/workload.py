import random
import math
from dataclasses import dataclass
from typing import List, Tuple, Dict, Any, Optional

@dataclass
class DiskRequest:
    id: int
    cylinder: int
    arrival_time: float
    workload_type: str
    phase: int

class WorkloadGenerator:

    def __init__(self, total_cylinders: int=200, seed: Optional[int]=42):
        self.total_cylinders = total_cylinders
        self.seed = seed
        if seed is not None:
            random.seed(seed)

    def generate_sequential(self, count: int, start_cylinder: Optional[int]=None, stride_range: Tuple[int, int]=(1, 4), direction: int=1, noise_prob: float=0.05) -> List[int]:
        if start_cylinder is None:
            curr = random.randint(10, self.total_cylinders - 20)
        else:
            curr = start_cylinder
        requests = []
        d = direction
        for _ in range(count):
            if random.random() < noise_prob:
                offset = random.randint(-5, 5)
                req = max(0, min(self.total_cylinders - 1, curr + offset))
            else:
                stride = random.randint(stride_range[0], stride_range[1]) * d
                req = curr + stride
                if req >= self.total_cylinders - 1:
                    req = self.total_cylinders - 1
                    d = -1
                elif req <= 0:
                    req = 0
                    d = 1
                curr = req
            requests.append(curr)
        return requests

    def generate_random(self, count: int) -> List[int]:
        return [random.randint(0, self.total_cylinders - 1) for _ in range(count)]

    def generate_bursty_clustered(self, count: int, num_clusters: int=3, cluster_std: float=6.0, switch_prob: float=0.2) -> List[int]:
        centers = [int((i + 0.5) * (self.total_cylinders / num_clusters)) for i in range(num_clusters)]
        current_cluster = random.choice(centers)
        requests = []
        for _ in range(count):
            if random.random() < switch_prob:
                current_cluster = random.choice(centers)
            val = int(round(random.gauss(current_cluster, cluster_std)))
            val = max(0, min(self.total_cylinders - 1, val))
            requests.append(val)
        return requests

    def generate_shifting_timeline(self, phase_lengths: Dict[str, int]=None) -> Tuple[List[DiskRequest], List[Dict[str, Any]]]:
        if phase_lengths is None:
            phase_lengths = {'sequential': 250, 'random': 250, 'bursty': 250, 'mixed_shift': 250}
        requests: List[DiskRequest] = []
        phase_metadata = []
        req_id = 0
        current_time = 0.0
        phase_idx = 0
        for w_type, length in phase_lengths.items():
            start_idx = req_id
            if w_type == 'sequential':
                cyls = self.generate_sequential(length)
            elif w_type == 'random':
                cyls = self.generate_random(length)
            elif w_type == 'bursty':
                cyls = self.generate_bursty_clustered(length)
            elif w_type == 'mixed_shift':
                cyls = []
                while len(cyls) < length:
                    rem = length - len(cyls)
                    chunk_len = min(rem, random.randint(15, 35))
                    choice = random.choice(['sequential', 'bursty', 'random'])
                    if choice == 'sequential':
                        cyls.extend(self.generate_sequential(chunk_len))
                    elif choice == 'bursty':
                        cyls.extend(self.generate_bursty_clustered(chunk_len))
                    else:
                        cyls.extend(self.generate_random(chunk_len))
            else:
                cyls = self.generate_random(length)
            for c in cyls:
                current_time += random.expovariate(1.0)
                requests.append(DiskRequest(id=req_id, cylinder=c, arrival_time=round(current_time, 3), workload_type=w_type, phase=phase_idx))
                req_id += 1
            phase_metadata.append({'phase': phase_idx, 'workload_type': w_type, 'start_req_id': start_idx, 'end_req_id': req_id - 1, 'count': length})
            phase_idx += 1
        return (requests, phase_metadata)

def create_sliding_windows(requests: List[int], window_size: int=15, stride: int=5) -> List[List[int]]:
    windows = []
    for i in range(0, len(requests) - window_size + 1, stride):
        windows.append(requests[i:i + window_size])
    return windows
