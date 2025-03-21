# import requests
# import json
# import os
# import logging
# import time
# import random
# from urllib.parse import quote_plus
# from bs4 import BeautifulSoup
# from functools import lru_cache

# class EcommerceProductRecommendation:
#     """
#     Dịch vụ gợi ý sản phẩm từ các trang thương mại điện tử như Shopee, Lazada, Tiki
#     dựa trên kết quả phân loại hình ảnh
#     """
    
#     def __init__(self, cache_dir=None):
#         self.logger = logging.getLogger(__name__)
        
#         # Directory lưu kết quả phân loại và cache
#         self.results_dir = "classification_results"
#         os.makedirs(self.results_dir, exist_ok=True)
        
#         # Directory cho cache
#         self.cache_dir = cache_dir or "recommendation_cache"
#         os.makedirs(self.cache_dir, exist_ok=True)
        
#         # Thời gian cache (24 giờ)
#         self.cache_expire_time = 24 * 60 * 60
        
#         # Danh sách User-Agent để tránh bị chặn
#         self.user_agents = [
#             "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
#             "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36",
#             "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15",
#             "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
#         ]
        
#         # Headers cơ bản cho requests
#         self.get_headers()
    
#     def get_headers(self):
#         """
#         Tạo headers ngẫu nhiên cho mỗi request để tránh bị chặn
        
#         Returns:
#             dict: Headers cho request
#         """
#         # Chọn User-Agent ngẫu nhiên
#         user_agent = random.choice(self.user_agents)
        
#         return {
#             "User-Agent": user_agent,
#             "Accept-Language": "en-US,en;q=0.9,vi;q=0.8",
#             "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
#             "Cache-Control": "no-cache",
#             "Pragma": "no-cache",
#             "Sec-Fetch-Dest": "document",
#             "Sec-Fetch-Mode": "navigate",
#             "Sec-Fetch-Site": "none",
#             "Sec-Fetch-User": "?1"
#         }
    
#     def save_classification_result(self, image_id, classification_result):
#         """
#         Lưu kết quả phân loại để sử dụng sau này
        
#         Args:
#             image_id (str): ID của hình ảnh được phân loại
#             classification_result (dict): Kết quả phân loại từ API
#         """
#         file_path = os.path.join(self.results_dir, f"{image_id}.json")
#         with open(file_path, 'w', encoding='utf-8') as f:
#             json.dump(classification_result, f, ensure_ascii=False, indent=2)
        
#         self.logger.info(f"Đã lưu kết quả phân loại cho ảnh {image_id}")
#         return file_path
    
#     def _get_cache_path(self, platform, query):
#         """
#         Tạo đường dẫn file cache
        
#         Args:
#             platform (str): Tên nền tảng
#             query (str): Từ khóa tìm kiếm
            
#         Returns:
#             str: Đường dẫn file cache
#         """
#         # Chuẩn hóa query để dùng làm tên file
#         safe_query = "".join(c if c.isalnum() or c in ['-', '_'] else '_' for c in query)
#         return os.path.join(self.cache_dir, f"{platform}_{safe_query}.json")
    
#     def _save_to_cache(self, platform, query, data):
#         """
#         Lưu kết quả tìm kiếm vào cache
        
#         Args:
#             platform (str): Tên nền tảng
#             query (str): Từ khóa tìm kiếm
#             data (list): Kết quả tìm kiếm
#         """
#         cache_path = self._get_cache_path(platform, query)
#         cache_data = {
#             "timestamp": time.time(),
#             "query": query,
#             "platform": platform,
#             "data": data
#         }
        
#         with open(cache_path, 'w', encoding='utf-8') as f:
#             json.dump(cache_data, f, ensure_ascii=False, indent=2)
        
#         self.logger.info(f"Đã lưu cache cho [{platform}] với từ khóa: {query}")
    
#     def _get_from_cache(self, platform, query):
#         """
#         Lấy kết quả tìm kiếm từ cache nếu còn hiệu lực
        
