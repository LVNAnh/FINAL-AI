import requests
import os
import logging

class SentimentAnalysisService:
    """Service for analyzing sentiment using Hugging Face API"""
    
    def __init__(self, api_token=None):
        self.api_token = api_token or os.environ.get("HUGGING_FACE_TOKEN")
        
        if not self.api_token:
            logging.warning("No Hugging Face API token provided. Sentiment analysis will not work.")
        
        self.sentiment_model = "distilbert-base-uncased-finetuned-sst-2-english"
        self.headers = {"Authorization": f"Bearer {self.api_token}"}
        
    def get_api_url(self, model_name=None):
        """Generate the API URL for the specified model"""
        model = model_name or self.sentiment_model
        return f"https://api-inference.huggingface.co/models/{model}"
    
    def analyze_text(self, text, model_name=None):
        """
        Analyze the sentiment of the provided text
        
        Args:
            text (str): The text to analyze
            model_name (str, optional): The Hugging Face model to use
            
        Returns:
            dict: Processed sentiment analysis results
        """
        if not self.api_token:
            return {"error": "No API token configured for Hugging Face"}
        
        try:
            api_url = self.get_api_url(model_name)
            payload = {"inputs": text}
            
            response = requests.post(api_url, headers=self.headers, json=payload)
            response.raise_for_status()  
            
            sentiment_data = response.json()
            
            if isinstance(sentiment_data, list) and len(sentiment_data) > 0:
                result = sentiment_data[0]
                
                sentiments = sorted(result, key=lambda x: x['score'], reverse=True)
                
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
                
                overall_sentiment = formatted_results[0]['sentiment']
                
                return {
                    "success": True,
                    "overall_sentiment": overall_sentiment,
                    "details": formatted_results,
                    "text": text
                }
            else:
                return {
                    "error": "Invalid response from sentiment analysis API",
                    "raw_response": sentiment_data
                }
        
        except requests.exceptions.RequestException as e:
            return {"error": f"API request failed: {str(e)}"}
        
        except Exception as e:
            return {"error": f"Sentiment analysis failed: {str(e)}"}
