# coding: utf-8
import re

# TODO: try to get rid of this
from pyjarowinkler import distance
import torch
import random
import textwrap
import os
import sys

from getconfig import logger, settings, colors
from shutil import get_terminal_size

def in_colab():
    """Some terminal codes don't work in a colab notebook."""
    # from https://github.com/tqdm/tqdm/blob/master/tqdm/autonotebook.py
    try:
        from IPython import get_ipython
        if (not get_ipython()) or ('IPKernelApp' not in get_ipython().config):  # pragma: no cover
            raise ImportError("console")
        if 'VSCODE_PID' in os.environ:  # pragma: no cover
            raise ImportError("vscode")
    except ImportError:
        if get_terminal_size()[0]==0 or 'google.colab' in sys.modules:
            return True
        return False
    else:
        return True

termWidth = get_terminal_size()[0]
if termWidth < 5:
    logger.warning("Your detected terminal width is: "+str(get_terminal_size()[0]))
    termWidth = 999999999

def format_result(text):
    """
    Formats the result text from the AI to be more human-readable.
    """
    text = text.strip()
    text = re.sub("\n{3,}", "\n\n", text)
    text = re.sub("\n", " ", text)
    return text

# ECMA-48 set graphics codes for the curious. Check out "man console_codes"
def output(text1, col1="0", text2=None, col2="0", wrap=True, end=None):
    if text2 is None:
        res = "\x1B[{}m{}\x1B[{}m".format(col1, text1.strip(), colors["default"])
    else:
        res = "\x1B[{}m{}\x1B[{}m {}\x1B[{}m".format(col1, text1.strip(), col2, text2.strip(), colors["default"])
    if wrap:
        width = settings.getint("text-wrap-width")
        width = 999999999 if width < 2 else width
        width=min(width, termWidth)
        res = textwrap.fill(
            res, width, replace_whitespace=False
        )
    print(res, end=end)
    return res.count('\n') + 1

def input_line(str, col1=colors["default"], col2=colors["default"]):
    val = input("\x1B[{}m{}\x1B[0m\x1B[{}m".format(col1, str, col1))
    print("\x1B[0m", end="")
    return val

def clear_lines(n):
    """Clear the last line in the terminal."""
    if in_colab() or settings.getboolean('colab-mode'):
        # this wont work in colab etc
        return
    screen_code = "\033[1A[\033[2K"  # up one line, and clear line
    for _ in range(n):
        print(screen_code, end="")

def input_number(n):
    bell()
    val = input_line(
        "Enter a number from above (default 0):",
        colors["selection-prompt"],
        colors["selection-value"],
    )
    if val == "":
        return 0
    elif not re.match("^\d+$", val) or 0 > int(val) or int(val) > n:
        output("Invalid choice.", colors["error"])
        return input_number(n)
    else:
        return int(val)

def bell():
    if settings.getboolean("console-bell"):
        print("\x07", end="")

# TODO: get rid if pyjarowinker dependency
# (AOP) You could use a simpler method, but this has been reported by RebootTech as a much more accurate way to compare strings. It also helps clean up the history. So it will hurt ability to check for looping
def get_similarity(a, b):
    if len(a) == 0 or len(b) == 0:
        return 1
    return distance.get_jaro_distance(a, b, winkler=True, scaling=0.1)

def get_num_options(num):

    while True:
        choice = input("Enter the number of your choice: ")
        try:
            result = int(choice)
            if result >= 0 and result < num:
                return result
            else:
                print("Error invalid choice. ")
        except ValueError:
            print("Error invalid choice. ")

def player_died(text):
    """
    TODO: Add in more sophisticated NLP, maybe a custom classifier
    trained on hand-labelled data that classifies second-person
    statements as resulting in death or not.
    """
    lower_text = text.lower()
    you_dead_regexps = [
        "you('re| are) (dead|killed|slain|no more|nonexistent)",
        "you (die|pass away|perish|suffocate|drown|bleed out)",
        "you('ve| have) (died|perished|suffocated|drowned|been (killed|slain))",
        "you (\w* )?(yourself )?to death",
        "you (\w* )*(collapse|bleed out|chok(e|ed|ing)|drown|dissolve) (\w* )*and (die(|d)|pass away|cease to exist|(\w* )+killed)",
    ]
    return any(re.search(regexp, lower_text) for regexp in you_dead_regexps)

