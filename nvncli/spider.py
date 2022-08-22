import json
import re
import ssl

from urllib import request
from urllib.request import Request
from urllib.parse import urlencode
from multiprocessing.dummy import Pool as ThreadPool

from brotli import decompress

from nvncli.nvn_utils import deltaToRawText #, sharedUrl_deltaToRawText, rawTextToDelta

ssl._create_default_https_context = ssl._create_unverified_context

class Spider:
    notevnProcessAPI = "https://notevn.com/ajax.php"

    def __init__(self,url, verbose=False):
        self.url = url
        self.domain = ''
        self.response = ''
        self.verbose = verbose
        self.content = ''
        self.haspw = False
        self.notevnGetShared = "https://notevn.com/get_shared/"
        self.cookies = ""

        self.get_domain()
        self.USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36'
        self.url_key = ""
        self.pad_key = ""
        self.visit()

        if(self.url_key != "" and self.pad_key != ""):
            self.hit()
    
    def get_domain(self):
        pattern = r'(http[s]?://[a-zA-Z0-9]+?\.?[a-zA-Z0-9\-]+\.[a-z]{2,})'
        result = re.findall(pattern, self.url)

        if(result):
            self.domain = result[0]

    def visit(self):
        if(self.verbose):
            print("Visiting {}".format(self.url))
        
        try:
            request_obj = Request(self.url)
            request_obj.add_header('User-Agent',self.USER_AGENT)
            request_obj.add_header('Content-Type', 'text/html')
            response_obj = request.urlopen(request_obj)
            self.headers = response_obj.getheaders()
            self.cookies = response_obj.getheader('Set-Cookie')
            self.response = response_obj.read().decode('utf-8')
            
            self.get_pad_key(self.response)
            self.get_url_key(self.response)

        except Exception as e: 
            print(e)

    def add_headers(self, request_obj):
        request_obj.add_header('User-Agent',self.USER_AGENT)
        request_obj.add_header('Cookie', self.cookies)
        request_obj.add_header('referer', 'https://notevn.com/' + self.url_key)
        request_obj.add_header('x-requested-with', 'XMLHttpRequest')
        request_obj.add_header('accept-encoding', 'gzip, deflate, br')
        
        return request_obj

    def hit(self):
        anotherRequest = Request(self.notevnGetShared + self.pad_key) # cookies=self.cookies
        
        anotherRequest = request.urlopen(anotherRequest)
        try:
            response = json.loads(anotherRequest.read())
            self.content = deltaToRawText(response['ops'])
        except ValueError as _:
            self.haspw = True

        return

    def get_pad_key(self, response):
        pad_key_pattern = r'(?<=pad_key = \')[a-z0-9]+'
        results = re.findall(pad_key_pattern, response)

        if(results):
            for pad_key in results:
                self.pad_key = pad_key

    def get_url_key(self, response):
        url_key_pattern = r'(?<=url_key = \')[a-z0-9]+'
        results = re.findall(url_key_pattern, response)

        if(results):
            for url_key in results:
                if(url_key):
                    self.url_key = url_key

    def save(self, data):
        encoded_data = urlencode(data).encode('utf-8')

        request_obj = Request(self.notevnProcessAPI, method="POST", data=encoded_data, headers={})

        request_obj = self.add_headers(request_obj)
        request_obj.add_header('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8')
        request_obj.add_header('origin', 'https://notevn.com')

        request.urlopen(request_obj)

if __name__ == '__main__':
    content = ""
    # url = "https://notevn.com/notevncli"
    # spider = Spider(url)

    # print(sharedUrl_deltaToRawText('diu'))
    # print(rawTextToDelta("test\ntesst"))

