import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.schedulers import fcfs, sstf, scan, c_scan, evaluate_all

def test_textbook_example():
    requests = [98, 183, 37, 122, 14, 124, 65, 67]
    head = 53
    cylinders = 200
    res_fcfs = fcfs(requests, head, cylinders)
    print(f'FCFS Total Seek: {res_fcfs.total_seek_distance} (Expected: 640)')
    assert res_fcfs.total_seek_distance == 640, f'FCFS mismatch: {res_fcfs.total_seek_distance}'
    res_sstf = sstf(requests, head, cylinders)
    print(f'SSTF Total Seek: {res_sstf.total_seek_distance} (Expected: 236)')
    assert res_sstf.total_seek_distance == 236, f'SSTF mismatch: {res_sstf.total_seek_distance}'
    res_scan = scan(requests, head, cylinders, direction='up')
    print(f'SCAN Total Seek: {res_scan.total_seek_distance} (Expected: 331)')
    assert res_scan.total_seek_distance == 331, f'SCAN mismatch: {res_scan.total_seek_distance}'
    res_cscan = c_scan(requests, head, cylinders, direction='up')
    print(f'C-SCAN Total Seek: {res_cscan.total_seek_distance} (Expected: 382)')
    assert res_cscan.total_seek_distance == 382, f'C-SCAN mismatch: {res_cscan.total_seek_distance}'
    print('ALL TEXTBOOK REFERENCE TESTS PASSED PERFECTLY!')
if __name__ == '__main__':
    test_textbook_example()
