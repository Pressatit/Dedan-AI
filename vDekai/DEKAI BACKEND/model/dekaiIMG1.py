from PIL import Image
import torch
import io
import torch.nn.functional as F
import os
from transformers import ViTForImageClassification, ViTImageProcessor

device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")

current_dir = os.path.dirname(os.path.abspath(__file__))
# Point to the model folder sitting next to it
local_path = os.path.join(current_dir, "dekai_final_model")

local_model = ViTForImageClassification.from_pretrained(local_path).to(device)
local_processor = ViTImageProcessor.from_pretrained(local_path)

local_model.eval()

def predict_landmark(image: Image.Image):

    inputs = local_processor(image, return_tensors="pt").to(device)
    
    with torch.no_grad():
        outputs = local_model(**inputs)
    
    """
    probabilities = F.softmax(outputs.logits, dim=-1)
    
   
    conf_score, predicted_id = torch.max(probabilities, dim=-1)
    
    confidence = conf_score.item()
    
    
    # 4. Set your Confidence Threshold (0.6 = 60%)
    THRESHOLD = 0.4
    
    if confidence < THRESHOLD:
        # Instead of a landmark name, return a specific "unsure" flag
        return "Unknown Landmark"
    """
    # Otherwise, return the actual name from our 84 classes
    predicted_id = outputs.logits.argmax(-1).item()

    result = local_model.config.id2label[predicted_id]
    return result
