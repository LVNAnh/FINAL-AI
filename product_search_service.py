import requests
import logging
import json
import os
import re
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

class ProductSearchService:
    """Dịch vụ tìm kiếm sản phẩm thực từ các trang web thương mại điện tử"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9,vi;q=0.8"
        }
        self.timeout = 10
        
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
            shopee_products = self.search_shopee(query)
            if shopee_products:
                all_products.extend(shopee_products)
                self.logger.info(f"Tìm thấy {len(shopee_products)} sản phẩm từ Shopee")
        except Exception as e:
            self.logger.error(f"Lỗi khi tìm trên Shopee: {str(e)}")
        
        try:
            tiki_products = self.search_tiki(query)
            if tiki_products:
                all_products.extend(tiki_products)
                self.logger.info(f"Tìm thấy {len(tiki_products)} sản phẩm từ Tiki")
        except Exception as e:
            self.logger.error(f"Lỗi khi tìm trên Tiki: {str(e)}")
        
        try:
            lazada_products = self.search_lazada(query)
            if lazada_products:
                all_products.extend(lazada_products)
                self.logger.info(f"Tìm thấy {len(lazada_products)} sản phẩm từ Lazada")
        except Exception as e:
            self.logger.error(f"Lỗi khi tìm trên Lazada: {str(e)}")
            
        if not all_products:
            try:
                google_products = self.search_google_shopping(query)
                if google_products:
                    all_products.extend(google_products)
                    self.logger.info(f"Tìm thấy {len(google_products)} sản phẩm từ Google Shopping")
            except Exception as e:
                self.logger.error(f"Lỗi khi tìm trên Google Shopping: {str(e)}")
        
        return all_products[:max_results]
    
    def search_shopee(self, query, limit=3):
        """Tìm kiếm sản phẩm trên Shopee"""
        products = []
        
        try:
            search_url = f"https://shopee.vn/search?keyword={quote_plus(query)}"
            
            response = requests.get(search_url, headers=self.headers, timeout=self.timeout)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            product_items = soup.select('.shopee-search-item-result__item')
            
            for item in product_items[:limit]:
                try:
                    name_element = item.select_one('.shopee-item-card__text-name')
                    price_element = item.select_one('.shopee-item-card__current-price')
                    link_element = item.select_one('a[href]')
                    image_element = item.select_one('img._3vEAJn')
                    
                    if name_element and price_element and link_element:
                        name = name_element.text.strip()
                        price_text = price_element.text.strip()
                        
                        price_match = re.search(r'[\d.,]+', price_text)
                        price = price_match.group(0).replace('.', '') if price_match else "Liên hệ"
                        
                        link = link_element.get('href')
                        if link and not link.startswith('http'):
                            link = f"https://shopee.vn{link}"
                        
                        image_url = ""
                        if image_element:
                            image_url = image_element.get('src') or image_element.get('data-src', '')
                        
                        products.append({
                            'title': name,
                            'price': price,
                            'price_text': price_text,
                            'url': link,
                            'image_url': image_url,
                            'source': 'Shopee'
                        })
                except Exception as e:
                    self.logger.error(f"Lỗi khi xử lý sản phẩm Shopee: {str(e)}")
                    continue
                    
                if len(products) >= limit:
                    break
        except Exception as e:
            self.logger.error(f"Lỗi khi tìm kiếm trên Shopee: {str(e)}")
            
        return products
    
    def search_tiki(self, query, limit=3):
        """Tìm kiếm sản phẩm trên Tiki"""
        products = []
        
        try:
            search_url = f"https://tiki.vn/search?q={quote_plus(query)}"
            
            response = requests.get(search_url, headers=self.headers, timeout=self.timeout)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            product_items = soup.select('div[data-view-id="product_list_container"] > div')
            
            for item in product_items[:limit]:
                try:
                    name_element = item.select_one('div[class*="info"] > div[class*="name"]')
                    price_element = item.select_one('div[class*="price-discount__price"]')
                    link_element = item.select_one('a[href]')
                    image_element = item.select_one('img[src]')
                    
                    if name_element and price_element and link_element:
                        name = name_element.text.strip()
                        price_text = price_element.text.strip()
                        
                        price_match = re.search(r'[\d.,]+', price_text)
                        price = price_match.group(0).replace('.', '') if price_match else "Liên hệ"
                        
                        link = link_element.get('href')
                        if link and not link.startswith('http'):
                            link = f"https://tiki.vn{link}"
                            
                        image_url = ""
                        if image_element:
                            image_url = image_element.get('src', '')
                        
                        products.append({
                            'title': name,
                            'price': price,
                            'price_text': price_text,
                            'url': link,
                            'image_url': image_url,
                            'source': 'Tiki'
                        })
                except Exception as e:
                    self.logger.error(f"Lỗi khi xử lý sản phẩm Tiki: {str(e)}")
                    continue
                    
                if len(products) >= limit:
                    break
        except Exception as e:
            self.logger.error(f"Lỗi khi tìm kiếm trên Tiki: {str(e)}")
            
        return products
    
    def search_lazada(self, query, limit=3):
        """Tìm kiếm sản phẩm trên Lazada"""
        products = []
        
        try:
            search_url = f"https://www.lazada.vn/catalog/?q={quote_plus(query)}"
            
            response = requests.get(search_url, headers=self.headers, timeout=self.timeout)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            product_items = soup.select('.Bm3ON')
            
            for item in product_items[:limit]:
                try:
                    name_element = item.select_one('.RfADt')
                    price_element = item.select_one('.aBrP0')
                    link_element = item.select_one('a[href]')
                    image_element = item.select_one('img[src]')
                    
                    if name_element and price_element and link_element:
                        name = name_element.text.strip()
                        price_text = price_element.text.strip()
                        
                        link = link_element.get('href')
                        
                        image_url = ""
                        if image_element:
                            image_url = image_element.get('src', '')
                        
                        products.append({
                            'title': name,
                            'price': "Xem trên trang", 
                            'price_text': price_text,
                            'url': link,
                            'image_url': image_url,
                            'source': 'Lazada'
                        })
                except Exception as e:
                    self.logger.error(f"Lỗi khi xử lý sản phẩm Lazada: {str(e)}")
                    continue
                    
                if len(products) >= limit:
                    break
        except Exception as e:
            self.logger.error(f"Lỗi khi tìm kiếm trên Lazada: {str(e)}")
            
        return products
    
    def search_google_shopping(self, query, limit=3):
        """Tìm kiếm sản phẩm trên Google Shopping"""
        products = []
        
        try:
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
        
        if "espresso" in query.lower() or "coffee" in query.lower():
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
