# vision_model.py
import tensorflow as tf
from tensorflow import keras
import numpy as np

class DEKAIVision:
    def __init__(self, model_path="models/dekai_vision"):
        print("🔹 Loading DEKAI-Vision model...")
        self.model = keras.models.load_model(model_path)
        print("✅ Vision model ready.")

    def predict_caption(self, image_tensor):
        preds = self.model.predict(image_tensor)
        pred_tokens = tf.argmax(preds, axis=-1).numpy()[0]
        # Convert token IDs to words if using a tokenizer
        # For now, assume model outputs text directly
        return str(pred_tokens)


