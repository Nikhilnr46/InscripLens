"""Predict one supplied character crop using a locally trained model.
Only load model files produced by this project; joblib files execute Python on load.
Usage: python predict_character.py MODEL.joblib CROP.png
"""
import argparse, json
import joblib
from run_character_benchmark import features

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('model');p.add_argument('image');a=p.parse_args()
    loaded=joblib.load(a.model)
    model=loaded['model'] if isinstance(loaded,dict) else loaded
    variant=loaded['preprocessing'] if isinstance(loaded,dict) else 'original'
    prediction=str(model.predict(features(a.image,variant).reshape(1,-1))[0])
    print(json.dumps({'predicted_source_label':prediction,'preprocessing':variant,'input_scope':'single supplied character crop','verified_transcription':False},ensure_ascii=True))