#         Args:
#             platform (str): Tên nền tảng
#             query (str): Từ khóa tìm kiếm
            
#         Returns:
#             list or None: Kết quả tìm kiếm từ cache hoặc None nếu không có hoặc hết hạn
#         """
#         cache_path = self._get_cache_path(platform, query)
        
#         if not os.path.exists(cache_path):
#             return None
        
#         try:
#             with open(cache_path, 'r', encoding='utf-8') as f:
#                 cache_data = json.load(f)
            
#             # Kiểm tra thời gian hết hạn
#             if time.time() - cache_data["timestamp"] > self.cache_expire_time:
#                 self.logger.info(f"Cache hết hạn cho [{platform}] với từ khóa: {query}")
#                 return None
            
#             self.logger.info(f"Đã lấy cache cho [{platform}] với từ khóa: {query}")
#             return cache_data["data"]
        
#         except Exception as e:
#             self.logger.error(f"Lỗi khi đọc cache: {str(e)}")
#             return None
    
#     def get_product_recommendations(self, classification_result, num_products=6, platforms=None, use_cache=True):
#         """
#         Lấy gợi ý sản phẩm từ các trang thương mại điện tử dựa trên kết quả phân loại
        
#         Args:
#             classification_result (dict): Kết quả phân loại từ API
#             num_products (int): Số sản phẩm cần gợi ý cho mỗi nền tảng
#             platforms (list): Danh sách các nền tảng cần tìm kiếm (shopee, lazada, tiki...)
#             use_cache (bool): Sử dụng cache hay không
            
#         Returns:
#             dict: Danh sách sản phẩm gợi ý từ các nền tảng
#         """
#         if not platforms:
#             platforms = ["shopee", "lazada", "tiki"]
        
#         if not classification_result.get("predictions"):
#             return {"error": "Không có kết quả phân loại"}
        
#         # Lấy top 2 categories có độ tin cậy cao nhất
#         top_categories = classification_result["predictions"][:2]
#         search_queries = [item["class_name"] for item in top_categories]
        
#         # Thêm từ khóa tiếng Việt nếu là các danh mục phổ biến
#         search_queries_vi = self._translate_popular_categories(search_queries)
#         search_queries.extend(search_queries_vi)
        
#         recommendations = {
#             "based_on": classification_result,
#             "recommendations": {},
#             "search_queries": search_queries
#         }
        
#         for platform in platforms:
#             recommendations["recommendations"][platform] = []
            
#             for query in search_queries:
#                 # Kiểm tra cache trước
#                 if use_cache:
#                     cached_results = self._get_from_cache(platform, query)
#                     if cached_results:
#                         # Lấy số lượng sản phẩm cần thiết từ cache
#                         platform_results = cached_results[:num_products // len(search_queries)]
#                         recommendations["recommendations"][platform].extend(platform_results)
#                         continue
                
#                 # Nếu không có cache hoặc không sử dụng cache, tìm kiếm trực tiếp
#                 platform_results = self._search_platform(platform, query, num_products // len(search_queries))
                
#                 # Lưu vào cache nếu có kết quả
#                 if platform_results and use_cache:
#                     self._save_to_cache(platform, query, platform_results)
                
#                 recommendations["recommendations"][platform].extend(platform_results)
        
#         # Thêm phân loại sản phẩm theo danh mục
#         recommendations["categories"] = self._categorize_recommendations(recommendations["recommendations"])
        
#         return recommendations
    
#     def _translate_popular_categories(self, categories):
#         """
#         Dịch các danh mục phổ biến sang tiếng Việt
        
#         Args:
#             categories (list): Danh sách các danh mục
            
