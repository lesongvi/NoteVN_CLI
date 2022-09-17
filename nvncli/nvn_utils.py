import json
import random
import re
from urllib import request
from urllib.request import Request
from bs4 import BeautifulSoup

from deltaprocessor import delta_process


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


def calculateLength(content):
    content = re.sub("((\r|\n)+?)", 'n', content, flags=re.MULTILINE)
    return len(content)


def getCurrentLength(key, shared_url=None):
    if shared_url == None:
        raise Exception("shared_url is None")

    request_obj = Request(shared_url + key)

    response_obj = request.urlopen(request_obj)

    try:
        content = json.loads(response_obj.read())['ops']
    except Exception as _:
        return 0

    return calculateLength(deltaToRawText(content))


def generateDeleteContent(key, shared_url=None):
    if shared_url == None:
        raise Exception("shared_url is None")

    delta = '{"delete":' + str(getCurrentLength(key, shared_url)) + '}'
    result = json.loads("[" + delta + "]")

    return json.dumps({
        "ops": result
    })


def getDefaultContent(content, key, shared_url=None):
    if shared_url == None:
        raise Exception("shared_url is required")
    result = json.loads('[{"insert": "' + content.replace("\n", "\\n") +
                        '"}, {"delete":' + str(getCurrentLength(key, shared_url) - 1) + '}]')
    return json.dumps({
        "ops": result
    })


def genMySeed():
    random.seed(4542355562136458828)
    return random.randint(1000000000, 9999999999)


def calculateIOContentIncludeRandomSeed(content, randomSeed, start, end):
    return len(content.replace("\n", randomSeed)[start:end].replace(randomSeed, "d"))


def exportAsDumps(content):
    return json.dumps(content)


def comparingAndRetainIf(old_content, new_content=None, key=None, shared_url=None):
    if shared_url == None:
        raise Exception("shared_url is required")

    return getDefaultContent(old_content, key, shared_url)


def rawTextToDelta(txt, txtDelete=False, key=None):
    deltaText = re.sub("\"", '\\\"', txt, flags=re.MULTILINE)
    if txtDelete == False:
        deltaText = re.sub(
            "(^(?![\r\n]).*$)", '{"insert": "\g<1>"},', deltaText, 0, flags=re.MULTILINE)
        deltaText = re.sub(
            "((\r|\n)+?)", '{"attributes":{"block":true},"insert":"\\\\n"},', deltaText, flags=re.MULTILINE)
        deltaText = deltaText + '{"attributes":{"block":true},"insert":"\\n"}'
    else:
        if key == None:
            raise Exception("Key is required when txtDelete is True")
        deltaText = re.sub("((\r|\n)+?)", '\\\\n',
                           deltaText, 0, flags=re.MULTILINE)
        deltaText = '{"insert": "' + deltaText + '"}'
    if deltaText[-1] == ',':
        deltaText = deltaText[:-1]

    delta = json.loads("[" + deltaText + "]")

    return json.dumps({
        "ops": delta
    })


def sharedUrl_deltaToRawText(shared_key, shared_url=None):
    if shared_url == None:
        raise Exception("shared_url is required")

    request_obj = Request(shared_url + shared_key)

    response_obj = request.urlopen(request_obj)

    content = json.loads(response_obj.read())['ops']

    return deltaToRawText(content)


def deltaToRawText(content):
    randomSeed = "nvncli_dotpoint_" + str(genMySeed()) + "_roy"

    t = delta_process.TranslatorBase()
    result = t.translate_to_html(content)

    result = re.sub("\<p\>(.*?)\<\/p\>", "<p>\g<1></p>" + randomSeed,
                    result, flags=re.DOTALL | re.IGNORECASE | re.MULTILINE)
    bs = BeautifulSoup(result, 'html.parser')

    resultTxt = re.sub(randomSeed, "\n", bs.get_text(),
                       flags=re.DOTALL | re.IGNORECASE)
    return resultTxt
