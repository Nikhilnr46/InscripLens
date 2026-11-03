from pathlib import Path
import numpy as np
from PIL import Image
from recognize_regions import recognize,match_boxes
from run_character_benchmark import features
assert recognize(Image.new('L',(30,30),0),{})==[]
assert match_boxes([],[])==[]
assert len(match_boxes([[0,0,10,10]],[[0,0,10,10],[0,0,10,10]]))==1
assert match_boxes([[0,0,10,10]],[[20,20,30,30]])==[]
assert match_boxes([[0,0,10,10]],[[0,0,10,10]])==[(0,0,1.0)]
path=next((Path(__file__).resolve().parent/'full_binarizer/crops/val').glob('*.png'))
with Image.open(path) as im:assert np.array_equal(features(path,'median'),features(im,'median'))
print('PASS blank mask, empty/disjoint/duplicate matching, and unchanged image/path features')
