# -*- coding: utf-8 -*-
import os
import time
import traceback
import random
import re
import json
import datetime
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException
import psycopg2
from configparser import ConfigParser
from scrapy.selector import Selector

base_dir = os.path.dirname(os.path.abspath(__file__))

class FooddataCrawler():

    # init
    def __init__(self):
        # read database config
        self.conn = self.connect_database()
        if self.conn is None:
            print("----- Can't connect to database. -----")
        else:
            print("--- Connected to database. ---")

        # Setting auto commit false
        self.conn.autocommit = True

        # declare self website list
        self.website_list = list()

        # read browseable websites
        self.load_websites()
        print(self.website_list)

        # declare upc variables
        self.link_set = list()

        # declare upc list
        self.upc_set = dict()

        # read proxy list
        self.get_proxy_list()

        # init web driver
        self.driver = None

    # get database config
    def database_config(self):
        # create a parser
        parser = ConfigParser()
        # read config file
        parser.read("{}/config.ini".format(base_dir))

        # get section, default to postgresql
        db = {}
        if parser.has_section("postgresql"):
            params = parser.items("postgresql")
            for param in params:
                db[param[0]] = param[1]
        else:
            raise Exception('Section {0} not found in the {1} file'.format("postgresql", "config.ini"))

        return db

    # connect "food_data" database
    def connect_database(self):
        """ Connect to the PostgreSQL database server """
        conn = None
        try:
            # read connection parameters
            params = self.database_config()

            # connect to the PostgreSQL server
            conn = psycopg2.connect(**params)

            return conn
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
            return conn

    # load websites
    def load_websites(self):
        try:
            cursor = self.conn.cursor()
            select_Query = "select * from websites"

            cursor.execute(select_Query)
            websites_records = cursor.fetchall()

            for row in websites_records:
                if row[2] and row[13] == "B" and row[4] == "No":
                    if 'Target' in row[1]:
                        self.website_list.append(row)

            # close communication with the PostgreSQL database server
            cursor.close()
        except:
            print(traceback.print_exc())

    # get proxy list
    def get_proxy_list(self):
        path = base_dir + "/proxies.txt"
        with open(path, 'r') as file_object:
            self.proxy_list = [row.rstrip('\n') for row in file_object]

    # get random proxy
    def get_random_proxy(self):
        random_idx = random.randint(1, len(self.proxy_list) - 1)
        proxy_ip = self.proxy_list[random_idx]
        print('----- selected proxy :', proxy_ip)
        return proxy_ip

    # create driver
    def set_driver(self):
        while True:
            try:
                random_proxy_ip = self.get_random_proxy()
                webdriver.DesiredCapabilities.CHROME['proxy'] = {
                    "httpProxy":random_proxy_ip,
                    "ftpProxy":random_proxy_ip,
                    "sslProxy":random_proxy_ip,
                    "proxyType":"MANUAL",
                }
                chrome_option = webdriver.ChromeOptions()
                chrome_option.add_argument('--no-sandbox')
                chrome_option.add_argument('--disable-dev-shm-usage')
                chrome_option.add_argument('--ignore-certificate-errors')
                chrome_option.add_argument("--disable-blink-features=AutomationControlled")
                chrome_option.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) ' \
                    'Chrome/80.0.3987.132 Safari/537.36')
                chrome_option.headless = True

                driver = webdriver.Chrome(options = chrome_option)
                # driver = webdriver.Chrome('/usr/local/bin/chromedriver', options = chrome_option)
                return driver
            except:
                continue

    # scroll down
    def scroll_down(self):
        try:
            scroll_flag = False
            # page height before scroll down
            before_height = self.driver.execute_script("return document.body.scrollHeight")

            # scroll down to the bottom.
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(10)

            # page height after scroll down
            after_height = self.driver.execute_script("return document.body.scrollHeight")

            if after_height > before_height:
                before_height = after_height
                scroll_flag = True
                print('----- Scroll Down -----')

            return scroll_flag
        except:
            return False

    # click pagination btn
    def click_pagination(self, event_pattern):
        try:
            before_url = self.driver.current_url
            pagination_btn_element = self.driver.find_element_by_xpath(event_pattern)

            pagination_valid_flag = True

            if pagination_btn_element is None:
                pagination_valid_flag = False

            if pagination_valid_flag and not pagination_btn_element.is_enabled():
                pagination_valid_flag = False

            if pagination_valid_flag and pagination_btn_element.get_attribute("disabled"):
                pagination_valid_flag = False

            if pagination_valid_flag and pagination_btn_element.get_attribute("class") and "disabled" in pagination_btn_element.get_attribute("class"):
                pagination_valid_flag = False

            if pagination_valid_flag:

                if pagination_btn_element.get_attribute('href'):
                    print("----- Get Pagination URL -----")
                    print('----- Next URL : ', pagination_btn_element.get_attribute('href'))
                    self.driver.get(pagination_btn_element.get_attribute('href'))
                    return True

                else:
                    pagination_btn_element.click()
                    after_url = self.driver.current_url

                    if before_url == after_url or before_url+"#" == after_url:
                        return False

                    print("----- Clicked Pagination Button -----")
                    print('----- Next URL : ', after_url)
                    return True

            return False
        except NoSuchElementException as err:
            print("??? Can not find page next button. ???")

        except:
            print(traceback.print_exc())
            return False

    # get product UPC
    def get_upc(self, res_content):
        res_content = re.sub(r'\s+', ' ', res_content)
        res_content = re.sub(r'\&colon\;', ':', res_content)
        res_content = re.sub(r'\&dollar\;', '$', res_content)
        res_content = re.sub(r'\&minus\;', '-', res_content)
        res_content = re.sub(r'\&\#39\;', '\'', res_content)
        res_content = re.sub(r'\%20', ' ', res_content)
        res_content = re.sub(r'\%3E', '>', res_content)
        res_content = re.sub(r'\%3C', '<', res_content)
        res_content = re.sub(r'\%2F', '/', res_content)
        res_content = re.sub(r'&nbsp;', ' ', res_content)
        res_content = re.sub(r'&quot;', '"', res_content)


        upc_pattern = re.compile(r'[\W]([\d\-]{10}[\d\-]*)[\W]')
        valid_upc_pattern = re.compile(r'[\W]upc[\W]|[\W]barcode[\W]|[\W]gtin\d+[\W]|[\W]vSKU[\W]', re.I)
        for matched_upc in upc_pattern.finditer(res_content):
            try:
                # case Html
                substring = res_content[ matched_upc.start() - 100 : matched_upc.end()]
                # case Js
                if not any( item in substring for item in ['<', '>']):
                    substring = res_content[matched_upc.start() - 30: matched_upc.end()]

                if valid_upc_pattern.search(substring):
                    upc = matched_upc.groups()[0]
                    upc = re.sub('\-', '', upc)
                    if 10 <= len(upc) <= 14:
                        return str(upc)
            except:
                print(traceback.print_exc())
                continue

        return None

    # get upc attrs from api
    def get_upc_attr_from_api(self, upc):
        try:
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'user_key': 'd9dcf2c74909ecc5ee435f8a3acd4260',
                'key_type': '3scale'
            }
            resp = requests.get('https://api.upcitemdb.com/prod/v1/lookup?upc={}'.format(upc), headers=headers)
            response_dict = json.loads(resp.text)
            if "code" in response_dict and response_dict["code"] == "OK":
                return response_dict["items"][0]
            else:
                return None
        except:
            return None

    # get upc attr from request
    def get_upc_attr_from_request(self, upc):
        try:
            upc_url = "https://www.upcitemdb.com/upc/{}".format(upc)
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
            response = requests.get(upc_url, verify=False)

            # check upc is valid
            if "was incorrect or invalid" not in response.text:

                body = Selector(text=re.sub(r'\s+', ' ', response.text))

                product_dict = {
                    'UPC': upc,
                    'category': None,
                    'brand': None,
                    'size': None,
                    'dimension': None,
                    'description': None,
                }

                for tr_ele in body.xpath('//*[@id="info"]/table//tr'):
                    try:
                        tr_text_list = tr_ele.xpath('.//text()').extract()
                        key = re.sub('\s', '', tr_text_list[0].strip()).lower()
                        value = tr_text_list[1].strip()
                        if 'brand' in key:
                            product_dict['brand'] = value
                        elif "size" in key:
                            product_dict['size'] = value
                        elif "dimension" in key:
                            product_dict['dimension'] = value
                    except:
                        continue

                category_ele = body.xpath('//ol[@class="category breadcrumb"]/li[@class="breadcrumb-item active"]')
                if category_ele:
                    product_dict['category'] = category_ele.xpath('.//text()').extract_first()
                    if '>' in product_dict['category']:
                        product_dict['category'] = product_dict['category'].split('>')[-1].strip()

                for small_ele in body.xpath('//small'):
                    try:
                        small_ele_text = small_ele.xpath('.//text()').extract_first()
                        if "ingredients" in small_ele_text.lower():
                            product_dict['description'] = small_ele_text
                    except:
                        continue

                return product_dict

            else:
                return None
        except:
            print(traceback.print_exc())
            return None

    # get product name
    def get_product_name(self):
        product_name_pattern_list = [
            { 'xpath' : '//h1[@itemprop="name"]', 'key': 'name', 'type': 'itemprop'},
            { 'xpath' : '//h1', 'key' : 'productname', 'type' : 'id'},
            { 'xpath' : '//h1', 'key' : 'product_name', 'type' : 'class'},
            { 'xpath' : '//div', 'key' : 'product_name', 'type' : 'class'},
            { 'xpath' : '//h2', 'key': 'product-title', 'type': 'class'},
            { 'xpath' : '//div', 'key': 'product_name', 'type': 'class'},
            { 'xpath' : '//h1', 'key': 'page,title', 'type': 'class'},
            { 'xpath' : '//h1', 'key': 'title', 'type': 'id'},
            { 'xpath' : '//h1', 'key': 'title', 'type': 'class'},
            { 'xpath' : '//div', 'key': 'title', 'type': 'class'},
            { 'xpath' : '//*[@itemprop="name"]', 'key': 'name', 'type': 'itemprop'},
        ]

        for pattern in product_name_pattern_list:
            try:
                title_elements = self.driver.find_elements_by_xpath(pattern['xpath'])
                for title_element in title_elements:
                    try:
                        if title_element.get_attribute(pattern['type']) and all(key in title_element.get_attribute(pattern['type']).lower() for key in pattern['key'].split(',')):
                            product_name = re.sub('\s+', ' ', title_element.text).strip()
                            if product_name:
                                return product_name
                    except:
                        continue
            except:
                continue
        return None

    # get product description
    def get_product_description(self):
        product_description_pattern_list = [
            { 'xpath': '//h3[contains(text(),"Description")]/following-sibling::div', 'key': 'default', 'type': 'class'},
            { 'xpath' : '//*[@itemprop="description"]', 'key' : 'description', 'type' : 'itemprop' },
            { 'xpath' : '//article', 'key' : 'product_description,product-description', 'type' : 'class'},
            { 'xpath' : '//ul', 'key' : 'prod-details,desc_prod', 'type' : 'class'},
            { 'xpath' : '//div', 'key' : 'productDetails', 'type' : 'id'},
            { 'xpath' : '//div', 'key' : 'prd-block_description,product-description,product-details,ProductDescriptionContainer,ab-store-single-product-header,product__description', 'type' : 'class'},
        ]

        for pattern in product_description_pattern_list:
            try:
                desc_elements = self.driver.find_elements_by_xpath(pattern['xpath'])
                for desc_element in desc_elements:
                    try:
                        if desc_element.get_attribute(pattern['type']) and any( key in desc_element.get_attribute(pattern['type']).lower() for key in pattern['key'].split(',')):
                            product_desc = re.sub('\s+', ' ', desc_element.get_attribute('textContent')).strip()
                            if product_desc:
                                return product_desc
                    except:
                        print(traceback.print_exc())
                        continue
            except:
                print(traceback.print_exc())
                continue

        return None

    # get product category
    def get_product_category(self):
        product_category_pattern_list = [
            {'xpath': '//*[@data-set="breadcrumb"]', 'key': 'breadcrumb', 'type': 'data-set'},
            {'xpath': '//*[@data-test="breadcrumb"]', 'key': 'breadcrumb', 'type': 'data-test'},
            {'xpath': '//ol', 'key': 'breadcrumbs', 'type': 'class'},
            {'xpath': '//ol', 'key': 'BreadcrumbList', 'type': 'typeof'},
        ]

        for pattern in product_category_pattern_list:
            cat_elements = self.driver.find_elements_by_xpath(pattern['xpath'])
            for cat_element in cat_elements:
                try:
                    has_property_flag = False
                    if pattern['key']:
                        if cat_element.get_attribute(pattern['type']) and any(key in cat_element.get_attribute(pattern['type']).lower() for key in pattern['key'].split(',')):
                            has_property_flag = True
                    else:
                        if cat_element.find_element_by_xpath(pattern['type']):
                            has_property_flag = True

                    if has_property_flag:
                        product_category = re.sub('\s+', ' ', cat_element.text).strip()
                        if product_category:
                            if '/' in product_category:
                                return product_category.rsplit('/', 1)[1].strip()
                            else:
                                return product_category.strip()
                except:
                    print(traceback.print_exc())
                    continue
        return None

    # get product brand
    def get_product_brand(self, res_content):
        try:
            res_content = re.sub(r'\s+', ' ', res_content)
            res_content = re.sub(r'\&colon\;', ':', res_content)
            res_content = re.sub(r'\&dollar\;', '$', res_content)
            res_content = re.sub(r'\&minus\;', '-', res_content)
            res_content = re.sub(r'\&\#39\;', '\'', res_content)
            res_content = re.sub(r'\%20', ' ', res_content)
            res_content = re.sub(r'\%3E', '>', res_content)
            res_content = re.sub(r'\%3C', '<', res_content)
            res_content = re.sub(r'\%2F', '/', res_content)
            res_content = re.sub(r'&nbsp;', ' ', res_content)
            res_content = re.sub(r'&quot;', '"', res_content)

            product_brand_pattern_list = [
                re.compile(r'itemprop\=[\"\']brand[\"\']\scontent\=([\"\'])', re.IGNORECASE),
                re.compile(r'[\"\']brand[\"\']\s*\:\s*([\"\'])', re.IGNORECASE),
            ]

            for pattern in product_brand_pattern_list:
                for item in pattern.finditer(res_content):
                    try:
                        brand_string = res_content[item.end(): item.end() + 50]
                        if item.groups()[0]:
                            brand = brand_string.split(item.groups()[0], 1)[0]
                        else:
                            brand = brand_string.split(',', 1)[0]
                        if brand:
                            return brand
                    except:
                        print(traceback.print_exc())
        except:
            print(traceback.print_exc())

        return None

    # get product price
    def get_product_price(self):
        product_price_pattern_list = [
            {'xpath': '//div[contains(@class,"product-detail__price")]/b', 'key': '', 'type': ''},
            {'xpath': '//div[@data-test="product-price"]', 'key': '', 'type': ''},
            {'xpath': '//*[@itemprop="price"]', 'key': 'price', 'type': 'itemprop'},
            {'xpath': '//*[@id="ProductPrice"]', 'key': 'product,price', 'type': 'id'},
            {'xpath': '//h2', 'key': 'product,price', 'type': 'id'},
            {'xpath': '//*[@id="product-price"]//div', 'key': 'price', 'type': 'id'},
            {'xpath': '//span', 'key': 'reducing,price', 'type': 'aria-label'},
            {'xpath': '//span', 'key': 'origin,price', 'type': 'aria-label'},
            {'xpath': '//span', 'key': '', 'type': 'data-product-price'},
            {'xpath': '//span', 'key': 'prd,price', 'type': 'class'},
            {'xpath': '//span', 'key': 'product,price', 'type': 'class'},
            {'xpath': '//span', 'key': 'current,price', 'type': 'class'},
            {'xpath': '//span', 'key': 'product,pricing', 'type': 'class'},
            {'xpath': '//div', 'key': 'product,price', 'type': 'class'},
            {'xpath': '//h2', 'key': 'product,price', 'type': 'class'},
            {'xpath': '//span', 'key': 'item,price', 'type': 'class'},
            {'xpath': '//span', 'key': 'price', 'type': 'class'},
            {'xpath': '//p', 'key': 'money', 'type': 'class'},
        ]

        for pattern in product_price_pattern_list:
            price_elements = self.driver.find_elements_by_xpath(pattern['xpath'])
            for price_element in price_elements:
                try:
                    has_property_flag = False
                    if pattern['key']:
                        if price_element.get_attribute(pattern['type']) and all(
                                key in price_element.get_attribute(pattern['type']).lower() for
                                key in pattern['key'].split(',')):
                            has_property_flag = True
                    elif pattern["type"]:
                        if price_element.get_attribute(pattern['type']):
                            has_property_flag = True
                    else:
                        has_property_flag = True

                    if has_property_flag:
                        product_price = re.sub('\s+', ' ', price_element.text).strip()
                        if product_price and re.search(r'\$\s*\d+\.\d+|\$\s*\d+', product_price):
                            return float(re.sub(r'\$', '', re.search(r'\$\s*\d+\.\d+|\$\s*\d+', product_price).group()))
                except:
                    continue

        return None

    # get product price
    def get_product_img_url(self):
        product_img_pattern_list = [
            { 'xpath' : '//img', 'key' : 'product,image', 'type' : 'id'},
            { 'xpath' : '//img', 'key' : 'main,image', 'type' : 'id'},
            { 'xpath' : '//img', 'key' : 'featured,Photo', 'type' : 'id'},
            { 'xpath' : '//div[@class="ProductThumbImage"]//img', 'key': 'image', 'type': 'itemprop'},
            { 'xpath' : '//img', 'key' : 'product,image', 'type' : 'class'},
            { 'xpath' : '//img', 'key' : 'product,detail', 'type' : 'class'},
            { 'xpath' : '//img', 'key' : 'dynamic,price', 'type' : 'class'},
            { 'xpath' : '//img', 'key' : 'product,media', 'type' : 'class'},
            { 'xpath' : '//img', 'key' : 'product,img', 'type' : 'class'},
            { 'xpath' : '//img', 'key': 'zoom,Img', 'type': 'class'},
            { 'xpath' : '//img', 'key': 'product,zoom', 'type': 'class'},
            { 'xpath' : '//img', 'key': 'zoomImage', 'type': 'data-cloudzoom'},
            { 'xpath' : '//img', 'key': '', 'type': 'data-zoom-image'},
            { 'xpath' : '//img', 'key': '', 'type': 'data-zoom'},
            { 'xpath' : '//img', 'key': 'featured,image', 'type': 'class'},
            { 'xpath' : '//img', 'key': 'zoom', 'type': 'class'},
            { 'xpath' : '//img', 'key': 'normal', 'type': 'class'},
            { 'xpath' : '//img', 'key': '', 'type': 'srcset'},
        ]

        product_img_except_pattern_list = ['logo', 'brand']

        for pattern in product_img_pattern_list:
            try:
                img_elements = self.driver.find_elements_by_xpath(pattern['xpath'])
                for img_element in img_elements:
                    try:
                        if img_element.get_attribute(pattern['type']) and all( key in img_element.get_attribute(pattern['type']).lower() for key in pattern['key'].split(',')):
                            product_img = img_element.get_attribute("src") if img_element.get_attribute("src") else img_element.get_attribute("data-src")
                            if product_img and not any(item in product_img for item in product_img_except_pattern_list):
                                product_img_string = re.sub('\s+', ' ', product_img).strip()
                                if product_img_string:
                                    return product_img_string.strip()
                    except:
                        continue
            except:
                continue

        return None

    # get product data
    def get_product_data(self, product_url_list):
        # iterate all products
        for index, product_url in enumerate(product_url_list):
            try:
                print("----- {}th / {} Current Product Url : {}".format(str(index + 1), str(len(product_url_list)), product_url))
                # create web driver
                self.driver = self.set_driver()
                self.driver.get(product_url)

                # get page source
                page_source = WebDriverWait(self.driver, 30).until(lambda driver: driver.find_element_by_tag_name("html").get_attribute("innerHTML").strip())

                # get upc
                upc_code = self.get_upc(page_source)

                # Creating a cursor object using the cursor() method
                cursor = self.conn.cursor()

                upc_attrs = None

                if upc_code:
                    print('----- {} -----'.format(upc_code))
                    if upc_code in self.upc_set:
                        upc_attrs = self.upc_set[upc_code]
                    else:
                        upc_attrs = self.get_upc_attr_from_api(upc_code)

                        if not upc_attrs:
                            upc_attrs = self.get_upc_attr_from_request(upc_code)

                        self.upc_set[upc_code] = upc_attrs
                    print('---------- Found UPC Attrs------------')
                    print(upc_attrs)
                    print('----------------------')

                final_dict = dict()
                final_dict['Website_Name'] = self.website_row[1]
                final_dict['Website_homepage'] = self.website_row[2]
                final_dict['Product_URL'] = product_url
                final_dict['Product_Name'] = None
                final_dict['Product_Description'] = None
                final_dict['Product_Category'] = None
                final_dict['Product_Brand'] = None
                final_dict['UPC'] = upc_code
                final_dict['upc_Category'] = None
                final_dict['upc_Brand'] = None
                final_dict['upc_Size'] = None
                final_dict['upc_Dimension'] = None
                final_dict['upc_Ingredients'] = None
                final_dict['last_price'] = None
                final_dict['current_price'] = None
                final_dict['percent_from_last_price'] = None
                final_dict['date_pricechange'] = None
                final_dict['date_created'] = None
                final_dict['date_modified'] = None
                final_dict['img_url'] = None

                # get product name
                final_dict['Product_Name'] = self.get_product_name()

                # get product description
                final_dict['Product_Description'] = self.get_product_description()

                # get product category
                final_dict['Product_Category'] = self.get_product_category()

                # get product category
                final_dict['Product_Brand'] = self.get_product_brand(page_source)

                # get product price
                final_dict['current_price'] = self.get_product_price()

                # get product img url
                if "images" in upc_attrs and upc_attrs["images"]:
                    final_dict['img_url'] = upc_attrs["images"][0]
                else:
                    final_dict['img_url'] = self.get_product_img_url()

                if not upc_attrs:
                    final_dict['UPC'] = None
                    upc_code = None

                # get upc category
                if upc_attrs and "category" in upc_attrs:
                    if upc_attrs["category"] and ">" in upc_attrs["category"]:
                        final_dict['upc_Category'] = upc_attrs["category"].rsplit('>', 1)[1].strip()
                    else:
                        final_dict["upc_Category"] = upc_attrs["category"]

                # get upc brand
                if upc_attrs and "brand" in upc_attrs:
                    final_dict['upc_Brand'] = upc_attrs["brand"]

                # get upc size
                if upc_attrs and "size" in upc_attrs:
                    final_dict['upc_Size'] = upc_attrs["size"]

                # get upc dimension
                if upc_attrs and "dimension" in upc_attrs:
                    final_dict['upc_Dimension'] = upc_attrs["dimension"]

                # get upc ingredients
                if upc_attrs and "description" in upc_attrs:
                    final_dict['upc_Ingredients'] = upc_attrs["description"]

                # quit web driver
                self.driver.quit()

                # product valid flag
                if upc_code and final_dict['current_price']:
                    product_flag = True
                elif final_dict['Product_Name'] and final_dict['current_price']:
                    product_flag = True
                else:
                    product_flag = False

                if product_flag:

                    # if upc of product exist
                    if upc_code:
                        cursor.execute("SELECT * FROM catalogues WHERE UPC = %s and sitename = %s and producturl = %s",
                                       (final_dict['UPC'], final_dict['Website_Name'], final_dict['Product_URL']))
                    else:
                        cursor.execute(
                            "SELECT * FROM catalogues WHERE productname = %s and sitename = %s and producturl = %s",
                            (final_dict['Product_Name'], final_dict['Website_Name'], final_dict['Product_URL']))
                    exist_row = cursor.fetchone()

                    if exist_row:
                        print("----------- existing row. unique_id : %s ------------" % format(exist_row[0]))

                        row_updated_flag = False
                        # update product description
                        if final_dict['Product_Description']:
                            sql_update_query = """Update catalogues set productdescription = %s where uid = %s"""
                            cursor.execute(sql_update_query, (final_dict['Product_Description'], exist_row[0]))
                            row_updated_flag = True

                        # update product category
                        if final_dict['Product_Category']:
                            sql_update_query = """Update catalogues set productcategory = %s where uid = %s"""
                            cursor.execute(sql_update_query, (final_dict['Product_Category'], exist_row[0]))
                            row_updated_flag = True

                        # update product brand
                        if final_dict['Product_Brand']:
                            sql_update_query = """Update catalogues set productbrand = %s where uid = %s"""
                            cursor.execute(sql_update_query, (final_dict['Product_Brand'], exist_row[0]))
                            row_updated_flag = True

                        # update upc category
                        if final_dict['upc_Category']:
                            sql_update_query = """Update catalogues set upccategory = %s where uid = %s"""
                            cursor.execute(sql_update_query, (final_dict['upc_Category'], exist_row[0]))
                            row_updated_flag = True

                        # update upc brand
                        if final_dict['upc_Brand']:
                            sql_update_query = """Update catalogues set upcbrand = %s where uid = %s"""
                            cursor.execute(sql_update_query, (final_dict['upc_Brand'], exist_row[0]))
                            row_updated_flag = True

                        # update upc size
                        if final_dict['upc_Size']:
                            sql_update_query = """Update catalogues set upcsize = %s where uid = %s"""
                            cursor.execute(sql_update_query, (final_dict['upc_Size'], exist_row[0]))
                            row_updated_flag = True

                        # update upc dimension
                        if final_dict['upc_Dimension']:
                            sql_update_query = """Update catalogues set upcdimension = %s where uid = %s"""
                            cursor.execute(sql_update_query, (final_dict['upc_Dimension'], exist_row[0]))
                            row_updated_flag = True

                        # update upc ingredients
                        if final_dict['upc_Ingredients']:
                            sql_update_query = """Update catalogues set upcingredients = %s where uid = %s"""
                            cursor.execute(sql_update_query, (final_dict['upc_Ingredients'], exist_row[0]))
                            row_updated_flag = True

                        # update Image_url
                        if final_dict['img_url']:
                            sql_update_query = """Update catalogues set productimage = %s where uid = %s"""
                            cursor.execute(sql_update_query, (final_dict['img_url'], exist_row[0]))
                            row_updated_flag = True

                        # compare price
                        if exist_row[17] != final_dict['current_price']:
                            if exist_row[17]:
                                final_dict["percent_from_last_price"] = round(((float(final_dict['current_price']) - float(exist_row[17])) / float(exist_row[17])) * 100, 2)

                            sql_update_query = """Update catalogues set lastprice = %s, currentprice = %s, percentfromlastprice = %s, datepricechange = %s where uid = %s"""
                            cursor.execute(sql_update_query, (
                            exist_row[17], final_dict['current_price'], final_dict["percent_from_last_price"],
                            str(datetime.datetime.today()), exist_row[0]))
                            row_updated_flag = True

                        # update modifieddate
                        if row_updated_flag:
                            sql_update_query = """Update catalogues set modifieddate = %s where uid = %s"""
                            cursor.execute(sql_update_query, (str(datetime.datetime.today()), exist_row[0]))

                    else:
                        print('---------------------------- Found New Product ----------------------------')
                        print(final_dict)
                        print('--------------------------------------------------------')

                        today_date = str(datetime.datetime.today())
                        # Preparing SQL queries to INSERT a record into the database.
                        insert_query = """ INSERT INTO catalogues (sitename, sitehomepage, producturl, productname, productdescription, productcategory, productbrand, upc, upccategory, upcbrand, upcsize, upcdimension, upcingredients, lastprice, currentprice, percentfromlastprice, datecreated, modifieddate, productimage) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
                        record_to_insert = (
                            final_dict['Website_Name'], final_dict['Website_homepage'], final_dict['Product_URL'],
                            final_dict['Product_Name'], final_dict['Product_Description'],
                            final_dict["Product_Category"], final_dict["Product_Brand"], final_dict['UPC'],
                            final_dict['upc_Category'],
                            final_dict['upc_Brand'], final_dict['upc_Size'], final_dict['upc_Dimension'],
                            final_dict['upc_Ingredients'], final_dict['last_price'], final_dict['current_price'],
                            final_dict['percent_from_last_price'], today_date, today_date, final_dict['img_url'])
                        cursor.execute(insert_query, record_to_insert)

                else:
                    return

                # close cursor object
                cursor.close()

            except:
                print("---------- Getting Data Failed. ----------")
                print(traceback.print_exc())
                continue
            finally:
                if self.driver is not None:
                    self.driver.quit()

    # main function
    def start(self):
        try:
            # iterate websites
            for website_row in self.website_list:
                try:
                    self.website_row = website_row

                    # product URLs list
                    product_url_list = list()

                    inventory_urls_list = website_row[14].split(',,')

                    for inventory_uri in inventory_urls_list:
                        try:
                            # make inventory url
                            if "http" in inventory_uri:
                                inventory_url = inventory_uri
                            else:
                                inventory_url = "https://{}{}".format(make_domain(website_row[2]), inventory_uri)
                            print('inventory URL : ', inventory_url)

                            # create web driver
                            self.driver = self.set_driver()

                            # get inventory url
                            self.driver.get(inventory_url)

                            pagination_flag = True
                            while pagination_flag:
                                try:
                                    WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.XPATH, website_row[15].split(',,')[0])))
                                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                                    time.sleep(5)

                                    # get product urls
                                    for product_xpath in website_row[15].split(',,'):
                                        try:
                                            product_urls = self.driver.find_elements_by_xpath(product_xpath)
                                            for product_url in product_urls:
                                                if product_url.get_attribute("href") and product_url.get_attribute("href") not in product_url_list:
                                                    product_url_list.append(product_url.get_attribute("href"))
                                        except:
                                            continue
                                    print("----- Found {} Product URLs -----".format(len(product_url_list)))

                                    # pagination event
                                    if website_row[16]:
                                        for event in website_row[16].split(',,'):
                                            if event == "scroll_down":
                                                pagination_flag = self.scroll_down()
                                            else:
                                                pagination_flag = self.click_pagination(event)
                                    else:
                                        pagination_flag = False
                                except:
                                    print(traceback.print_exc())
                                    break

                            # quit web dirver
                            self.driver.quit()

                        except:
                            print(traceback.print_exc())
                            continue
                        finally:
                            if self.driver is not None:
                                self.driver.quit()

                            print('----- Total Product URL Count : {} -----'.format(len(product_url_list)))

                    # get product data
                    self.get_product_data(product_url_list)

                except:
                    print(traceback.print_exc())
                    continue

        except:
            print("---------- Error : The file does not found ----------")
            print(traceback.print_exc())

# Get Domain From URL
def make_domain(url):
    try:
        if "http" in url:
            url = url.split("//", 1)[1].split("/", 1)[0].split('?', 1)[0]
        if "www" in url:
            url = url[4:]
        return url.lower()
    except:
        print('Error in Make Domain Function!')

# Get Full URL (e.g. www.firststopautova.com -> http://www.firststopautova.com)
def make_url(url):
    try:
        if not 'http' in url:
            url = 'http://' + url
        return url.lower()
    except Exception as e:
        print(traceback.print_exc())
        return ''

if __name__ == "__main__":

    fooddata_crawler = FooddataCrawler()
    fooddata_crawler.start()
    
