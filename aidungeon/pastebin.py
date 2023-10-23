from urllib import request, error
import re
import os
from .utils import *
from pathlib import Path

fnamesSoFar = {}


def filename(s):
    fname = re.sub("-$", "", re.sub("^-", "", re.sub("[^a-zA-Z0-9_-]+", "-", s)))
    n = 1
    fname2 = fname
    while fname2 in fnamesSoFar:
        n += 1
        fname2 = f"{fname}-{n}"
    fnamesSoFar[fname2] = True
    return fname2


try:
    paste = request.urlopen("https://0paste.com/261042.txt").read().decode("utf-8")
except error.HTTPError as e:
    if e.code == 404:
        output("Unable to find pastebin for scraping.", "error")
    else:
        output(
            f"Unable to load pastebin for custom prompts. Error code: {e.code}",
            "error",
        )
except error.URLError as e:
    output(
        f"Unexpected error while trying to load pastebin prompts! Error code: {e.code}",
        "error",
    )
paste = re.sub(r'\nTAGS:.*\n', '\n', paste)
#pipe is never used in paste so use it as a seperator
paste = re.sub("=====+", "|", paste)
paste = re.sub("\r", "", paste)
paste = re.sub("\n\s*\n\s*", "\n\n", paste)
sections = re.findall(r"[^|]+", paste)
for sect in sections[2:][:-1]:
    category = re.search(r"\*\*\*([^\*]+)\*\*\*", sect).group(1)
    category = re.sub(".[pP]rompts?$", "", category)
    category = filename(category)
    try:  
        Path("prompts", category).mkdir(exist_ok=True)
        print(category)
    except IOError:
        output("Permission error! Unable to create directory for custom prompts.", "error")
    for story in list(filter(None, sect.split("\n\n")))[1:]:
        title = re.search(r"^\(([^\)]+)", story)
        title = title.group(1) if bool(title) else story[:30]
        title = f"{filename(title)}.txt"
        with Path("prompts", category, title).open("w", encoding="UTF-8") as f:
            try:
                f.write(re.sub(r"^\([^\)]+\)\n", "", story))
            except IOError:
                output("Permission error! Unable to write custom prompt to file.", "error")
