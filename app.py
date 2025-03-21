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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["http://127.0.0.1:5500", "http://localhost:5500"]}})

HUGGING_FACE_TOKEN = os.environ.get("HUGGING_FACE_TOKEN", "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")
SENTIMENT_API_URL = "https://api-inference.huggingface.co/models/distilbert-base-uncased-finetuned-sst-2-english"
HEADERS = {"Authorization": f"Bearer {HUGGING_FACE_TOKEN}"}

try:
    model = tf.keras.applications.MobileNetV2(weights="imagenet")
    logger.info("Successfully loaded MobileNetV2 model")
except Exception as e:
    logger.error(f"Error loading MobileNetV2 model: {str(e)}")
    model = None

labels = []
try:
    if os.path.exists("ImageNetLabels.txt"):
        with open("ImageNetLabels.txt", "r") as f:
            labels = f.read().splitlines()
        logger.info(f"Loaded {len(labels)} ImageNet labels")
    else:
        logger.warning("ImageNetLabels.txt not found, checking for alternate file")
        if os.path.exists("imagenet_labels.txt"):
            with open("imagenet_labels.txt", "r") as f:
                labels = f.read().splitlines()
            logger.info(f"Loaded {len(labels)} ImageNet labels from alternate file")
        else:
            logger.warning("No labels file found. Label names will not be available.")
except Exception as e:
    logger.error(f"Error loading labels: {str(e)}")

