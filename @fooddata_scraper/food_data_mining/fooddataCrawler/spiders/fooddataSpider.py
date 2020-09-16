import os
import re
import time
import datetime
import requests
import json
import psycopg2
import traceback
from scrapy import signals
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.selector import Selector
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from configparser import ConfigParser

base_dir = os.path.dirname(os.path.abspath(__file__))

class MySpider(CrawlSpider):

    name = 'fooddataCrawler'

    def __init__(self, *args, **kwargs):
        
        super(MySpider, self).__init__(*args, **kwargs)

        # read database config
        self.conn = self.connect_database()
        if self.conn is None:
            print("----- Can't connect to database. -----")
            return
        else:
            print("--- Connected to database. ---")

        # Setting auto commit false
        self.conn.autocommit = True

        # /* load websites */
        # declare spider necessary variables
        self.allowed_domains = list()
        self.start_urls = list()

        # declare self website variables
        self.company_list = list()
        self.website_list = list()
        self.site_catagory_list = list()
        self.category_lookup_list = list()
        self.detail_lookup_list = list()
        self.sign_up_deal_list = list()
        self.sign_up_deal_ifYes_list = list()
        self.shipping_cost_list = list()
        self.isshopify_list = list()
        self.ismagento_list = list()
        self.isother_list = list()
        self.inventoryPath_list = list()
        self.detail_pattern_list = list()
        self.pagination_pattern_list = list()
        self.redirect_url_list = list()

        self.load_websites()

        # declare upc variables
        self.link_set = list()
        self.upc_set = dict()

    # spider rule
    rules = (
        Rule(LinkExtractor(), callback='parse_item', process_links="link_filtering", follow=True),
    )

    # link filter
    def link_filtering(self, links):
        res = []

        for link in links:

            # check already gotten url
            if link.url in self.link_set:
                continue
            else:
                self.link_set.append(link.url)

            # check allowed domain
            if make_domain(link.url) not in self.allowed_domains:
                continue

            # check url deepth
            if link.url.count('/') > 8:
                continue

            # patterns that url shouldn't have
            link_except_patterns = ['/b/', '/account', '/login', '/wishlist', '/add/', '-finder', '/faq', '/about', 'locator', '/blog', '/our-story', '/recipes', 'recommendation', 'add-to-cart=', '/cart', '/locations', '/contact', 'reviews', '/why-', '/how-', '/find-', '/where', 'policy', '/community', '/order']

            # check url have except pattern
            if any(except_item in link.url for except_item in link_except_patterns):
                continue

            # ------------- For Test ------------------------
            if '/protein-powders/' not in link.url:
                continue
            # -----------------------------------------------

            # print('*****', link.url)

            res.append(link)

        return res

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):

        spider = super(MySpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    # when spider closed, run
    def spider_closed(self, spider):

        # close conn
        if self.conn is not None:
            self.conn.close()
            print('Database connection closed.')

        print('------- closed spider -------')

    # parse item from response
    def parse_item(self, response):

        time.sleep(1)
        # if domain changed, return
        res_domain = make_domain(response.url)
        if res_domain in self.allowed_domains:
            index = self.allowed_domains.index(res_domain)
        else:
            return

        # return if category or inventory page
        response_url_except_patterns = ['/c-', '/c/', '/b-', '/b/', '/m-', '/m/', '/s-', 's/?']
        if any(item in response.url for item in response_url_except_patterns):
            print('--- Returned by URL pattern : {}'.format(response.url))
            return

        # convert response to text
        try:
            res_content = str(response.text)
        except Exception as err:
            print("----- Text doesn't exist in response")
            return

        if self.detail_pattern_list[index]:
            if re.sub(r'\s', '', self.detail_pattern_list[index]).lower() not in re.sub(r'\s', '', res_content).lower():
                print('----- Returned by detail pattern {} : {}'.format(self.detail_pattern_list[index], response.url))
                return
        else:
            response_text_except_patterns = re.compile(r'Filter\s*by\s*keyword|Filter\sresults|CollectionFilter|FILTERS|filter-dropdown[\s\'\"]|Sort By|View.?More|Next.?Page|compare.?checkbox', re.I)
            if response_text_except_patterns.search(res_content):
                print("----- Returned by TEXT pattern - {} : {}".format(response_text_except_patterns.search(res_content).group(), response.url))
                return

        # Creating a cursor object using the cursor() method
        cursor = self.conn.cursor()

        upc_code = self.get_upc(res_content)
        upc_attrs = None

        if upc_code:
            print('----- {} -----'.format(upc_code))
            if upc_code in self.upc_set:
                upc_attrs = self.upc_set[upc_code]
            else:
                upc_attrs = self.get_upc_attr_from_api(upc_code)

                if not upc_attrs:
                    upc_attrs = self.get_upc_attr_from_request(upc_code)

                if upc_attrs:
                    self.upc_set[upc_code] = upc_attrs

            print('---------- Found UPC Attrs------------')
            print(upc_attrs)
            print('----------------------')

        final_dict = dict()
        final_dict['Website_Name'] = self.company_list[index]
        final_dict['Website_homepage'] = self.website_list[index]
        final_dict['Product_URL'] = response.url
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
        final_dict['Product_Name'] = self.get_product_name(response)

        # get product description
        final_dict['Product_Description'] = self.get_product_description(response)

        # get product category
        final_dict['Product_Category'] = self.get_product_category(response)

        # get product category
        final_dict['Product_Brand'] = self.get_product_brand(res_content)

        # get product price
        final_dict['current_price'] = self.get_product_price(response)

        # get product img url
        if upc_attrs and "images" in upc_attrs and upc_attrs["images"]:
            final_dict['img_url'] = upc_attrs["images"][0]
        else:
            final_dict['img_url'] = self.get_product_img_url(response)

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

        print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        print(final_dict)
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
                print("----------- existing row. uid : %s ------------" % format(exist_row[0]))

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
                    cursor.execute(sql_update_query, (exist_row[17], final_dict['current_price'], final_dict["percent_from_last_price"], str(datetime.datetime.today()), exist_row[0]))
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
                final_dict['Product_Name'], final_dict['Product_Description'], final_dict["Product_Category"], final_dict["Product_Brand"], final_dict['UPC'], final_dict['upc_Category'],
                final_dict['upc_Brand'], final_dict['upc_Size'], final_dict['upc_Dimension'], final_dict['upc_Ingredients'], final_dict['last_price'], final_dict['current_price'], final_dict['percent_from_last_price'], today_date, today_date, final_dict['img_url'])
                cursor.execute(insert_query, record_to_insert)

            # close cursor object
            cursor.close()
        else:
            # close cursor object
            cursor.close()
            return

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
        cursor = self.conn.cursor()
        select_Query = "select * from websites"

        cursor.execute(select_Query)
        websites_records = cursor.fetchall()

        for row in websites_records:
            if row[2] and row[13] == "C" and row[4] == "No":
                if row[1] == "Luckyvitamin":
                    self.company_list.append(row[1])
                    self.website_list.append(row[2])
                    self.site_catagory_list.append(row[3])
                    self.category_lookup_list.append(row[5])
                    self.detail_lookup_list.append(row[6])
                    self.sign_up_deal_list.append(row[7])
                    self.sign_up_deal_ifYes_list.append(row[8])
                    self.shipping_cost_list.append(row[9])
                    self.isshopify_list.append(row[10])
                    self.ismagento_list.append(row[11])
                    self.isother_list.append(row[12])
                    self.inventoryPath_list.append(row[14])
                    self.detail_pattern_list.append(row[15])
                    self.pagination_pattern_list.append(row[16])
                    self.redirect_url_list.append(row[17])
                    self.allowed_domains.append(make_domain(row[2].strip()))
                    self.start_urls.append(make_url(row[2].strip()))

        print(self.website_list)
        # close communication with the PostgreSQL database server
        cursor.close()

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
            print(traceback.print_exc())
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
                    tr_text_list = tr_ele.xpath('.//text()').extract()
                    key = re.sub('\s', '', tr_text_list[0].strip()).lower()
                    value = tr_text_list[1].strip()
                    if 'brand' in key:
                        product_dict['brand'] = value
                    elif "size" in key:
                        product_dict['size'] = value
                    elif "dimension" in key:
                        product_dict['dimension'] = value

                category_ele = body.xpath('//ol[@class="category breadcrumb"]/li[@class="breadcrumb-item active"]')
                if category_ele:
                    product_dict['category'] = category_ele.xpath('.//text()').extract_first()
                    if '>' in product_dict['category']:
                        product_dict['category'] = product_dict['category'].split('>')[-1].strip()

                for small_ele in body.xpath('//small'):
                    small_ele_text = small_ele.xpath('.//text()').extract_first()
                    if "ingredients" in small_ele_text.lower():
                        product_dict['description'] = small_ele_text

                return product_dict

            else:
                return None
        except:
            print(traceback.print_exc())
            return None

    # get product name
    def get_product_name(self, response):
        product_name_pattern_list = [
            { 'xpath' : '//h1[@itemprop="name"]', 'key': 'name', 'type': 'itemprop'},
            { 'xpath' : '//div[@data-test="product-title"]', 'key' : 'product-title', 'type' : 'data-test' },
            { 'xpath' : '//h1', 'key' : 'productname', 'type' : 'id'},
            { 'xpath' : '//h1', 'key' : 'product_name', 'type' : 'class'},
            { 'xpath' : '//div', 'key' : 'product_name', 'type' : 'class'},
            { 'xpath' : '//h2', 'key': 'product-title', 'type': 'class'},
            { 'xpath' : '//div', 'key': 'product_name', 'type': 'class'},
            { 'xpath' : '//h1', 'key': 'page,title', 'type': 'class'},
            { 'xpath' : '//h1', 'key': 'title', 'type': 'id'},
            { 'xpath' : '//h1', 'key': 'title', 'type': 'class'},
            { 'xpath' : '//h1', 'key': '', 'type': ''},
            { 'xpath' : '//div', 'key': 'title', 'type': 'class'},
            { 'xpath' : '//*[@itemprop="name"]', 'key': 'name', 'type': 'itemprop'},
        ]

        for pattern in product_name_pattern_list:
            title_elements = response.xpath(pattern['xpath'])
            for title_element in title_elements:
                try:
                    has_property_flag = False
                    if pattern['type'] and pattern['key']:
                        if title_element.xpath('@{}'.format(pattern['type'])).extract_first() and all(
                            key in title_element.xpath('@{}'.format(pattern['type'])).extract_first().lower() for key in
                            pattern['key'].split(',')):
                            has_property_flag = True
                    elif pattern['type']:
                        if title_element.xpath('@{}'.format(pattern['type'])):
                            has_property_flag = True
                    else:
                        has_property_flag = True

                    if has_property_flag:
                        product_name = re.sub('\s+', ' ', " ".join(title_element.xpath('.//text()').extract())).strip()
                        if product_name:
                            return product_name
                except:
                    print(traceback.print_exc())
                    continue

        return None

    # get product description
    def get_product_description(self, response):
        product_description_pattern_list = [
            { 'xpath' : '//*[@itemprop="description"]', 'key' : 'description', 'type' : 'itemprop' },
            { 'xpath' : '//article', 'key' : 'product_description,product-description', 'type' : 'class'},
            { 'xpath' : '//ul', 'key' : 'prod-details,desc_prod', 'type' : 'class'},
            { 'xpath' : '//div', 'key' : 'productDetails', 'type' : 'id'},
            { 'xpath' : '//div', 'key' : 'prd-block_description,product-description,product-details,ProductDescriptionContainer,ab-store-single-product-header,product__description', 'type' : 'class'},
        ]

        for pattern in product_description_pattern_list:
            desc_elements = response.xpath(pattern['xpath'])
            for desc_element in desc_elements:
                try:
                    has_property_flag = False
                    if pattern['key']:
                        if desc_element.xpath('@{}'.format(pattern['type'])).extract_first() and any( key in desc_element.xpath('@{}'.format(pattern['type'])).extract_first().lower() for key in pattern['key'].split(',')):
                            has_property_flag = True
                    else:
                        if desc_element.xpath('@{}'.format(pattern['type'])):
                            has_property_flag = True

                    if has_property_flag:
                        product_desc = re.sub('\s+', ' ', " ".join(desc_element.xpath('.//text()').extract())).strip()
                        if product_desc:
                            return product_desc
                except:
                    print(traceback.print_exc())
                    continue
        return None

    # get product category
    def get_product_category(self, response):
        product_category_pattern_list = [
            {'xpath': '//*[@data-set="breadcrumb"]', 'key': '', 'type': ''},
            {'xpath': '//*[@data-test="breadcrumb"]', 'key': '', 'type': ''},
            {'xpath': '//*[@aria-label="breadcrumbs"]', 'key': '', 'type': ''},
            {'xpath': '//ol', 'key': 'breadcrumbs', 'type': 'class'},
            {'xpath': '//ol', 'key': 'BreadcrumbList', 'type': 'typeof'},
        ]

        for pattern in product_category_pattern_list:
            cat_elements = response.xpath(pattern['xpath'])
            for cat_element in cat_elements:
                try:
                    has_property_flag = False
                    if pattern['key'] and pattern['type']:
                        if cat_element.xpath('@{}'.format(pattern['type'])).extract_first() and any(
                                key in cat_element.xpath('@{}'.format(pattern['type'])).extract_first().lower() for
                                key in pattern['key'].split(',')):
                            has_property_flag = True
                    elif pattern['type']:
                        if cat_element.xpath('@{}'.format(pattern['type'])):
                            has_property_flag = True
                    else:
                        has_property_flag = True

                    if has_property_flag:
                        product_category = ''
                        for item in cat_element.xpath('.//text()').extract():
                            if re.sub(r'\s', '', item):
                                if not product_category:
                                    product_category = item
                                else:
                                    product_category += " / " + item

                        if product_category:
                            product_category = product_category.rsplit('/', 1)[0]
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
                        brand_string = res_content[item.end() : item.end() + 50]
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
    def get_product_price(self, response):
        product_price_pattern_list = [
            { 'xpath' : '//div[contains(@class,"product-detail__price")]/b', 'key' : '', 'type' : '' },
            { 'xpath' : '//div[@data-test="product-price"]', 'key' : '', 'type' : '' },
            { 'xpath' : '//*[@itemprop="price"]', 'key' : 'price', 'type' : 'itemprop' },
            { 'xpath' : '//*[@id="ProductPrice"]', 'key' : 'product,price', 'type' : 'id' },
            { 'xpath' : '//span', 'key': '', 'type': 'data-product-price'},
            { 'xpath': '//h2', 'key': 'product,price', 'type': 'id'},
            { 'xpath': '//*[@id="product-price"]//div', 'key': 'price', 'type': 'id'},
            { 'xpath' : '//span', 'key' : 'reducing,price', 'type' : 'aria-label'},
            { 'xpath' : '//span', 'key' : 'origin,price', 'type' : 'aria-label'},
            { 'xpath' : '//span', 'key' : 'prd,price', 'type' : 'class'},
            { 'xpath' : '//span', 'key' : 'product,price', 'type' : 'class'},
            { 'xpath' : '//span', 'key': 'current,price', 'type': 'class'},
            { 'xpath' : '//span', 'key': 'product,pricing', 'type': 'class'},
            { 'xpath' : '//div', 'key': 'product,price', 'type': 'class'},
            { 'xpath' : '//h2', 'key': 'product,price', 'type': 'class'},
            { 'xpath' : '//span', 'key' : 'item,price', 'type' : 'class'},
            { 'xpath' : '//span', 'key': 'price', 'type': 'class'},
            { 'xpath' : '//p', 'key': 'money', 'type': 'class'},
        ]

        for pattern in product_price_pattern_list:
            price_elements = response.xpath(pattern['xpath'])
            for price_element in price_elements:
                try:
                    has_property_flag = False
                    if pattern['key']:
                        if price_element.xpath('@{}'.format(pattern['type'])).extract_first() and all( key in price_element.xpath('@{}'.format(pattern['type'])).extract_first().lower() for key in pattern['key'].split(',')):
                            has_property_flag = True
                    elif pattern["type"]:
                        if price_element.xpath('@{}'.format(pattern['type'])):
                            has_property_flag = True
                    else:
                        has_property_flag = True

                    if has_property_flag:
                        product_price = re.sub('\s+', ' ', " ".join(price_element.xpath('.//text()').extract())).strip()
                        if product_price and re.search(r'\$\s*\d+\.\d+|\$\s*\d+', product_price):
                            return float(re.sub(r'\$', '', re.search(r'\$\s*\d+\.\d+|\$\s*\d+', product_price).group()))
                except:
                    print(traceback.print_exc())
                    continue

        return None

    # get product price
    def get_product_img_url(self, response):
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
            img_elements = response.xpath(pattern['xpath'])
            for img_element in img_elements:
                try:
                    has_property_flag = False
                    if pattern["key"] and pattern['type']:
                        if img_element.xpath('@{}'.format(pattern['type'])).extract_first() and all( key in img_element.xpath('@{}'.format(pattern['type'])).extract_first().lower() for key in pattern['key'].split(',')):
                            has_property_flag = True
                    elif pattern['type']:
                        if img_element.xpath('@{}'.format(pattern['type'])):
                            has_property_flag = True
                    else:
                        has_property_flag = True

                    if has_property_flag:
                        product_img = img_element.xpath('@src').extract_first() if img_element.xpath('@src').extract_first() else img_element.xpath('@data-src').extract_first()
                        if not product_img:
                            product_img = img_element.xpath('@{}'.format(pattern['type'])).extract_first()

                        if product_img and not any(item in product_img for item in product_img_except_pattern_list):
                            product_img_string = re.sub('\s+', ' ', product_img).strip()
                            if product_img_string:
                                return product_img_string.strip()
                except:
                    print(traceback.print_exc())
                    continue

        return None

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

def main():
    process = CrawlerProcess(get_project_settings())
    process.crawl("fooddataCrawler")
    process.start()

if __name__ == '__main__':
    main()
