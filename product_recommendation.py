import requests
import json
import os
import logging
import time
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

class EcommerceProductRecommendation:
    """
    Dịch vụ gợi ý sản phẩm từ các trang thương mại điện tử như Shopee, Lazada
    dựa trên kết quả phân loại hình ảnh
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Directory lưu kết quả phân loại
        self.results_dir = "classification_results"
        os.makedirs(self.results_dir, exist_ok=True)
        
        # Headers cho requests
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9,vi;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8"
        }
    
    def save_classification_result(self, image_id, classification_result):
        """
        Lưu kết quả phân loại để sử dụng sau này
        
        Args:
            image_id (str): ID của hình ảnh được phân loại
            classification_result (dict): Kết quả phân loại từ API
        """
        file_path = os.path.join(self.results_dir, f"{image_id}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(classification_result, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"Đã lưu kết quả phân loại cho ảnh {image_id}")
        return file_path
    
    def get_product_recommendations(self, classification_result, num_products=6, platforms=None):
        """
        Lấy gợi ý sản phẩm từ các trang thương mại điện tử dựa trên kết quả phân loại
        
        Args:
            classification_result (dict): Kết quả phân loại từ API
            num_products (int): Số sản phẩm cần gợi ý
            platforms (list): Danh sách các nền tảng cần tìm kiếm (shopee, lazada, tiki...)
            
        Returns:
            dict: Danh sách sản phẩm gợi ý từ các nền tảng
        """
        if not platforms:
            platforms = ["shopee", "lazada"]
        
        if not classification_result.get("predictions"):
            return {"error": "Không có kết quả phân loại"}
        
        # Lấy top 2 categories có độ tin cậy cao nhất
        top_categories = classification_result["predictions"][:2]
        search_queries = [item["class_name"] for item in top_categories]
        
        recommendations = {
            "based_on": classification_result,
            "recommendations": {}
        }
        
        for platform in platforms:
            recommendations["recommendations"][platform] = []
            
            for query in search_queries:
                # Tìm kiếm sản phẩm trên nền tảng
                platform_results = self._search_platform(platform, query, num_products // len(search_queries))
                recommendations["recommendations"][platform].extend(platform_results)
        
        return recommendations
    
    def _search_platform(self, platform, query, num_products):
        """
        Tìm kiếm sản phẩm trên một nền tảng cụ thể
        
        Args:
            platform (str): Tên nền tảng (shopee, lazada...)
            query (str): Từ khóa tìm kiếm
            num_products (int): Số sản phẩm cần trả về
            
        Returns:
            list: Danh sách sản phẩm tìm thấy
        """
        if platform.lower() == "shopee":
            return self._search_shopee(query, num_products)
        elif platform.lower() == "lazada":
            return self._search_lazada(query, num_products)
        elif platform.lower() == "tiki":
            return self._search_tiki(query, num_products)
        else:
            self.logger.warning(f"Nền tảng {platform} không được hỗ trợ")
            return []
    
    def _search_shopee(self, query, num_products):
        """
        Tìm kiếm sản phẩm trên Shopee
        
        Args:
            query (str): Từ khóa tìm kiếm
            num_products (int): Số sản phẩm cần trả về
            
        Returns:
            list: Danh sách sản phẩm từ Shopee
        """
        products = []
        escaped_query = quote_plus(query)
        
        try:
            # URL tìm kiếm Shopee
            url = f"https://shopee.vn/search?keyword={escaped_query}"
            self.logger.info(f"Tìm kiếm trên Shopee với từ khóa: {query}")
            
            # Sử dụng Shopee API thay vì scraping trực tiếp 
            # URL API có thể thay đổi theo thời gian
            api_url = f"https://shopee.vn/api/v4/search/search_items?by=relevancy&keyword={escaped_query}&limit={num_products}&newest=0&order=desc&page_type=search&scenario=PAGE_GLOBAL_SEARCH&version=2"
            
            response = requests.get(api_url, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Xử lý dữ liệu từ API
                if "items" in data and data["items"]:
                    for item in data["items"][:num_products]:
                        product_data = item.get("item_basic", {})
                        
                        if product_data:
                            # Định dạng URL hình ảnh Shopee
                            image_id = product_data.get("image", "")
                            shop_id = product_data.get("shopid", "")
                            item_id = product_data.get("itemid", "")
                            
                            image_url = f"https://cf.shopee.vn/file/{image_id}"
                            product_url = f"https://shopee.vn/{product_data.get('name', '').replace(' ', '-')}-i.{shop_id}.{item_id}"
                            
                            product = {
                                "platform": "Shopee",
                                "name": product_data.get("name", "Sản phẩm Shopee"),
                                "price": f"{product_data.get('price', 0) / 100000:,.0f}đ",
                                "original_price": f"{product_data.get('price_before_discount', 0) / 100000:,.0f}đ" if product_data.get('price_before_discount', 0) > 0 else None,
                                "image_url": image_url,
                                "product_url": product_url,
                                "rating": product_data.get("item_rating", {}).get("rating_star", 0),
                                "sold": product_data.get("historical_sold", 0)
                            }
                            products.append(product)
            
            # Nếu không có kết quả từ API, thử scraping HTML
            if not products:
                self.logger.info("Không có kết quả từ API Shopee, thử scraping HTML")
                response = requests.get(url, headers=self.headers)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    # Logic scraping HTML (phức tạp và có thể thay đổi)
                    # Chú ý: Shopee sử dụng JavaScript để render sản phẩm, không dễ để scrape
        
        except Exception as e:
            self.logger.error(f"Lỗi khi tìm kiếm trên Shopee: {str(e)}")
        
        return products
    
    def _search_lazada(self, query, num_products):
        """
        Tìm kiếm sản phẩm trên Lazada
        
        Args:
            query (str): Từ khóa tìm kiếm
            num_products (int): Số sản phẩm cần trả về
            
        Returns:
            list: Danh sách sản phẩm từ Lazada
        """
        products = []
        escaped_query = quote_plus(query)
        
        try:
            url = f"https://www.lazada.vn/catalog/?q={escaped_query}"
            self.logger.info(f"Tìm kiếm trên Lazada với từ khóa: {query}")
            
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Lazada stores product data in a script tag as JSON
                script_tag = soup.find('script', text=lambda t: t and 'window.pageData=' in t)
                
                if script_tag:
                    # Extract JSON data
                    json_text = script_tag.string.split('window.pageData=')[1].split('</script>')[0].strip()
                    try:
                        # Clean the JSON text (remove trailing semicolons, etc.)
                        if json_text.endswith(';'):
                            json_text = json_text[:-1]
                        
                        data = json.loads(json_text)
                        
                        # Extract product information
                        if 'mods' in data and 'listItems' in data['mods']:
                            items = data['mods']['listItems']
                            
                            for item in items[:num_products]:
                                product = {
                                    "platform": "Lazada",
                                    "name": item.get('name', 'Sản phẩm Lazada'),
                                    "price": item.get('price', ''),
                                    "original_price": item.get('originalPrice', '') if item.get('originalPrice') != item.get('price') else None,
                                    "image_url": item.get('image', ''),
                                    "product_url": f"https://www.lazada.vn/products/{item.get('nid', '')}",
                                    "rating": item.get('ratingScore', 0),
                                    "sold": item.get('sold', 0)
                                }
                                products.append(product)
                    except json.JSONDecodeError as e:
                        self.logger.error(f"Lỗi khi parse JSON từ Lazada: {str(e)}")
        
        except Exception as e:
            self.logger.error(f"Lỗi khi tìm kiếm trên Lazada: {str(e)}")
        
        return products
    
    def _search_tiki(self, query, num_products):
        """
        Tìm kiếm sản phẩm trên Tiki
        
        Args:
            query (str): Từ khóa tìm kiếm
            num_products (int): Số sản phẩm cần trả về
            
        Returns:
            list: Danh sách sản phẩm từ Tiki
        """
        products = []
        escaped_query = quote_plus(query)
        
        try:
            # Sử dụng API của Tiki
            api_url = f"https://tiki.vn/api/v2/products?limit={num_products}&q={escaped_query}"
            self.logger.info(f"Tìm kiếm trên Tiki với từ khóa: {query}")
            
            response = requests.get(api_url, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'data' in data:
                    for item in data['data'][:num_products]:
                        product = {
                            "platform": "Tiki",
                            "name": item.get('name', 'Sản phẩm Tiki'),
                            "price": f"{item.get('price', 0):,.0f}đ",
                            "original_price": f"{item.get('original_price', 0):,.0f}đ" if item.get('original_price', 0) > item.get('price', 0) else None,
                            "image_url": item.get('thumbnail_url', ''),
                            "product_url": f"https://tiki.vn/{item.get('url_path', '')}",
                            "rating": item.get('rating_average', 0),
                            "sold": item.get('quantity_sold', {}).get('value', 0)
                        }
                        products.append(product)
        
        except Exception as e:
            self.logger.error(f"Lỗi khi tìm kiếm trên Tiki: {str(e)}")
        
        return products