class ProductSearchService:
    """Dịch vụ tìm kiếm sản phẩm thực từ các trang web thương mại điện tử"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9,vi;q=0.8"
        }
        self.timeout = 10
        
        self.product_db = {}
        try:
            if os.path.exists("product_db.json"):
                with open("product_db.json", "r") as f:
                    self.product_db = json.load(f)
                self.logger.info(f"Loaded {len(self.product_db)} product categories from database")
        except Exception as e:
            self.logger.error(f"Error loading product database: {str(e)}")
            self.create_sample_product_db()
        
    def search_products(self, query, max_results=6):
        """
        Tìm kiếm sản phẩm từ nhiều nguồn khác nhau
        
        Args:
            query (str): Từ khóa tìm kiếm
            max_results (int): Số lượng kết quả tối đa
            
        Returns:
            list: Danh sách sản phẩm tìm thấy
        """
        self.logger.info(f"Tìm kiếm sản phẩm với từ khóa: {query}")
        
        all_products = []
        
        try:
            google_products = self.search_google_shopping(query)
            if google_products:
                all_products.extend(google_products)
                self.logger.info(f"Tìm thấy {len(google_products)} sản phẩm từ Google Shopping")
        except Exception as e:
            self.logger.error(f"Lỗi khi tìm trên Google Shopping: {str(e)}")
        
        if not all_products:
            try:
                db_products = self._search_local_db(query)
                if db_products:
                    all_products.extend(db_products)
                    self.logger.info(f"Tìm thấy {len(db_products)} sản phẩm từ cơ sở dữ liệu")
            except Exception as e:
                self.logger.error(f"Lỗi khi tìm trong cơ sở dữ liệu: {str(e)}")
        
        if not all_products:
            fallback_products = self.fallback_products(query)
            all_products.extend(fallback_products)
            self.logger.info(f"Sử dụng {len(fallback_products)} sản phẩm mẫu")
        
        return all_products[:max_results]
    
    def search_google_shopping(self, query, limit=3):
        """Tìm kiếm sản phẩm trên Google Shopping"""
        products = []
        
        try:
            from urllib.parse import quote_plus
            search_url = f"https://www.google.com/search?q={quote_plus(query)}&tbm=shop"
            
            response = requests.get(search_url, headers=self.headers, timeout=self.timeout)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            product_items = soup.select('.sh-dgr__grid-result')
            
            for item in product_items[:limit]:
                try:
                    name_element = item.select_one('.Xjkr3b')
                    price_element = item.select_one('.a8Pemb')
                    merchant_element = item.select_one('.aULzUe')
                    link_element = item.select_one('.Lq5OHe')
                    image_element = item.select_one('img.ArOc1c')
                    
                    if name_element and price_element and link_element:
                        name = name_element.text.strip()
                        price_text = price_element.text.strip()
                        
                        merchant = ""
                        if merchant_element:
                            merchant = merchant_element.text.strip()
                            
                        link = link_element.get('href')
                        if link and link.startswith('/'):
                            link = f"https://www.google.com{link}"
                            
                        image_url = ""
                        if image_element:
                            image_url = image_element.get('src', '')
                        
                        product_info = {
                            'title': name,
                            'price_text': price_text,
                            'url': link,
                            'image_url': image_url,
                            'source': f'Google Shopping{f" - {merchant}" if merchant else ""}'
                        }
                        
                        import re
                        price_match = re.search(r'[\d.,]+', price_text)
                        if price_match:
                            try:
                                price_str = price_match.group(0).replace('.', '').replace(',', '')
                                product_info['price'] = float(price_str)
                            except:
                                product_info['price'] = price_text
                        else:
                            product_info['price'] = "Xem trên trang"
                        
                        products.append(product_info)
                except Exception as e:
                    self.logger.error(f"Lỗi khi xử lý sản phẩm Google Shopping: {str(e)}")
                    continue
                    
                if len(products) >= limit:
                    break
        except Exception as e:
            self.logger.error(f"Lỗi khi tìm kiếm trên Google Shopping: {str(e)}")
            
        return products
    
    def _search_local_db(self, query, limit=3):
        """Search for products in local product database"""
        results = []
        query = query.lower()
        
        for category, products in self.product_db.items():
            if query in category.lower() or category.lower() in query:
                results.extend(products[:limit])
                if len(results) >= limit:
                    break
        
        return results[:limit]
    
    def fallback_products(self, query, limit=3):
        """
        Tạo dữ liệu mẫu khi không tìm thấy sản phẩm thực
        
        Args:
            query (str): Từ khóa tìm kiếm
            limit (int): Số lượng sản phẩm trả về
            
        Returns:
            list: Danh sách sản phẩm mẫu
        """
        sample_products = []
        from urllib.parse import quote_plus
        
        if "espresso" in query.lower() or "coffee" in query.lower() or "coffeepot" in query.lower():
            sample_products = [
                {
                    "title": f"Máy pha cà phê Espresso cao cấp",
                    "description": "Máy pha cà phê espresso chuyên nghiệp với áp suất 15 bar",
                    "price": 5500000,
                    "price_text": "5.500.000₫",
                    "rating": 4.7,
                    "url": "#",
                    "image_url": "https://via.placeholder.com/150?text=Espresso+Maker",
                    "source": "Dữ liệu mẫu"
                },
                {
                    "title": f"Máy pha cà phê Espresso tự động",
                    "description": "Máy pha cà phê tự động với chức năng nghiền hạt",
                    "price": 8900000,
                    "price_text": "8.900.000₫",
                    "rating": 4.5,
                    "url": "#",
                    "image_url": "https://via.placeholder.com/150?text=Auto+Espresso",
                    "source": "Dữ liệu mẫu"
                },
                {
                    "title": f"Máy pha cà phê Espresso mini",
                    "description": "Máy pha cà phê espresso nhỏ gọn dành cho gia đình",
                    "price": 2200000,
                    "price_text": "2.200.000₫",
                    "rating": 4.2,
                    "url": "#",
                    "image_url": "https://via.placeholder.com/150?text=Mini+Espresso",
                    "source": "Dữ liệu mẫu"
                }
            ]
        else:
            price_ranges = [(1000000, 3000000), (3000000, 8000000), (8000000, 15000000)]
            
            for i in range(limit):
                import random
                price_range = price_ranges[i % len(price_ranges)]
                price = random.randint(price_range[0], price_range[1])
                price_formatted = f"{price:,}₫".replace(",", ".")
                
                sample_products.append({
                    "title": f"{query.title()} - Mẫu {i+1}",
                    "description": f"Sản phẩm {query} chất lượng cao",
                    "price": price,
                    "price_text": price_formatted,
                    "rating": round(random.uniform(3.5, 5.0), 1),
                    "url": "#",
                    "image_url": f"https://via.placeholder.com/150?text={quote_plus(query)}+{i+1}",
                    "source": "Dữ liệu mẫu"
                })
                
        return sample_products[:limit]

    def create_sample_product_db(self, output_file="product_db.json"):
        """
        Create a sample product database with some common categories
        This is for demonstration purposes only
        """
        categories = {
            "laptop": [
                {
                    "title": "Laptop - Premium Model",
                    "description": "High-performance laptop with 16GB RAM and 1TB SSD",
                    "price": 15000000,
                    "price_text": "15.000.000₫",
                    "rating": 4.7,
                    "url": "#",
                    "image_url": "https://via.placeholder.com/150?text=Premium+Laptop",
                    "source": "Sample Data"
                },
                {
                    "title": "Laptop - Standard Edition",
                    "description": "Reliable laptop for everyday use with 8GB RAM",
                    "price": 9500000,
                    "price_text": "9.500.000₫",
                    "rating": 4.3,
                    "url": "#",
                    "image_url": "https://via.placeholder.com/150?text=Standard+Laptop",
                    "source": "Sample Data"
                },
                {
                    "title": "Laptop - Budget Friendly",
                    "description": "Affordable laptop for basic computing needs",
                    "price": 5500000,
                    "price_text": "5.500.000₫",
                    "rating": 4.0,
                    "url": "#",
                    "image_url": "https://via.placeholder.com/150?text=Budget+Laptop",
                    "source": "Sample Data"
                }
            ],
            "smartphone": [
                {
                    "title": "Smartphone - Premium Model",
                    "description": "Flagship smartphone with advanced camera system",
                    "price": 12000000,
                    "price_text": "12.000.000₫",
                    "rating": 4.8,
                    "url": "#",
                    "image_url": "https://via.placeholder.com/150?text=Premium+Phone",
                    "source": "Sample Data"
                },
                {
                    "title": "Smartphone - Mid-range",
                    "description": "Great performance at a reasonable price",
                    "price": 6000000,
                    "price_text": "6.000.000₫",
                    "rating": 4.5,
                    "url": "#",
                    "image_url": "https://via.placeholder.com/150?text=Midrange+Phone",
                    "source": "Sample Data"
                },
                {
                    "title": "Smartphone - Entry Level",
                    "description": "Affordable smartphone with essential features",
                    "price": 2500000,
                    "price_text": "2.500.000₫",
                    "rating": 4.0,
                    "url": "#",
                    "image_url": "https://via.placeholder.com/150?text=Budget+Phone",
                    "source": "Sample Data"
                }
            ],
            "espresso maker": [
                {
                    "title": "Máy pha cà phê Espresso cao cấp",
                    "description": "Máy pha cà phê espresso chuyên nghiệp với áp suất 15 bar",
                    "price": 5500000,
                    "price_text": "5.500.000₫",
                    "rating": 4.7,
                    "url": "#",
                    "image_url": "https://via.placeholder.com/150?text=Espresso+Maker",
                    "source": "Sample Data"
                },
                {
                    "title": "Máy pha cà phê Espresso tự động",
                    "description": "Máy pha cà phê tự động với chức năng nghiền hạt",
                    "price": 8900000,
                    "price_text": "8.900.000₫",
                    "rating": 4.5,
                    "url": "#",
                    "image_url": "https://via.placeholder.com/150?text=Auto+Espresso",
                    "source": "Sample Data"
                },
                {
                    "title": "Máy pha cà phê Espresso mini",
                    "description": "Máy pha cà phê espresso nhỏ gọn dành cho gia đình",
                    "price": 2200000,
                    "price_text": "2.200.000₫",
                    "rating": 4.2,
                    "url": "#",
                    "image_url": "https://via.placeholder.com/150?text=Mini+Espresso",
                    "source": "Sample Data"
                }
            ],
            "coffee pot": [
                {
                    "title": "Bình đun cà phê cao cấp",
                    "description": "Bình pha cà phê bằng thép không gỉ dung tích 1 lít",
                    "price": 850000,
                    "price_text": "850.000₫",
                    "rating": 4.5,
                    "url": "#",
                    "image_url": "https://via.placeholder.com/150?text=Coffee+Pot",
                    "source": "Sample Data"
                },
                {
                    "title": "Bình đun cà phê Moka Pot",
                    "description": "Bình pha cà phê kiểu Ý 300ml",
                    "price": 450000,
                    "price_text": "450.000₫",
                    "rating": 4.3,
                    "url": "#",
                    "image_url": "https://via.placeholder.com/150?text=Moka+Pot",
                    "source": "Sample Data"
                },
                {
                    "title": "Bộ pha cà phê thủy tinh",
                    "description": "Bộ pha cà phê kiểu Pour Over bằng thủy tinh",
                    "price": 650000,
                    "price_text": "650.000₫",
                    "rating": 4.4,
                    "url": "#",
                    "image_url": "https://via.placeholder.com/150?text=Pour+Over",
                    "source": "Sample Data"
                }
            ]
        }
        
        with open(output_file, "w") as f:
            json.dump(categories, f, indent=2)
            
        self.product_db = categories
        self.logger.info(f"Created sample product database with {len(categories)} categories")
        return categories

try:
    from bs4 import BeautifulSoup
    product_search_service = ProductSearchService()
    
    if not os.path.exists("product_db.json"):
        product_search_service.create_sample_product_db()
        logger.info("Created sample product database")
except ImportError:
    logger.warning("BeautifulSoup not installed. Product recommendation service will not be available.")
    product_search_service = None
except Exception as e:
    logger.error(f"Error initializing product search service: {str(e)}")
    product_search_service = None

def image_preprocessing(img):
    """
    Preprocess image for MobileNetV2 model
    
    Args:
        img: Image to preprocess (PIL Image or numpy array)
    
    Returns:
        Preprocessed image array ready for model prediction
    """
    if isinstance(img, Image.Image):
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
        
        img = Image.open(io.BytesIO(file.read()))
        img = img.resize((224, 224))
        
        if img.mode != "RGB":
            img = img.convert("RGB")
            
        img_array = image_preprocessing(img)
        
        predictions = model.predict(img_array)
        results = decode_predictions(predictions, top=3)[0]
        
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

@app.route('/recommend-products', methods=['POST'])
def recommend_products():
    """Endpoint đề xuất sản phẩm dựa trên kết quả phân loại hình ảnh"""
    try:
        if product_search_service is None:
            return jsonify({
                "error": "Dịch vụ đề xuất sản phẩm không khả dụng"
            }), 500
            
        data = request.json
        if not data or 'predictions' not in data:
            return jsonify({
                "error": "Không có dữ liệu phân loại hình ảnh được cung cấp"
            }), 400
            
        predictions = data['predictions']
        
        if not predictions or len(predictions) == 0:
            return jsonify({
                "error": "Không tìm thấy kết quả phân loại hình ảnh"
            }), 400
        
        top_prediction = predictions[0]
        search_query = top_prediction.get("class_name", "").replace("_", " ")
        
        logger.info(f"Tìm kiếm sản phẩm với từ khóa: {search_query}")
        
        max_results = int(request.args.get('max_results', 6))
        
        product_results = product_search_service.search_products(search_query, max_results)
        
        return jsonify({
            "success": True,
            "recommendations": product_results,
            "search_query": search_query,
            "confidence": top_prediction.get("confidence", 0)
        })
    
    except Exception as e:
        logger.error(f"Lỗi khi đề xuất sản phẩm: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/analyze-sentiment', methods=['POST'])
def analyze_sentiment():
    """Endpoint for analyzing customer reviews sentiment using Hugging Face API"""
    try:
        data = request.json
        if not data or 'text' not in data:
            return jsonify({"error": "No text provided"}), 400
            
        text = data['text']
        
        payload = {"inputs": text}
        response = requests.post(SENTIMENT_API_URL, headers=HEADERS, json=payload)
        
        if response.status_code != 200:
            logger.error(f"Hugging Face API error: {response.status_code} - {response.text}")
            return jsonify({
                "error": f"Sentiment analysis API returned status code {response.status_code}",
                "details": response.text
            }), 500
            
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
    
@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint for checking the health of the application"""
    return jsonify({
        "status": "healthy",
        "services": {
            "image_classification": model is not None,
            "sentiment_analysis": HUGGING_FACE_TOKEN is not None,
            "labels_loaded": len(labels) > 0,
            "product_recommendations": product_search_service is not None
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
    logger.info(f"Product recommendation service available: {product_search_service is not None}")
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)