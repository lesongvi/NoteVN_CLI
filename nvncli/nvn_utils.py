import copy
import json
from functools import wraps
import random
from typing import Any, Dict
import re
from urllib import request
from urllib.request import Request
from bs4 import BeautifulSoup
# from difflib import ndiff

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

def getCurrentLength (key):
    request_obj = Request("https://notevn.com/get_shared/" + key)

    response_obj = request.urlopen(request_obj)
    
    try:
        content = json.loads(response_obj.read())['ops']
    except Exception as _:
        return 0

    return calculateLength(deltaToRawText(content))

def generateDeleteContent (key):
    delta = '{"delete":' + str(getCurrentLength(key)) + '}'
    result = json.loads("[" + delta + "]")

    return json.dumps({
        "ops": result
    })

def getDefaultContent (content, key):
    result = json.loads('[{"insert": "' + content.replace("\n", "\\n") + '"}, {"delete":' + str(getCurrentLength(key) - 1) + '}]')
    return json.dumps({
        "ops": result
    })

def genMySeed ():
    random.seed(4542355562136458828)
    return random.randint(1000000000, 9999999999)

def calculateIOContentIncludeRandomSeed (content, randomSeed, start, end):
    return len(content.replace("\n", randomSeed)[start:end].replace(randomSeed, "d"))

def exportAsDumps (content):
    return json.dumps(content)

def comparingAndRetainIf (old_content, new_content = None, key = None):
    # newDeltaContent = [];
    # randomSeed = " nvncli_dotpoint_" + str(genMySeed()) + "_vdiu "
    # if new_content == None:
    #     request_obj = Request("https://notevn.com/get_shared/" + key)

    #     response_obj = request.urlopen(request_obj)
        
    #     try:
    #         new_content = deltaToRawText(json.loads(response_obj.read())['ops'])
    #         new_content = new_content[:-1]
    #     except Exception as _:
    #         return None
    # if old_content == new_content:
    #     return None

    # diff_between_old_and_new = ndiff(new_content.replace("\n", randomSeed).splitlines(keepends=True), old_content.replace("\n", randomSeed).splitlines(keepends=True))
    # isChange = [[], []]
    # for (idx, value) in enumerate(list(diff_between_old_and_new)):
    #     if idx == 1 and value[0] == '?':
    #         for (i, symbol) in enumerate([x for x in value[2:]]):
    #             if symbol == '-' or symbol == '^':
    #                 if isChange[0] == []:
    #                     isChange[0] = [i, i]
    #                 elif isChange[0][1] == i - 1:
    #                     isChange[0][1] = i
    #                 else:
    #                     return getDefaultContent(old_content, key)
    #     if (idx == 3 or idx == 2) and value[0] == '?':
    #         for (i, symbol) in enumerate([x for x in value[2:]]):
    #             if symbol == '+' or symbol == '^':
    #                 if isChange[1] == []:
    #                     isChange[1] = [i, i]
    #                 elif isChange[1][1] == i - 1:
    #                     isChange[1][1] = i
    #                 else:
    #                     return getDefaultContent(old_content, key)
    # if isChange[0] != [] or isChange[1] != []:
    #     if isChange[0] != [] and isChange[1] != [] and isChange[0][0] != isChange[1][0]:
    #         return getDefaultContent(old_content, key)
    #     re_genre = "%s" % randomSeed
    #     regex_pattern = re.compile(re_genre, re.MULTILINE|re.DOTALL)  
    #     if isChange[0] != []:
    #         if isChange[1][0] != 0:
    #             newDeltaContent.append({
    #                 "retain": calculateIOContentIncludeRandomSeed (old_content, randomSeed, 0, isChange[1][0])
    #             })
    #         elif isChange[0][0] != 0:
    #             newDeltaContent.append({
    #                 "retain": calculateIOContentIncludeRandomSeed (old_content, randomSeed, 0, isChange[0][0])
    #             })
    #         if isChange[1] != [] and isChange[1][0] == isChange[0][0]:
    #             textToReplace = old_content.replace("\n", randomSeed)[isChange[0][0]:isChange[1][1] + 1]
    #             insertTxt = regex_pattern.sub('\\n', textToReplace, count=0)
    #             newDeltaContent.append({
    #                 "insert": insertTxt
    #             })
    #         newDeltaContent.append({
    #             "delete": calculateIOContentIncludeRandomSeed (old_content, randomSeed, isChange[0][0], isChange[1][1] - 1)
    #         })
    #         return exportAsDumps(newDeltaContent)
    #     elif isChange[1] != []:
    #         if isChange[1][0] != 0:
    #             newDeltaContent.append({
    #                 "retain": calculateIOContentIncludeRandomSeed (old_content, randomSeed, 0, isChange[1][0])
    #             })
    #         textToReplace = old_content.replace("\n", randomSeed)[isChange[1][0]:isChange[1][1] + 1]
    #         insertTxt = regex_pattern.sub('\\n', textToReplace, count=0)
    #         newDeltaContent.append({
    #             "insert": insertTxt
    #         })
    #         return exportAsDumps(newDeltaContent)
    return getDefaultContent(old_content, key)

def rawTextToDelta (txt, txtDelete = False, key = None):
    deltaText = re.sub("\"", '\\\"', txt, flags=re.MULTILINE)
    if txtDelete == False:
        deltaText = re.sub("(^(?![\r\n]).*$)", '{"insert": "\g<1>"},', deltaText, 0, flags=re.MULTILINE)
        deltaText = re.sub("((\r|\n)+?)", '{"attributes":{"block":true},"insert":"\\\\n"},', deltaText, flags=re.MULTILINE)
        deltaText = deltaText + '{"attributes":{"block":true},"insert":"\\n"}'
    else:
        if key == None:
            raise Exception("Key is required when txtDelete is True")
        deltaText = re.sub("((\r|\n)+?)", '\\\\n', deltaText, 0, flags=re.MULTILINE)
        deltaText = '{"insert": "' + deltaText + '"}'
        # deltaText = deltaText + ',{"delete": ' + str(getCurrentLength(key)) + '}'
    if deltaText[-1] == ',':
        deltaText = deltaText[:-1]

    delta = json.loads("[" + deltaText + "]")

    return json.dumps({
        "ops": delta
    })

def sharedUrl_deltaToRawText (shared_url):
    request_obj = Request("https://notevn.com/get_shared/" + shared_url)

    response_obj = request.urlopen(request_obj)
    
    content = json.loads(response_obj.read())['ops']

    return deltaToRawText(content)

def deltaToRawText (content):
    randomSeed = "nvncli_dotpoint_" + str(genMySeed()) + "_roy"

    t = delta_process.TranslatorBase()
    result = t.translate_to_html(content)

    result = re.sub("\<p\>(.*?)\<\/p\>", "<p>\g<1></p>" + randomSeed, result, flags=re.DOTALL|re.IGNORECASE|re.MULTILINE)
    bs = BeautifulSoup(result, 'html.parser')

    resultTxt = re.sub(randomSeed, "\n", bs.get_text(), flags=re.DOTALL|re.IGNORECASE)
    return resultTxt