#         Returns:
#             list: Danh sách các danh mục bằng tiếng Việt
#         """
#         # Dictionary ánh xạ từ danh mục tiếng Anh sang tiếng Việt
#         category_translations = {
#             "Laptop": "Máy tính xách tay",
#             "Cell Phone": "Điện thoại di động",
#             "Mobile Phone": "Điện thoại di động",
#             "Smartphone": "Điện thoại thông minh",
#             "Television": "Tivi",
#             "TV": "Tivi",
#             "Camera": "Máy ảnh",
#             "Headphone": "Tai nghe",
#             "Headphones": "Tai nghe",
#             "Watch": "Đồng hồ",
#             "Smart Watch": "Đồng hồ thông minh",
#             "Shoe": "Giày",
#             "Shoes": "Giày",
#             "Dress": "Váy",
#             "T-shirt": "Áo thun",
#             "Shirt": "Áo sơ mi",
#             "Bag": "Túi xách",
#             "Backpack": "Balo",
#             "Furniture": "Đồ nội thất",
#             "Sofa": "Ghế sofa",
#             "Table": "Bàn",
#             "Chair": "Ghế",
#             "Book": "Sách",
#             "Food": "Thực phẩm",
#             "Bicycle": "Xe đạp",
#             "Toy": "Đồ chơi",
#             "Makeup": "Mỹ phẩm",
#             "Cosmetics": "Mỹ phẩm",
#             "Jewelry": "Trang sức",
#             "Ring": "Nhẫn",
#             "Necklace": "Vòng cổ",
#             "Bracelet": "Vòng tay",
#             "Computer": "Máy tính",
#             "Keyboard": "Bàn phím",
#             "Mouse": "Chuột máy tính",
#             "Monitor": "Màn hình",
#             "Printer": "Máy in",
#             "Refrigerator": "Tủ lạnh",
#             "Washing Machine": "Máy giặt",
#             "Air Conditioner": "Máy điều hòa",
#             "Fan": "Quạt",
#             "Microwave": "Lò vi sóng",
#             "Oven": "Lò nướng",
#             "Blender": "Máy xay",
#             "Rice Cooker": "Nồi cơm điện",
#             "Guitar": "Đàn guitar",
#             "Piano": "Đàn piano",
#             "Violin": "Đàn violin",
#             "Drum": "Trống",
#             "Perfume": "Nước hoa",
#             "Sunglasses": "Kính mát",
#             "Glasses": "Kính",
#             "Hat": "Mũ",
#             "Cap": "Mũ lưỡi trai",
#             "Belt": "Thắt lưng",
#             "Wallet": "Ví",
#             "Umbrella": "Ô dù",
#             "Clock": "Đồng hồ treo tường",
#             "Lamp": "Đèn",
#             "Carpet": "Thảm",
#             "Curtain": "Rèm",
#             "Pillow": "Gối",
#             "Blanket": "Chăn",
#             "Towel": "Khăn tắm",
#             "Bottle": "Chai",
#             "Cup": "Cốc",
#             "Plate": "Đĩa",
#             "Bowl": "Bát",
#             "Spoon": "Thìa",
#             "Fork": "Nĩa",
#             "Knife": "Dao",
#             "Pot": "Nồi",
#             "Pan": "Chảo"
#         }
        
#         result = []
#         for category in categories:
#             # Tìm từ khóa phù hợp nhất
#             translated = None
#             for eng, vi in category_translations.items():
#                 if eng.lower() in category.lower():
#                     translated = vi
#                     break
            
#             if translated:
#                 result.append(translated)
        
#         # Thêm một số từ khóa phổ biến nếu có từ khóa chung chung
#         generic_keywords = ["đồ dùng", "sản phẩm", "hàng chính hãng"]
#         for category in categories:
#             for keyword in generic_keywords:
#                 result.append(f"{category} {keyword}")
        
#         return result
    
#     def _categorize_recommendations(self, platform_recommendations):
#         """
#         Phân loại sản phẩm gợi ý theo danh mục
        
#         Args:
#             platform_recommendations (dict): Sản phẩm gợi ý theo nền tảng
            
#         Returns:
#             dict: Sản phẩm gợi ý theo danh mục
#         """
#         categories = {}
        
#         # Danh sách các nền tảng
#         platforms = platform_recommendations.keys()
        