def player_won(text):
    lower_text = text.lower()
    won_phrases = [
        "you ((\w* )*and |)live happily ever after",
        "you ((\w* )*and |)live (forever|eternally|for eternity)",
        "you ((\w* )*and |)(are|become|turn into) ((a|now) )?(deity|god|immortal)",
        "you ((\w* )*and |)((go|get) (in)?to|arrive (at|in)) (heaven|paradise)",
        "you ((\w* )*and |)celebrate your (victory|triumph)",
        "you ((\w* )*and |)retire",
    ]
    return any(re.search(regexp, lower_text) for regexp in won_phrases)

def remove_profanity(text):
    return pf.censor(text)

def cut_trailing_quotes(text):
    num_quotes = text.count('"')
    if num_quotes % 2 == 0:
        return text
    else:
        final_ind = text.rfind('"')
        return text[:final_ind]


def split_first_sentence(text):
    first_period = text.find(".")
    first_exclamation = text.find("!")

    if first_exclamation < first_period and first_exclamation > 0:
        split_point = first_exclamation + 1
    elif first_period > 0:
        split_point = first_period + 1
    else:
        split_point = text[0:20]

    return text[0:split_point], text[split_point:]


def cut_trailing_action(text):
    lines = text.split("\n")
    last_line = lines[-1]
    if (
        "you ask" in last_line
        or "You ask" in last_line
        or "you say" in last_line
        or "You say" in last_line
    ) and len(lines) > 1:
        text = "\n".join(lines[0:-1])
    return text


def clean_suggested_action(result_raw, min_length=4):
    result_cleaned = standardize_punctuation(result_raw)
    result_cleaned = cut_trailing_sentence(result_cleaned, allow_action=True)

    # The generations actions carry on into the next prompt, so lets remove the prompt
    results = result_cleaned.split("\n")
    results = [s.strip() for s in results]
    results = [s for s in results if len(s) > min_length]

    # Sometimes actions are generated with leading > ! . or ?. Likely the model trying to finish the prompt or start an action.
    result = results[0].strip().lstrip(" >!.?") if len(results) else ""

    # result = cut_trailing_quotes(result)
    logger.debug(
        "full suggested action '%r'. Cropped: '%r'. Split '%r'",
        result_raw,
        result,
        results,
    )

    # Often actions are cropped with sentance fragments, lets remove. Or we could just turn up config_act["generate-number"]
    result = first_to_second_person(result)
    # Sometimes the suggestion start with "You" we will add that on later anyway so remove it here
    # result = re.sub("^ ?[Yy]ou try to ?", "", result)
    # result = re.sub("^ ?[Yy]ou start to ?", "", result)
    # result = re.sub("^ ?[Yy]ou ", "", result)
    logger.debug("suggested action after cleaning `%r`", result)
    return result


def fix_trailing_quotes(text):
    num_quotes = text.count('"')
    if num_quotes % 2 == 0:
        return text
    else:
        return text + '"'


def cut_trailing_sentence(text, allow_action=False):
    text = standardize_punctuation(text)
    last_punc = max(text.rfind("."), text.rfind("!"), text.rfind("?"))
    if last_punc <= 0:
        last_punc = len(text) - 1

    et_token = text.find("<")
    if et_token > 0:
        last_punc = min(last_punc, et_token - 1)
    # elif et_token == 0:
    #     last_punc = min(last_punc, et_token)

    if allow_action:
        act_token = text.find(">")
        if act_token > 0:
            last_punc = min(last_punc, act_token - 1)
        # elif act_token == 0:
        #     last_punc = min(last_punc, act_token)

    text = text[: last_punc + 1]

    text = fix_trailing_quotes(text)
    if allow_action:
        text = cut_trailing_action(text)
    return text


def replace_outside_quotes(text, current_word, repl_word):
    text = standardize_punctuation(text)

    reg_expr = re.compile(current_word + '(?=([^"]*"[^"]*")*[^"]*$)')

    output = reg_expr.sub(repl_word, text)
    return output


