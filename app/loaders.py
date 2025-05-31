import joblib
import json
import os

MODELS_PATH = os.path.dirname(__file__)

def load_model():
    return joblib.load(os.path.join(MODELS_PATH, 'xgb_final_model.pkl'))

def load_preprocessor():
    return joblib.load(os.path.join(MODELS_PATH, 'preprocessor.pkl'))

def load_label_encoder():
    return joblib.load(os.path.join(MODELS_PATH, 'label_encoder.pkl'))

def load_feature_columns():
    with open(os.path.join(MODELS_PATH, 'feature_columns.json'), 'r') as f:
        return json.load(f)
    
def load_model_assets():
    model = load_model()
    preprocessor = load_preprocessor()
    label_encoder = load_label_encoder()
    feature_columns = load_feature_columns()
    return model, preprocessor, label_encoder, feature_columns