#         # Danh sách tất cả sản phẩm
#         all_products = []
#         for platform in platforms:
#             for product in platform_recommendations[platform]:
#                 # Thêm thông tin nền tảng vào sản phẩm
#                 product["source_platform"] = platform
#                 all_products.append(product)
        
#         # Phân loại theo giá
#         price_ranges = {
#             "Dưới 100K": lambda p: p < 100000,
#             "100K - 500K": lambda p: 100000 <= p < 500000,
#             "500K - 1 triệu": lambda p: 500000 <= p < 1000000,
#             "1 triệu - 5 triệu": lambda p: 1000000 <= p < 5000000,
#             "5 triệu - 10 triệu": lambda p: 5000000 <= p < 10000000,
#             "Trên 10 triệu": lambda p: p >= 10000000
#         }
        
#         categories["price_ranges"] = {}
#         for range_name, price_check in price_ranges.items():
#             categories["price_ranges"][range_name] = []
        
#         # Phân loại sản phẩm theo giá
#         for product in all_products:
#             # Lấy giá sản phẩm
#             price_str = product.get("price", "0đ")
            
#             # Chuyển đổi chuỗi giá thành số
#             try:
#                 # Xóa các ký tự không phải số
#                 price_num = ''.join(c for c in price_str if c.isdigit())
#                 price = int(price_num) if price_num else 0
                
#                 # Phân loại theo khoảng giá
#                 for range_name, price_check in price_ranges.items():
#                     if price_check(price):
#                         categories["price_ranges"][range_name].append(product)
#                         break
#             except Exception as e:
#                 self.logger.error(f"Lỗi khi phân loại giá sản phẩm: {str(e)}")
        
#         # Phân loại theo nền tảng và xếp hạng
#         categories["by_rating"] = {}
#         for platform in platforms:
#             # Sắp xếp sản phẩm theo xếp hạng giảm dần
#             sorted_products = sorted(
#                 platform_recommendations[platform],
#                 key=lambda p: p.get("rating", 0),
#                 reverse=True
#             )
#             categories["by_rating"][platform] = sorted_products
        
#         # Phân loại theo sản phẩm bán chạy
#         categories["best_selling"] = sorted(
#             all_products,
#             key=lambda p: p.get("sold", 0),
#             reverse=True
#         )[:10]  # Top 10 sản phẩm bán chạy
        
#         # Phân loại theo khuyến mãi (có giá gốc cao hơn giá hiện tại)
#         categories["on_sale"] = []
#         for product in all_products:
#             if product.get("original_price") and product.get("price"):
#                 # Nếu sản phẩm có giá gốc và khác giá hiện tại
#                 categories["on_sale"].append(product)
        
#         return categories
    
#     def _search_platform(self, platform, query, num_products):
#         """
#         Tìm kiếm sản phẩm trên một nền tảng cụ thể
        
#         Args:
#             platform (str): Tên nền tảng (shopee, lazada...)
#             query (str): Từ khóa tìm kiếm
#             num_products (int): Số sản phẩm cần trả về
            
#         Returns:
#             list: Danh sách sản phẩm tìm thấy
#         """
#         if platform.lower() == "shopee":
#             return self._search_shopee(query, num_products)
#         elif platform.lower() == "lazada":
#             return self._search_lazada(query, num_products)
#         elif platform.lower() == "tiki":
#             return self._search_tiki(query, num_products)
#         else:
#             self.logger.warning(f"Nền tảng {platform} không được hỗ trợ")
#             return []
    
#     def _search_shopee(self, query, num_products):
#         """
#         Tìm kiếm sản phẩm trên Shopee
        
#         Args:
#             query (str): Từ khóa tìm kiếm
#             num_products (int): Số sản phẩm cần trả về
            
#         Returns:
#             list: Danh sách sản phẩm từ Shopee
#         """
#         products = []
#         escaped_query = quote_plus(query)
        
#         try:
#             # URL tìm kiếm Shopee
#             url = f"https://shopee.vn/search?keyword={escaped_query}"
#             self.logger.info(f"Tìm kiếm trên Shopee với từ khóa: {query}")
            
