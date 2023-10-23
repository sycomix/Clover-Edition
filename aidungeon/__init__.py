from .play import *

import traceback
from pathlib import Path
from datetime import datetime

import gc
import torch

from .utils import *

def print_intro():
    print()

    with open(Path("interface/", "mainTitle.txt"), "r", encoding="utf-8") as file:
        output(file.read(), "title", wrap=False, beg='')

    with open(Path("interface/", "subTitle.txt"), "r", encoding="utf-8") as file:
        output(file.read(), "subtitle", wrap=False, beg='')

    output("Go to https://github.com/cloveranon/Clover-Edition/ "
           "or email cloveranon@nuke.africa for bug reports, help, and feature requests.",
           'subsubtitle', end="\n\n")

if not use_ptoolkit() and os.name == 'nt':
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    output("INFO: ANSI escape sequence enabled")


logger.info(f"Colab detected: {in_colab()}")


if not Path("prompts", "Anime").exists():
    try:
        from . import pastebin
    except:
        output("Continuing without downloading prompts...", "error")


if __name__ in ["__main__", "aidungeon"]:
    with open(Path("interface/", "clover"), "r", encoding="utf-8") as file_:
        print(file_.read())
    try:
        gm = GameManager(get_generator())
        while True:
            # May be needed to avoid out of mem
            gc.collect()
            torch.cuda.empty_cache()
            print_intro()
            gm.play_story()
    except KeyboardInterrupt:
        output("Quitting game.", "message")
        if gm and gm.story:
            if input_bool("Do you want to save? (y/N): ", "query"):
                save_story(gm.story)
    except Exception:
        traceback.print_exc()
        output("A fatal error has occurred. ", "error")
        if gm and gm.story:
            if not gm.story.savefile or len(gm.story.savefile.strip()) == 0:
                savefile = datetime.now().strftime("crashes/%d-%m-%Y_%H%M%S")
            else:
                savefile = gm.story.savefile
            save_story(gm.story, file_override=savefile)
        exit(1)