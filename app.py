from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import tensorflow as tf
from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input, decode_predictions
import numpy as np
from PIL import Image
import io
import os
import requests
import cv2
import logging
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask application
app = Flask(__name__)
CORS(app)

# Hugging Face API configuration
HUGGING_FACE_TOKEN = os.environ.get("HUGGING_FACE_TOKEN", "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")
SENTIMENT_API_URL = "https://api-inference.huggingface.co/models/distilbert-base-uncased-finetuned-sst-2-english"
HEADERS = {"Authorization": f"Bearer {HUGGING_FACE_TOKEN}"}

# Load TensorFlow MobileNetV2 model for image classification
try:
    model = tf.keras.applications.MobileNetV2(weights="imagenet")
    logger.info("Successfully loaded MobileNetV2 model")
except Exception as e:
    logger.error(f"Error loading MobileNetV2 model: {str(e)}")
    model = None

# Load ImageNet labels
labels = []
try:
    if os.path.exists("ImageNetLabels.txt"):
        with open("ImageNetLabels.txt", "r") as f:
            labels = f.read().splitlines()
        logger.info(f"Loaded {len(labels)} ImageNet labels")
    else:
        logger.warning("ImageNetLabels.txt not found, checking for alternate file")
        # Try alternate file name
        if os.path.exists("imagenet_labels.txt"):
            with open("imagenet_labels.txt", "r") as f:
                labels = f.read().splitlines()
            logger.info(f"Loaded {len(labels)} ImageNet labels from alternate file")
        else:
            logger.warning("No labels file found. Label names will not be available.")
except Exception as e:
    logger.error(f"Error loading labels: {str(e)}")

def image_preprocessing(img):
    """
    Preprocess image for MobileNetV2 model
    
    Args:
        img: Image to preprocess (PIL Image or numpy array)
    
    Returns:
        Preprocessed image array ready for model prediction
    """
    if isinstance(img, Image.Image):
        # Convert PIL Image to numpy array
        img_array = np.array(img)
    else:
        img_array = img
        
    img_array = np.expand_dims(img_array, axis=0)
    return preprocess_input(img_array)

@app.route('/')
def home():
    """Render the main application page"""
    return render_template("index.html")