#             # Sử dụng Shopee API
#             # Lưu ý: API URL của Shopee có thể thay đổi
#             api_url = f"https://shopee.vn/api/v4/search/search_items?by=relevancy&keyword={escaped_query}&limit={num_products}&newest=0&order=desc&page_type=search&scenario=PAGE_GLOBAL_SEARCH&version=2"
            
#             # Sử dụng headers để giả lập trình duyệt
#             headers = self.get_headers()
            
#             response = requests.get(api_url, headers=headers)
            
#             if response.status_code == 200:
#                 data = response.json()
                
#                 # Xử lý dữ liệu từ API
#                 if "items" in data and data["items"]:
#                     for item in data["items"][:num_products]:
#                         product_data = item.get("item_basic", {})
                        
#                         if product_data:
#                             # Định dạng URL hình ảnh Shopee
#                             image_id = product_data.get("image", "")
#                             shop_id = product_data.get("shopid", "")
#                             item_id = product_data.get("itemid", "")
                            
#                             image_url = f"https://cf.shopee.vn/file/{image_id}"
#                             product_url = f"https://shopee.vn/{product_data.get('name', '').replace(' ', '-')}-i.{shop_id}.{item_id}"
                            
#                             # Định dạng giá tiền
#                             price = product_data.get('price', 0) / 100000
#                             price_str = f"{price:,.0f}đ"
                            
#                             original_price = None
#                             if product_data.get('price_before_discount', 0) > 0:
#                                 original_price = product_data.get('price_before_discount', 0) / 100000
#                                 original_price_str = f"{original_price:,.0f}đ"
#                             else:
#                                 original_price_str = None
                            
#                             product = {
#                                 "platform": "Shopee",
#                                 "name": product_data.get("name", "Sản phẩm Shopee"),
#                                 "price": price_str,
#                                 "original_price": original_price_str,
#                                 "image_url": image_url,
#                                 "product_url": product_url,
#                                 "rating": product_data.get("item_rating", {}).get("rating_star", 0),
#                                 "sold": product_data.get("historical_sold", 0)
#                             }
#                             products.append(product)
            
#             # Nếu không có kết quả từ API, thử phương pháp khác
#             if not products:
#                 self.logger.info("Không có kết quả từ API Shopee, thử phương pháp thay thế")
                
#                 # Sử dụng phương pháp scraping HTML (giả lập)
#                 # Đây chỉ là dữ liệu mẫu vì scraping có thể bị chặn
#                 fallback_products = [
#                     {
#                         "platform": "Shopee",
#                         "name": f"{query} - Sản phẩm chất lượng cao",
#                         "price": "299.000đ",
#                         "original_price": "399.000đ",
#                         "image_url": "https://cf.shopee.vn/file/placeholder_image",
#                         "product_url": f"https://shopee.vn/search?keyword={escaped_query}",
#                         "rating": 4.8,
#                         "sold": 150
#                     },
#                     {
#                         "platform": "Shopee",
#                         "name": f"{query} - Hàng chính hãng",
#                         "price": "499.000đ",
#                         "original_price": "599.000đ",
#                         "image_url": "https://cf.shopee.vn/file/placeholder_image",
#                         "product_url": f"https://shopee.vn/search?keyword={escaped_query}",
#                         "rating": 4.7,
#                         "sold": 120
#                     }
#                 ]
                
#                 products = fallback_products[:num_products]
        
#         except Exception as e:
#             self.logger.error(f"Lỗi khi tìm kiếm trên Shopee: {str(e)}")
            
#             # Trả về dữ liệu mẫu trong trường hợp lỗi
#             products = [
#                 {
#                     "platform": "Shopee",
#                     "name": f"{query} - Sản phẩm A",
#                     "price": "199.000đ",
#                     "original_price": "250.000đ",
#                     "image_url": "https://cf.shopee.vn/file/placeholder_image",
#                     "product_url": f"https://shopee.vn/search?keyword={escaped_query}",
#                     "rating": 4.5,
#                     "sold": 100
#                 }
#             ]
        
