import urllib.request
import json
import time

# 1. Test Standard Mode
print("Testing Standard Mode...")
t0 = time.perf_counter()
req_std = urllib.request.Request(
    'http://127.0.0.1:8000/api/analyse?use_demo=true',
    data=b'',
    headers={'Content-Type': 'application/json'}
)
res_std = urllib.request.urlopen(req_std)
std_data = json.loads(res_std.read().decode('utf-8'))
t_std = time.perf_counter() - t0
print(f"Standard Mode Completed in {t_std:.2f}s:")
print(f"  run_id: {std_data['id']}")
print(f"  candidate_count: {std_data['candidate_count']}")
print(f"  mode: {std_data.get('mode')}")
print(f"  mode_label: {std_data.get('mode_label')}")
assert std_data['candidate_count'] == 133, f"Expected 133 candidates, got {std_data['candidate_count']}"
assert std_data['mode'] == 'standard'

# 2. Test High Accuracy Mode
print("\nTesting High Accuracy Mode...")
t1 = time.perf_counter()
req_high = urllib.request.Request(
    'http://127.0.0.1:8000/api/analyse?use_demo=true&mode=high_accuracy',
    data=b'',
    headers={'Content-Type': 'application/json'}
)
res_high = urllib.request.urlopen(req_high)
high_data = json.loads(res_high.read().decode('utf-8'))
t_high = time.perf_counter() - t1
print(f"High Accuracy Mode Completed in {t_high:.2f}s:")
print(f"  run_id: {high_data['id']}")
print(f"  candidate_count: {high_data['candidate_count']}")
print(f"  mode: {high_data.get('mode')}")
print(f"  mode_label: {high_data.get('mode_label')}")
assert high_data['mode'] == 'high_accuracy'

# 3. Test History
print("\nTesting History...")
req_hist = urllib.request.urlopen('http://127.0.0.1:8000/api/history')
hist_data = json.loads(req_hist.read().decode('utf-8'))
print(f"History records count: {len(hist_data)}")
for item in hist_data[:2]:
    print(f"  Run {item['id']}: {item['display_name']} | Mode: {item.get('mode_label')} ({item.get('mode')})")

# 4. Test Export
print("\nTesting Export...")
req_exp = urllib.request.urlopen(f"http://127.0.0.1:8000/api/export/{high_data['id']}")
exp_data = json.loads(req_exp.read().decode('utf-8'))
print(f"Export analysis mode: {exp_data['analysis']['details'].get('mode_label')}")

print("\nALL BACKEND API VERIFICATIONS PASSED.")