@app.route('/classify', methods=['POST'])
def classify_image():
    """Endpoint for classifying product images using TensorFlow MobileNetV2"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    try:
        if model is None:
            return jsonify({'error': 'Image classification model not available'}), 500
        
        file = request.files['file']
        
        # Read and preprocess the image
        img = Image.open(io.BytesIO(file.read()))
        img = img.resize((224, 224))
        
        # Convert to RGB if needed
        if img.mode != "RGB":
            img = img.convert("RGB")
            
        img_array = image_preprocessing(img)
        
        # Make prediction
        predictions = model.predict(img_array)
        results = decode_predictions(predictions, top=3)[0]
        
        # Format results
        formatted_results = [
            {
                "class_name": item[1].replace('_', ' ').title(),
                "class_id": item[0],
                "confidence": float(item[2] * 100)
            }
            for item in results
        ]
        
        return jsonify({
            "success": True,
            "predictions": formatted_results
        })
    
    except Exception as e:
        logger.error(f"Error in image classification: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/analyze-sentiment', methods=['POST'])
def analyze_sentiment():
    """Endpoint for analyzing customer reviews sentiment using Hugging Face API"""
    try:
        data = request.json
        if not data or 'text' not in data:
            return jsonify({"error": "No text provided"}), 400
            
        text = data['text']
        
        # Call Hugging Face API for sentiment analysis
        payload = {"inputs": text}
        response = requests.post(SENTIMENT_API_URL, headers=HEADERS, json=payload)
        
        # Check if the request was successful
        if response.status_code != 200:
            logger.error(f"Hugging Face API error: {response.status_code} - {response.text}")
            return jsonify({
                "error": f"Sentiment analysis API returned status code {response.status_code}",
                "details": response.text
            }), 500
            
        sentiment_data = response.json()
        
        # Process the response
        if isinstance(sentiment_data, list) and len(sentiment_data) > 0:
            result = sentiment_data[0]
            # Extract and format the sentiment analysis results
            sentiments = sorted(result, key=lambda x: x['score'], reverse=True)
            
            # Map sentiment labels to more user-friendly terms
            sentiment_mapping = {
                "POSITIVE": "Positive",
                "NEGATIVE": "Negative",
                "NEUTRAL": "Neutral"
            }
            
            formatted_results = [
                {
                    "sentiment": sentiment_mapping.get(item['label'], item['label']),
                    "confidence": round(item['score'] * 100, 2)
                }
                for item in sentiments
            ]
            
            # Determine overall sentiment
            overall_sentiment = formatted_results[0]['sentiment']
            
            return jsonify({
                "success": True,
                "overall_sentiment": overall_sentiment,
                "details": formatted_results,
                "text": text
            })
        else:
            logger.error(f"Invalid response from sentiment analysis API: {sentiment_data}")
            return jsonify({
                "error": "Invalid response from sentiment analysis API", 
                "raw_response": sentiment_data
            }), 500
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error in sentiment analysis: {str(e)}")
        return jsonify({"error": f"API request failed: {str(e)}"}), 500
    
    except Exception as e:
        logger.error(f"Error in sentiment analysis: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/recommend-products', methods=['POST'])
def recommend_products():
    """Endpoint for recommending products based on image classification results"""
    try:
        data = request.json
        if not data or 'predictions' not in data:
            return jsonify({"error": "Không có kết quả phân loại được cung cấp"}), 400
            
        # Import the product recommendation service
        from product_recommendation import EcommerceProductRecommendation
        
        # Initialize the recommendation service
        recommender = EcommerceProductRecommendation()
        
        # Get recommendations based on the classification results
        recommendations = recommender.get_product_recommendations(
            classification_result=data,
            num_products=6,  # Number of products to recommend
            platforms=["shopee", "lazada"]  # Platforms to search
        )
        
        return jsonify(recommendations)
    
    except Exception as e:
        logger.error(f"Error in product recommendation: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint for checking the health of the application"""
    return jsonify({
        "status": "healthy",
        "services": {
            "image_classification": model is not None,
            "sentiment_analysis": HUGGING_FACE_TOKEN is not None,
            "labels_loaded": len(labels) > 0
        },
        "version": "1.0.0"
    })

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    return jsonify({"error": "Internal server error"}), 500

@app.route('/api/docs', methods=['GET'])
def api_docs():
    """Provide simple API documentation"""
    docs = {
        "version": "1.0.0",
        "endpoints": [
            {
                "path": "/",
                "method": "GET",
                "description": "Main application interface"
            },
            {
                "path": "/classify",
                "method": "POST",
                "description": "Classify product images using TensorFlow",
                "parameters": [
                    {
                        "name": "file",
                        "type": "file",
                        "required": True,
                        "description": "Image file to classify"
                    }
                ]
            },
            {
                "path": "/analyze-sentiment",
                "method": "POST",
                "description": "Analyze sentiment of customer reviews",
                "parameters": [
                    {
                        "name": "text",
                        "type": "string",
                        "required": True,
                        "description": "Text content to analyze"
                    }
                ]
            },
            {
                "path": "/recommend-products",
                "method": "POST",
                "description": "Get product recommendations based on image classification",
                "parameters": [
                    {
                        "name": "predictions",
                        "type": "array",
                        "required": True,
                        "description": "Classification results from /classify endpoint"
                    }
                ]
            },
            {
                "path": "/health",
                "method": "GET",
                "description": "Health check endpoint"
            }
        ]
    }
    return jsonify(docs)

if __name__ == '__main__':
    logger.info("Starting Product Analysis Platform")
    logger.info(f"Image classification model loaded: {model is not None}")
    logger.info(f"Labels loaded: {len(labels)} labels available")
    logger.info(f"Hugging Face API token configured: {HUGGING_FACE_TOKEN is not None}")
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)