#         return products
    
#     def _search_lazada(self, query, num_products):
#         """
#         Tìm kiếm sản phẩm trên Lazada
        
#         Args:
#             query (str): Từ khóa tìm kiếm
#             num_products (int): Số sản phẩm cần trả về
            
#         Returns:
#             list: Danh sách sản phẩm từ Lazada
#         """
#         products = []
#         escaped_query = quote_plus(query)
        
#         try:
#             url = f"https://www.lazada.vn/catalog/?q={escaped_query}"
#             self.logger.info(f"Tìm kiếm trên Lazada với từ khóa: {query}")
            
#             # Sử dụng headers để giả lập trình duyệt
#             headers = self.get_headers()
            
#             response = requests.get(url, headers=headers)
            
#             if response.status_code == 200:
#                 soup = BeautifulSoup(response.text, 'html.parser')
                
#                 # Lazada lưu dữ liệu sản phẩm trong thẻ script dạng JSON
#                 script_tag = soup.find('script', text=lambda t: t and 'window.pageData=' in t)
                
#                 if script_tag:
#                     # Trích xuất dữ liệu JSON
#                     json_text = script_tag.string.split('window.pageData=')[1].split('</script>')[0].strip()
#                     try:
#                         # Làm sạch dữ liệu JSON (xóa dấu chấm phẩy cuối, etc.)
#                         if json_text.endswith(';'):
#                             json_text = json_text[:-1]
                        
#                         data = json.loads(json_text)
                        
#                         # Trích xuất thông tin sản phẩm
#                         if 'mods' in data and 'listItems' in data['mods']:
#                             items = data['mods']['listItems']
                            
#                             for item in items[:num_products]:
#                                 # Lấy hình ảnh sản phẩm
#                                 image_url = item.get('image', '')
                                
#                                 # Định dạng URL sản phẩm
#                                 product_url = f"https://www.lazada.vn/products/{item.get('nid', '')}"
                                
#                                 product = {
#                                     "platform": "Lazada",
#                                     "name": item.get('name', 'Sản phẩm Lazada'),
#                                     "price": item.get('price', ''),
#                                     "original_price": item.get('originalPrice', '') if item.get('originalPrice') != item.get('price') else None,
#                                     "image_url": image_url,
#                                     "product_url": product_url,
#                                     "rating": item.get('ratingScore', 0),
#                                     "sold": item.get('sold', 0)
#                                 }
#                                 products.append(product)
#                     except json.JSONDecodeError as e:
#                         self.logger.error(f"Lỗi khi parse JSON từ Lazada: {str(e)}")
            
#             # Nếu không có kết quả, trả về dữ liệu mẫu
#             if not products:
#                 self.logger.info("Không có kết quả từ Lazada, sử dụng dữ liệu mẫu")
                
#                 fallback_products = [
#                     {
#                         "platform": "Lazada",
#                         "name": f"{query} - Sản phẩm cao cấp",
#                         "price": "349.000đ",
#                         "original_price": "499.000đ",
#                         "image_url": "https://lzd-img-global.slatic.net/placeholder_image",
#                         "product_url": f"https://www.lazada.vn/catalog/?q={escaped_query}",
#                         "rating": 4.6,
#                         "sold": 80
#                     },
#                     {
#                         "platform": "Lazada",
#                         "name": f"{query} - Hàng nhập khẩu",
#                         "price": "599.000đ",
#                         "original_price": "799.000đ",
#                         "image_url": "https://lzd-img-global.slatic.net/placeholder_image",
#                         "product_url": f"https://www.lazada.vn/catalog/?q={escaped_query}",
#                         "rating": 4.7,
#                         "sold": 65
#                     }
#                 ]
                
#                 products = fallback_products[:num_products]
        
#         except Exception as e:
#             self.logger.error(f"Lỗi khi tìm kiếm trên Lazada: {str(e)}")
            
