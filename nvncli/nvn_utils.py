import copy
import json
from functools import wraps
import random
from typing import Any, Dict
import re
from urllib import request
from urllib.request import Request
from bs4 import BeautifulSoup

from delta_utils import delta_process

def is_url(url):
	url_pattern = r'^https?://(.*?)\.(.*?)$'
	result = re.findall(url_pattern, url)

	if len(result) == 0: 
		return False
	return True

def make_url(url, ext):
	if ext[0] == '/':
		return url + ext
	else:
		return url + '/' + ext

def calculateLength (content):
    content = re.sub("((\r|\n)+?)", 'n', content, flags=re.MULTILINE)
    return len(content)

def rawTextToDelta (txt, txtDelete = False):
    deltaText = re.sub("\"", '\\\"', txt, flags=re.MULTILINE)
    if txtDelete == False:
        deltaText = re.sub("(^(?![\r\n]).*$)", '{"insert": "\g<1>"},', deltaText, 0, flags=re.MULTILINE)
        deltaText = re.sub("((\r|\n)+?)", '{"attributes":{"block":true},"insert":"\\\\n"},', deltaText, flags=re.MULTILINE)
        deltaText = deltaText + '{"attributes":{"block":true},"insert":"\\\\n"}'
    else:
        deltaText = re.sub("((\r|\n)+?)", '\\\\n', deltaText, 0, flags=re.MULTILINE)
        deltaText = '{"insert": "' + deltaText + '"}'
        deltaText = deltaText + ',{"delete": ' + str(calculateLength(txt)) + '}'
    if deltaText[-1] == ',':
        deltaText = deltaText[:-1]
    delta = json.loads("[" + deltaText + "]")
    result = json.dumps({
        "ops": delta
    })
    return result

def sharedUrl_deltaToRawText (shared_url):
    request_obj = Request("https://notevn.com/get_shared/" + shared_url)

    response_obj = request.urlopen(request_obj)
    
    content = json.loads(response_obj.read())['ops']

    return deltaToRawText(content)


def deltaToRawText (content):
    randomSeed = "nvncli_dotpoint_" + str(random.seed(20)) + "_roy"

    t = delta_process.TranslatorBase()
    result = t.translate_to_html(content)

    result = re.sub("\<p\>(.*?)\<\/p\>", "<p>\g<1></p>" + randomSeed, result, flags=re.DOTALL|re.IGNORECASE|re.MULTILINE)
    bs = BeautifulSoup(result, 'html.parser')

    resultTxt = re.sub(randomSeed, "\n", bs.get_text(), flags=re.DOTALL|re.IGNORECASE)
    return resultTxt
