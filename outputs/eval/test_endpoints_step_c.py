import urllib.request
import json

# 1. Check API status
req = urllib.request.urlopen('http://127.0.0.1:8000/api/status')
print('API status:', json.loads(req.read().decode('utf-8')))

# 2. Run analysis on demo stone
req_analyse = urllib.request.Request(
    'http://127.0.0.1:8000/api/analyse?use_demo=true',
    data=b'',
    headers={'Content-Type': 'application/json'}
)
res_analyse = urllib.request.urlopen(req_analyse)
analyse_data = json.loads(res_analyse.read().decode('utf-8'))
run_id = analyse_data['id']
boxes = analyse_data['boxes']
print(f"Analysis completed: run_id={run_id}, candidate_boxes={len(boxes)}")

# 3. Test predict-crop on first box
crop_req_data = json.dumps({'run_id': run_id, 'bbox': boxes[0]}).encode('utf-8')
req_crop = urllib.request.Request(
    'http://127.0.0.1:8000/api/predict-crop',
    data=crop_req_data,
    headers={'Content-Type': 'application/json'}
)
res_crop = urllib.request.urlopen(req_crop)
crop_res = json.loads(res_crop.read().decode('utf-8'))
print('Predict-crop response:')
for k in ['prediction', 'confidence', 'uncertain', 'models_agree', 'alternatives', 'confidence_scores']:
    val = crop_res.get(k)
    print(f"  {k}: {ascii(val)}")

# 4. Test recognize-all on demo stone
rec_req_data = json.dumps({'run_id': run_id}).encode('utf-8')
req_all = urllib.request.Request(
    'http://127.0.0.1:8000/api/recognize-all',
    data=rec_req_data,
    headers={'Content-Type': 'application/json'}
)
res_all = urllib.request.urlopen(req_all)
all_res = json.loads(res_all.read().decode('utf-8'))
print("Recognize-all candidate_count:", all_res["candidate_count"])
r0 = all_res['regions'][0]
r1 = all_res['regions'][1]
print('Sample region 0:', {k: (ascii(v) if isinstance(v, str) else v) for k, v in r0.items()})
print('Sample region 1:', {k: (ascii(v) if isinstance(v, str) else v) for k, v in r1.items()})
