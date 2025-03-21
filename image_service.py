import tensorflow as tf
from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input, decode_predictions
import numpy as np
from PIL import Image
import os
import logging
import io

class ImageClassificationService:
    """Service for classifying images using TensorFlow MobileNetV2"""
    
    def __init__(self, model_path=None):
        try:
            # Load pre-trained model or custom model if specified
            if model_path and os.path.exists(model_path):
                self.model = tf.keras.models.load_model(model_path)
                logging.info(f"Loaded custom model from {model_path}")
            else:
                # Use pre-trained MobileNetV2
                self.model = MobileNetV2(weights="imagenet")
                logging.info("Loaded pre-trained MobileNetV2 model")
            
            # Load ImageNet labels if available
            self.labels = []
            if os.path.exists("ImageNetLabels.txt"):
                with open("ImageNetLabels.txt", "r") as f:
                    self.labels = f.read().splitlines()
                logging.info(f"Loaded {len(self.labels)} ImageNet labels")
            else:
                logging.warning("ImageNetLabels.txt not found. Label names will not be available.")
        
        except Exception as e:
            logging.error(f"Error initializing image classification service: {str(e)}")
            raise
    
    def preprocess_image(self, image_data):
        """
        Preprocess image data for classification
        
        Args:
            image_data (bytes or PIL.Image): Image data to process
            
        Returns:
            numpy.ndarray: Preprocessed image array
        """
        try:
            # Convert bytes to PIL Image if needed
            if isinstance(image_data, bytes):
                img = Image.open(io.BytesIO(image_data))
            else:
                img = image_data
            
            # Resize to expected dimensions
            img = img.resize((224, 224))
            
            # Convert to RGB if needed
            if img.mode != "RGB":
                img = img.convert("RGB")
            
            # Convert to numpy array and preprocess
            img_array = np.array(img)
            img_array = np.expand_dims(img_array, axis=0)
            return preprocess_input(img_array)
        
        except Exception as e:
            logging.error(f"Error preprocessing image: {str(e)}")
            raise
    
    def classify_image(self, image_data, top_n=3):
        """
        Classify an image
        
        Args:
            image_data (bytes or PIL.Image): Image data to classify
            top_n (int): Number of top predictions to return
            
        Returns:
            dict: Classification results
        """
        try:
            # Preprocess the image
            preprocessed_img = self.preprocess_image(image_data)
            
            # Make prediction
            predictions = self.model.predict(preprocessed_img)
            
            # Decode predictions
            results = decode_predictions(predictions, top=top_n)[0]
            
            # Format results
            formatted_results = [
                {
                    "class_name": item[1].replace('_', ' ').title(),
                    "class_id": item[0],
                    "confidence": float(item[2] * 100)
                }
                for item in results
            ]
            
            return {
                "success": True,
                "predictions": formatted_results
            }
        
        except Exception as e:
            logging.error(f"Error classifying image: {str(e)}")
            return {"error": str(e)}
    
    def get_class_name(self, class_id):
        """
        Get human-readable class name for an ID
        
        Args:
            class_id (int): Class ID from ImageNet
            
        Returns:
            str: Human-readable class name
        """
        if 0 <= class_id < len(self.labels):
            return self.labels[class_id]
        return f"Unknown (ID: {class_id})"