#             # Trả về dữ liệu mẫu trong trường hợp lỗi
#             products = [
#                 {
#                     "platform": "Lazada",
#                     "name": f"{query} - Sản phẩm B",
#                     "price": "299.000đ",
#                     "original_price": "350.000đ",
#                     "image_url": "https://lzd-img-global.slatic.net/placeholder_image",
#                     "product_url": f"https://www.lazada.vn/catalog/?q={escaped_query}",
#                     "rating": 4.3,
#                     "sold": 75
#                 }
#             ]
        
#         return products
    
#     def _search_tiki(self, query, num_products):
#         """
#         Tìm kiếm sản phẩm trên Tiki
        
#         Args:
#             query (str): Từ khóa tìm kiếm
#             num_products (int): Số sản phẩm cần trả về
            
#         Returns:
#             list: Danh sách sản phẩm từ Tiki
#         """
#         products = []
#         escaped_query = quote_plus(query)
        
#         try:
#             # Sử dụng API của Tiki
#             api_url = f"https://tiki.vn/api/v2/products?limit={num_products}&q={escaped_query}"
#             self.logger.info(f"Tìm kiếm trên Tiki với từ khóa: {query}")
            
#             # Sử dụng headers để giả lập trình duyệt
#             headers = self.get_headers()
            
#             response = requests.get(api_url, headers=headers)
            
#             if response.status_code == 200:
#                 data = response.json()
                
#                 if 'data' in data:
#                     for item in data['data'][:num_products]:
#                         # Xử lý thông tin giá
#                         price = item.get('price', 0)
#                         price_str = f"{price:,.0f}đ"
                        
#                         original_price = item.get('original_price', 0)
#                         original_price_str = f"{original_price:,.0f}đ" if original_price > price else None
                        
#                         # Tạo đối tượng sản phẩm
#                         product = {
#                             "platform": "Tiki",
#                             "name": item.get('name', 'Sản phẩm Tiki'),
#                             "price": price_str,
#                             "original_price": original_price_str,
#                             "image_url": item.get('thumbnail_url', ''),
#                             "product_url": f"https://tiki.vn/{item.get('url_path', '')}",
#                             "rating": item.get('rating_average', 0),
#                             "sold": item.get('quantity_sold', {}).get('value', 0)
#                         }
#                         products.append(product)
            
#             # Nếu không có kết quả, trả về dữ liệu mẫu
#             if not products:
#                 self.logger.info("Không có kết quả từ Tiki, sử dụng dữ liệu mẫu")
                
#                 fallback_products = [
#                     {
#                         "platform": "Tiki",
#                         "name": f"{query} - Sản phẩm chính hãng",
#                         "price": "419.000đ",
#                         "original_price": "519.000đ",
#                         "image_url": "https://salt.tikicdn.com/cache/280x280/placeholder_image.jpg",
#                         "product_url": f"https://tiki.vn/search?q={escaped_query}",
#                         "rating": 4.8,
#                         "sold": 95
#                     },
#                     {
#                         "platform": "Tiki",
#                         "name": f"{query} - Giao nhanh 2h",
#                         "price": "559.000đ",
#                         "original_price": "659.000đ",
#                         "image_url": "https://salt.tikicdn.com/cache/280x280/placeholder_image.jpg",
#                         "product_url": f"https://tiki.vn/search?q={escaped_query}",
#                         "rating": 4.5,
#                         "sold": 70
#                     }
#                 ]
                
#                 products = fallback_products[:num_products]
        
#         except Exception as e:
#             self.logger.error(f"Lỗi khi tìm kiếm trên Tiki: {str(e)}")
            
#             products = [
#                 {
#                     "platform": "Tiki",
#                     "name": f"{query} - Sản phẩm C",
#                     "price": "359.000đ",
#                     "original_price": "399.000đ",
#                     "image_url": "https://salt.tikicdn.com/cache/280x280/placeholder_image.jpg",
#                     "product_url": f"https://tiki.vn/search?q={escaped_query}",
#                     "rating": 4.6,
#                     "sold": 85
#                 }
#             ]
        
#         return products