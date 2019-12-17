import os
#import sys
#import time
#import json
import configparser
from pathlib import Path
from random import shuffle
from shutil import get_terminal_size

from generator.gpt2.gpt2_generator import *
from story.story_manager import *
from story.utils import *

#perhaps all the following should be put in a seperate utils file like original
config = configparser.ConfigParser()
config.read('config.ini')
settings=config["Settings"]
colors=config["Colors"]

os.environ["TF_CPP_MIN_LOG_LEVEL"] = settings["loglevel"]

if not Path('prompts', 'Anime').exists():
    import pastebin

#ECMA-48 set graphics codes for the curious. Check out "man console_codes"
def colPrint(str, col='0'):
        print("\x1B[{}m{}\x1B[{}m".format(col, str, colors["default"]))

def colInput(str, col1=colors["default"], col2=colors["default"]):
    val=input("\x1B[{}m{}\x1B[0m\x1B[{}m".format(col1,str,col1))
    print('\x1B[0m', end='')
    return val

def getNumberInput(n):
    val=colInput("Enter a number from above:", colors["selectionPrompt"], colors["selectionValue"])
    if val=='':
        return 0
    elif 0>int(val) or int(val)>=n:
        colPrint("Invalid choice.", colors["error"])
        return getNumberInput(n)
    else:
        return int(val)

def selectFile(p=Path('prompts')):
    if p.is_dir():
        files=[x for x in p.iterdir()]
        shuffle(files)
        for n in range(len(files)):
            colPrint('{}: {}'.format(n, re.sub(r'\.txt$', '', files[n].name)), colors["menu"])
        return selectFile(files[getNumberInput(len(files))])
    else:
        with p.open() as file:
            line1=file.readline()
            rest=file.read()
        return (line1, rest)

def instructions():
    with open('interface/instructions.txt', 'r', encoding='utf-8') as file:
         colPrint(file.read(), colors["instructions"])


#"\nEnter a prompt that describes who you are and the first couple sentences of where you start "
#            "out ex:\n 'You are a knight in the kingdom of Larion. You are hunting the evil dragon who has been "
#            + "terrorizing the kingdom. You enter the forest searching for the dragon and see' "



def play():
    colPrint("\nInitializing AI Dungeon! (This might take a few minutes)\n", colors["loadingMessage"])
    generator = GPT2Generator(
            generate_num=settings.getint('generatenum'),
            temperature=settings.getfloat("temp"),
            top_k=settings.getint("topkeks"),
            top_p=settings.getfloat("top_p"))
    story_manager = UnconstrainedStoryManager(generator)
    print("\n")

    with open("interface/mainTitle.txt", "r", encoding="utf-8") as file:
        colPrint(file.read(), colors["title"])

    with open('interface/subTitle.txt', 'r', encoding="utf-8") as file:
        cols=get_terminal_size()[0]
        for line in file:
            line=re.sub(r'\n', '', line)
            line=line[:cols]
            colPrint(re.sub(r'\|[ _]*\|', lambda x: '\x1B[7m'+x.group(0)+'\x1B[27m', line), colors["subtitle"])
        

    while True:
        if story_manager.story != None:
            del story_manager.story

        print("\n\n")
        
        context, prompt = selectFile()

        instructions()

        colPrint("\nGenerating story...", colors["loadingMessage"])

        story_manager.start_new_story(
            prompt, context=context
        )
        print("\n")
        colPrint(str(story_manager.story), colors["AIText"])

        while True:
            action = colInput("> ", colors["mainPrompt"], colors["userText"])
            if action == "restart":
                #rating = input("Please rate the story quality from 1-10: ")
                #rating_float = float(rating)
                #story_manager.story.rating = rating_float
                break
            elif action == "quit":
                #rating = input("Please rate the story quality from 1-10: ")
                #rating_float = float(rating)
                #story_manager.story.rating = rating_float
                exit()

            #elif action == "nosaving":
                #upload_story = False
                #story_manager.story.upload_story = False
                #console_print("Saving turned off.")

            elif action == "help":
                instructions()

            #elif action == "save":
            #    if upload_story:
            #        id = story_manager.story.save_to_storage()
            #        console_print("Game saved.")
            #        console_print(
            #            "To load the game, type 'load' and enter the following ID: "
            #            + id
            #        )
            #    else:
            #        console_print("Saving has been turned off. Cannot save.")

            #elif action == "load":
            #    load_ID = input("What is the ID of the saved game?")
            #    result = story_manager.story.load_from_storage(load_ID)
            #    console_print("\nLoading Game...\n")
            #    console_print(result)

            #elif len(action.split(" ")) == 2 and action.split(" ")[0] == "load":
            #    load_ID = action.split(" ")[1]
            #    result = story_manager.story.load_from_storage(load_ID)
            #    console_print("\nLoading Game...\n")
            #    console_print(result)

            elif action == "print":
                print("\nPRINTING\n")
                colPrint(str(story_manager.story), colors["printStory"])

            elif action == "revert":

                if len(story_manager.story.actions) is 0:
                    colPrint("You can't go back any farther. ", colors["error"])
                    continue

                story_manager.story.actions = story_manager.story.actions[:-1]
                story_manager.story.results = story_manager.story.results[:-1]
                colPrint("Last action reverted. ", colors["loadingMessage"])
                if len(story_manager.story.results) > 0:
                    colPrint(story_manager.story.results[-1], colors["AIText"])
                else:
                    console_print(story_manager.story.story_start, colors["AIText"])
                continue

            else:
                if action == "":
                    action = ""
                    result = story_manager.act(action)
                    colPrint(result, colors["AIText"])

                elif action[0] == '"':
                    action = "You say " + action

                else:
                    action = action.strip()
                    action = action[0].lower() + action[1:]

                    if "You" not in action[:6] and "I" not in action[:6]:
                        action = "You " + action

                    if action[-1] not in [".", "?", "!"]:
                        action = action + "."

                    action = first_to_second_person(action)

                    action = "\n> " + action + "\n"

                result = "\n" + story_manager.act(action)
                if len(story_manager.story.results) >= 2:
                    similarity = get_similarity(
                        story_manager.story.results[-1], story_manager.story.results[-2]
                    )
                    if similarity > 0.9:
                        story_manager.story.actions = story_manager.story.actions[:-1]
                        story_manager.story.results = story_manager.story.results[:-1]
                        colPrint( "Woops that action caused the model to start looping. Try a different action to prevent that.", colors["error"])
                        continue

                if player_won(result):
                    colPrint(result + "\n CONGRATS YOU WIN", colors["loadingMessage"])
                    break
                elif player_died(result):
                    colPrint(result, colors["AIText"])
                    colPrint("YOU DIED. GAME OVER", colors["error"])
                    console_print("\nOptions:\n0)Start a new game\n1)\"I'm not dead yet!\" (If you didn't actually die)", colors["menu"])
                    choice = getNumberInput(2)
                    if choice == 0:
                        break
                    else:
                        colPrint("Sorry about that...where were we?", colors["menu"])
                        console_print(result, colors["AIText"])

                else:
                    colPrint(result, colors["AIText"])


play()
