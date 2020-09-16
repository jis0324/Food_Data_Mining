# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class FooddatacrawlerItem(scrapy.Item):
    # define the fields for your item here like:

    RATING = scrapy.Field()
    RESTNAME = scrapy.Field()
    MENU = scrapy.Field()
    PHONE = scrapy.Field()
    ADDRESS = scrapy.Field()
    CITY = scrapy.Field()
    STATE = scrapy.Field()
    
