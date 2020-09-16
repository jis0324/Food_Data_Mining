import base64
import random
from fooddataCrawler.settings import USER_AGENT_LIST
#from scrapy import log
# from fooddataCrawler.settings import PROXIES
# from w3lib.http import basic_auth_header
# from scrapy.conf import settings



class RandomUserAgentMiddleware(object):
    def process_request(self, request, spider):
        # settings.get(USER_AGENT_LIST)
        # print settings.get(USER_AGENT_LIST)

        ua = random.choice(USER_AGENT_LIST)
        if ua:
            print('Changing user_agent: ' + ua)
            request.headers.setdefault('User-Agent', ua)
            # this is just to check which user agent is being used for request
            '''spider.log(
                u'User-Agent: {} {}'.format(request.headers.get('User-Agent'), request),
                level=log.DEBUG
            )'''
'''    
class ProxyMiddleware(object):
    def process_request(self, request, spider):

        proxy = random.choice(PROXIES)
        if proxy['user_pass'] is not None:
            print('Changing proxy: ' + proxy['ip_port'])
            request.meta['proxy'] = "http://%s" % proxy['ip_port']
            #encoded_user_pass = base64.encodestring(proxy['user_pass'])
            #request.headers['Proxy-Authorization'] = 'Basic ' + encoded_user_pass            
            request.headers['Proxy-Authorization'] = basic_auth_header(
            'celltrack', 'I6DHYNGIC9VVNMM4D4ZCI991')
        else:
            request.meta['proxy'] = "https://%s" % proxy['ip_port']
            '''