import json
import re
import ssl
import random

from urllib import request
from urllib.request import Request
from urllib.parse import urlencode
from multiprocessing.dummy import Pool as ThreadPool

from brotli import decompress
from nvncli import multihost
from nvncli.multihost import MultiHost

# , sharedUrl_deltaToRawText, rawTextToDelta
from nvncli.nvn_utils import deltaToRawText

ssl._create_default_https_context = ssl._create_unverified_context


class Spider:
    notevnProcessAPI = "https://notevn.com/ajax.php"  # Defaults to main_note

    def __init__(self, url, verbose=False, multihost=MultiHost('main_note')):
        self.multihost = multihost
        self.url = url
        self.domain = ''
        self.response = ''
        self.verbose = verbose
        self.content = ''
        self.haspw = False
        self.notevnGetShared = self.multihost.get_shared_url()
        self.cookies = ""
        self.notevnProcessAPI = self.multihost.get_process_url()
        self.sub_mode = self.multihost.get_sub_mode()
        self.hide_content = False

        self.get_domain()
        self.USER_AGENTS = [
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
            'Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11) Gecko/20071127 Firefox/2.0.0.11',
            'Opera/9.25 (Windows NT 5.1; U; en)',
            'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)',
            'Mozilla/5.0 (compatible; Konqueror/3.5; Linux) KHTML/3.5.5 (like Gecko) (Kubuntu)',
            'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.142 Safari/535.19',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:11.0) Gecko/20100101 Firefox/11.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:8.0.1) Gecko/20100101 Firefox/8.0.1',
            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.151 Safari/535.19'
        ]
        self.url_key = ""
        self.pad_key = ""
        self.visit()

        if (self.url_key != "" and self.pad_key != ""):
            self.hit()

    def get_domain(self):
        pattern = r'(http[s]?://[a-zA-Z0-9]+?\.?[a-zA-Z0-9\-]+\.[a-z]{2,})'
        result = re.findall(pattern, self.url)

        if (result):
            self.domain = result[0]

    def generate_random_user_agent(self):
        return self.USER_AGENTS[random.randint(0, len(self.USER_AGENTS) - 1)]

    def visit(self):
        if (self.verbose):
            print("Visiting {}".format(self.url))

        try:
            request_obj = Request(self.url)
            request_obj.add_header(
                'User-Agent', self.generate_random_user_agent())
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
        request_obj.add_header('User-Agent', self.generate_random_user_agent())
        request_obj.add_header('Cookie', self.cookies)
        request_obj.add_header(
            'referer', self.multihost.get_domain_name(False) + self.url_key)
        request_obj.add_header('x-requested-with', 'XMLHttpRequest')
        request_obj.add_header('accept-encoding', 'gzip, deflate, br')

        return request_obj

    def checkEmptyOrLockLevel2(self):
        data = dict()
        data['action'] = 'getnote'
        data['file'] = '/' + self.url_key
        encoded_data = urlencode(data).encode('utf-8')

        request_obj = Request(self.notevnProcessAPI, method=self.multihost.get_method_type(
            'init'), data=encoded_data, headers={})

        request_obj = self.add_headers(request_obj)
        request_obj.add_header(
            'Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8')
        request_obj.add_header(
            'origin', self.multihost.get_domain_name(False, lastSlash=False))

        response_obj = request.urlopen(request_obj)
        data_b = json.loads(decompress(response_obj.read()))

        if 'empty' in data_b['data']['notes'][0]:
            return 'empty'
        if data_b['data']['notes'][0]['type'] != 'public':
            if data_b['data']['notes'][0]['type'] != 'protected':
                return 'protect_level2'
        return 'good'

    def hit(self):
        if self.checkEmptyOrLockLevel2() == 'protect_level2':
            self.haspw = True
            self.hide_content = True  # consider
            return
        elif self.checkEmptyOrLockLevel2() == 'empty':
            self.content = ""
            return
        # cookies=self.cookies
        anotherRequest = Request(self.notevnGetShared + self.pad_key)

        anotherRequest = request.urlopen(anotherRequest)
        try:
            read_content = anotherRequest.read()
            if self.sub_mode == 'debug':
                self.content = read_content
            elif self.sub_mode == 'main_note':
                response = json.loads(read_content)
                self.content = deltaToRawText(response['ops'])
        except ValueError as _:
            # lock level 2?
            self.haspw = True

        return

    def get_pad_key(self, response):
        pad_key_pattern = r'(?<=pad_key = \')[a-z0-9]+'
        results = re.findall(pad_key_pattern, response)

        if (results):
            for pad_key in results:
                self.pad_key = pad_key

    def get_url_key(self, response):
        url_key_pattern = r'(?<=url_key = \')[a-z0-9]+'
        results = re.findall(url_key_pattern, response)

        if (results):
            for url_key in results:
                if (url_key):
                    self.url_key = url_key

    def save(self, data):
        encoded_data = urlencode(data).encode('utf-8')

        request_obj = Request(self.notevnProcessAPI, method=self.multihost.get_method_type(
            'save'), data=encoded_data, headers={})

        request_obj = self.add_headers(request_obj)
        request_obj.add_header(
            'Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8')
        request_obj.add_header(
            'origin', self.multihost.get_domain_name(False, lastSlash=False))

        request.urlopen(request_obj)


if __name__ == '__main__':
    content = ""
    # url = "https://notevn.com/notevncli"
    # spider = Spider(url)
    # multihost = MultiHost('development')

    # print(sharedUrl_deltaToRawText('diu'), multihost.get_domain_name(False))
    # print(rawTextToDelta("test\ntesst"))
