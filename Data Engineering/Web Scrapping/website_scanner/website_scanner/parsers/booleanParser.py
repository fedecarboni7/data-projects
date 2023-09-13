import re

def booleanParser(text: str, regexes: list[str]) -> list[tuple] :
    result: list[tuple] = []
    for regex in regexes:
        if re.search(regex, text):

            result.append((regex, True))
        else :
            result.append((regex, False))
    
    return result