def is_first_person(text):

    count = 0
    for pair in first_to_second_mappings:
        variations = mapping_variation_pairs(pair)
        for variation in variations:
            reg_expr = re.compile(variation[0] + '(?=([^"]*"[^"]*")*[^"]*$)')
            matches = re.findall(reg_expr, text)
            count += len(matches)

    if count > 3:
        return True
    else:
        return False


def is_second_person(text):
    count = 0
    for pair in second_to_first_mappings:
        variations = mapping_variation_pairs(pair)
        for variation in variations:
            reg_expr = re.compile(variation[0] + '(?=([^"]*"[^"]*")*[^"]*$)')
            matches = re.findall(reg_expr, text)
            count += len(matches)

    if count > 3:
        return True
    else:
        return False


def capitalize(word):
    return word[0].upper() + word[1:]


def mapping_variation_pairs(mapping):
    mapping_list = []
    mapping_list.append((" " + mapping[0] + " ", " " + mapping[1] + " "))
    mapping_list.append(
        (" " + capitalize(mapping[0]) + " ", " " + capitalize(mapping[1]) + " ")
    )

    # Change you it's before a punctuation
    if mapping[0] == "you":
        mapping = ("you", "me")
    mapping_list.append((" " + mapping[0] + ",", " " + mapping[1] + ","))
    mapping_list.append((" " + mapping[0] + "\?", " " + mapping[1] + "\?"))
    mapping_list.append((" " + mapping[0] + "\!", " " + mapping[1] + "\!"))
    mapping_list.append((" " + mapping[0] + "\.", " " + mapping[1] + "."))

    return mapping_list


first_to_second_mappings = [
    ("I'm", "you're"),
    ("Im", "you're"),
    ("Ive", "you've"),
    ("I am", "you are"),
    ("was I", "were you"),
    ("am I", "are you"),
    ("wasn't I", "weren't you"),
    ("I", "you"),
    ("I'd", "you'd"),
    ("i", "you"),
    ("I've", "you've"),
    ("was I", "were you"),
    ("am I", "are you"),
    ("wasn't I", "weren't you"),
    ("I", "you"),
    ("I'd", "you'd"),
    ("i", "you"),
    ("I've", "you've"),
    ("I was", "you were"),
    ("my", "your"),
    ("we", "you"),
    ("we're", "you're"),
    ("mine", "yours"),
    ("me", "you"),
    ("us", "you"),
    ("our", "your"),
    ("I'll", "you'll"),
    ("myself", "yourself"),
]

second_to_first_mappings = [
    ("you're", "I'm"),
    ("your", "my"),
    ("you are", "I am"),
    ("you were", "I was"),
    ("are you", "am I"),
    ("you", "I"),
    ("you", "me"),
    ("you'll", "I'll"),
    ("yourself", "myself"),
    ("you've", "I've"),
]


def capitalize_helper(string):
    string_list = list(string)
    string_list[0] = string_list[0].upper()
    return "".join(string_list)


def capitalize_first_letters(text):
    first_letters_regex = re.compile(r"((?<=[\.\?!]\s)(\w+)|(^\w+))")

    def cap(match):
        return capitalize_helper(match.group())

    result = first_letters_regex.sub(cap, text)
    return result


def standardize_punctuation(text):
    text = text.replace("’", "'")
    text = text.replace("`", "'")
    text = text.replace("“", '"')
    text = text.replace("”", '"')
    return text


def first_to_second_person(text):
    text = " " + text
    text = standardize_punctuation(text)
    for pair in first_to_second_mappings:
        variations = mapping_variation_pairs(pair)
        for variation in variations:
            text = replace_outside_quotes(text, variation[0], variation[1])

    return capitalize_first_letters(text[1:])


def second_to_first_person(text):
    text = " " + text
    text = standardize_punctuation(text)
    for pair in second_to_first_mappings:
        variations = mapping_variation_pairs(pair)
        for variation in variations:
            text = replace_outside_quotes(text, variation[0], variation[1])

    return capitalize_first_letters(text[1:])
