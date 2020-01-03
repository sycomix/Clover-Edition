from pathlib import Path
#remove this in a few days
with open(Path('interface', 'start-message.txt'), 'r') as file:
    print('\x1B[7m'+file.read()+'\x1B[27m')
import gc
import random
import torch
import textwrap
import sys
from random import shuffle

from getconfig import config, logger
#from story.story_manager import *
from storymanager import Story
from utils import *
from gpt2generator import GPT2Generator
from interface import instructions


# TODO: Move all these utilty functions to seperate utily file

# add color for windows users that install colorama
#   It is not necessary to install colorama on most systems
try:
    import colorama
    colorama.init()
except ModuleNotFoundError:
    pass

IN_COLAB = in_colab()
logger.info("Colab detected: {}".format(IN_COLAB))
IN_COLAB = IN_COLAB or settings.getboolean('colab-mode') 
if IN_COLAB:
    logger.warning("Colab mode enabled, disabling line clearing and readline to avoid colab bugs.")
else:
    try:
        import readline
        logger.info('readline has been imported. This enables a number of editting features but may cause bugs for colab users.')
    except ModuleNotFoundError:
        pass

def selectFile(p=Path("prompts")):
    if p.is_dir():
        files = [x for x in p.iterdir()]
        #TODO: make this a config option (although really it should be random)
        shuffle(files)
        for n in range(len(files)):
            output(
                "{}: {}".format(n, re.sub(r"\.txt$", "", files[n].name)), colors["menu"]
            )
        return selectFile(files[input_number(len(files) - 1)])
    else:
        with p.open("r", encoding="utf-8") as file:
            line1 = file.readline()
            rest = file.read()
        return (line1, rest)


def getGenerator():
    output(
        "\nInitializing AI Engine! (This might take a few minutes)\n",
        colors["loading-message"],
    )
    models=[x for x in Path('models').iterdir() if x.is_dir()]
    if not models:
        raise FileNotFoundError('There are no models in the models directory! You must download a pytorch compatible model!')
    elif len(models) > 1:
        output("You have multiple models in your models folder. Please select one to load:", colors['message'])
        for n, model_path in enumerate(models):
            output("{}: {}".format(n, model_path.name), colors['menu'])
        
        model=models[input_number(len(models) - 1)]
    else:
        model=models[0]
        logger.info("Using model: "+str(model))
    return GPT2Generator(
        model_path=model,
        generate_num=settings.getint("generate-num"),
        temperature=settings.getfloat("temp"),
        top_k=settings.getint("top-keks"),
        top_p=settings.getfloat("top-p"),
        repetition_penalty=settings.getfloat("rep-pen"),
    )


if not Path("prompts", "Anime").exists():
    try:
        import pastebin
    except:
        #temporary fix "e is not defined"
        #logger.warning("Failed to scrape pastebin: %e", e)
        output(
            "Failed to scrape pastebin, possible connection issue.\nTry again later. Continuing without downloading prompts...",
            colors["error"],
        )


#class AIPlayer:
    #def __init__(self, story):
        #self.story = story

    #def get_action(self):
        # While we want the story to be on track, but not to on track that it loops
        # the actions can be quite random, and this helps inject some user curated randomness
        # and prevent loops. So lets make the actions quite random, and prevent duplicates while we are at it

        # what to feed to model?
        #mem_ind = random.randint(1, 6) # How many steps to include
        #sample = random.randint(0, 1) # Random steps from history?
        #include_prompt = random.randint(0, 1) # Include the initial promts
        #predicates = ['You try to ', 'You say "', 'You start to ', '"']  # The model has to continue from here
        
        #predicate = random.sample(predicates, 1)[0]
        #action_prompt = self.story_manager.story_context(
        #    mem_ind,
        #    sample,
        #    include_prompt
        #)
        #action_prompt[-1] = action_prompt[-1].strip() + "\n> "+predicate
        #print(action_prompt)

        #result_raw = self.story_manager.generator.generate(
        #    action_prompt,
        #    self.story_manager.prompt,
        #    generate_num=settings.getint("action-generate-num"),
        #    temperature=settings.getfloat("action-temp"),
        #    stop_tokens=self.story_manager.generator.tokenizer.encode(["<|endoftext|>", "\n", ">"])
        #    # stop_tokens=self.generator.tokenizer.encode(['>', '<|endoftext|>'])
        #)
        #logger.debug("get_action (mem_ind=%s, sample=%s, include_prompt=%s, predicate=`%r`) -> %r", mem_ind, sample, include_prompt, predicate, result_raw)
        #result = predicate + result_raw.lstrip()
        #result = clean_suggested_action(
        #    result, min_length=settings.getint("action-min-length")
        #)
        # Sometimes the suggestion start with "You" we will add that on later anyway so remove it here
        #result = re.sub("^ ?[Yy]ou try to ?", "You ", result)
        #result = re.sub("^ ?[Yy]ou start to ?", "You ", result)
        #result = re.sub("^ ?[Yy]ou say \"", "\"", result)
        #result = re.sub("^ ?[Yy]ou ?", "", result)
        #return result
        #return self.story.getSuggestion()

def d20ify_speech(action, d):
    adjectives_say_d01 = [
        "mumble",
        "prattle",
        "incoherently say",
        "whine",
        "ramble",
        "wheeze",
    ]
    adjectives_say_d20 = [
        "successfully",
        "persuasively",
        "expertly",
        "conclusively",
        "dramatically",
        "adroitly",
        "aptly",
    ]
    if d == 1:
        adjective = random.sample(adjectives_say_d01, 1)[0]
        action = "You " + adjective + " " + action
    elif d == 20:
        adjective = random.sample(adjectives_say_d20, 1)[0]
        action = "You " + adjective + " say " + action
    else:
        action = "You say " + action
    return action

def d20ify_action(action, d):
    adjective_action_d01 = [
        "disastrously",
        "incompetently",
        "dangerously",
        "stupidly",
        "horribly",
        "miserably",
        "sadly",
    ]
    adjective_action_d20 = [
        "successfully",
        "expertly",
        "conclusively",
        "adroitly",
        "aptly",
        "masterfully",
    ]
    if d == 1:
        adjective = random.sample(adjective_action_d01, 1)[
            0
        ]
        action = "You " + adjective + " fail to " + action
    elif d < 5:
        action = "You attempt to " + action
    elif d < 10:
        action = "You try to " + action
    elif d < 15:
        action = "You start to " + action
    elif d < 20:
        action = "You " + action
    else:
        adjective = random.sample(adjective_action_d20, 1)[
            0
        ]
        action = "You " + adjective + " " + action
    return action

def newStory(generator, prompt, context):
    story = Story(generator, prompt)
    result = format_result(prompt + context)
    first_result = format_result(story.act(context)[0])
    output(result, colors['user-text'], first_result, colors['ai-text'], end='\n\n')
    return story

alphabets= "([A-Za-z])"
prefixes = "(Mr|St|Mrs|Ms|Dr)[.]"
suffixes = "(Inc|Ltd|Jr|Sr|Co)"
starters = "(Mr|Mrs|Ms|Dr|He\s|She\s|It\s|They\s|Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"
acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
websites = "[.](com|ca|gg|tv|co|net|org|io|gov)"

def splitIntoSentences(text):
    text = " " + text + "  "
    text = text.replace("...","<3elp><stop>")
    text = text.replace("..","<2elp><stop>")
    text = text.replace("\n"," ")
    text = re.sub(prefixes,"\\1<prd>",text)
    text = re.sub(websites,"<prd>\\1",text)
    if "Ph.D" in text: text = text.replace("Ph.D.","Ph<prd>D<prd>")
    text = re.sub("\s" + alphabets + "[.] "," \\1<prd> ",text)
    text = re.sub(acronyms+" "+starters,"\\1<stop> \\2",text)
    text = re.sub(alphabets + "[.]" + alphabets + "[.]" + alphabets + "[.]","\\1<prd>\\2<prd>\\3<prd>",text)
    text = re.sub(alphabets + "[.]" + alphabets + "[.]","\\1<prd>\\2<prd>",text)
    text = re.sub(" "+suffixes+"[.] "+starters," \\1<stop> \\2",text)
    text = re.sub(" "+suffixes+"[.]"," \\1<prd>",text)
    text = re.sub(" " + alphabets + "[.]"," \\1<prd>",text)
    text = text.replace(".",".<stop>")
    text = text.replace("?","?<stop>")
    text = text.replace("!","!<stop>")
    text = text.replace(".<stop>\"", ".\"<stop>")
    text = text.replace("?<stop>\"", "?\"<stop>")
    text = text.replace("!<stop>\"", "!\"<stop>")
    text = text.replace("<3elp><stop>\"", "<3elp>\"<stop>")
    text = text.replace("<2elp><stop>\"", "<2elp>\"<stop>")
    text = text.replace("<prd>",".")
    text = text.replace("<3elp>","...")
    text = text.replace("<2elp>","..")
    sentences = text.split("<stop>")
    sentences = [s.strip() for s in sentences]
    if sentences[-1] == "":
        sentences = sentences[:-1]
    return sentences

def listSentences(sentences, start=0):
    i = start
    for s in sentences:
        output(str(i) + ") " + s, colors['menu'])
        i += 1
    output(str(i) + ") (Back)", colors['menu'])

def alterText(text):
    sentences = splitIntoSentences(text)
    while True:
        output("\n" + " ".join(sentences) + "\n", colors['menu'])
        output("\n0) Edit a sentence.\n1) Remove a sentence.\n2) Add a sentence.\n3) Edit entire prompt.\n4) Save and finish.", colors['menu'], wrap=False)
        try:
            i = input_number(4)
        except:
            continue
        if i == 0:
            while True:
                output("\nChoose the sentence you want to edit.", colors["menu"])
                listSentences(sentences)
                i = input_number(len(sentences))
                if i == len(sentences):
                    break
                else:
                    output("\n" + sentences[i], colors['menu'])
                    res = input_line("\nEnter the altered sentence: ", colors['menu']).strip()
                    if len(res) == 0:
                        output("Invalid sentence entered: returning to previous menu. ", colors['error'])
                        continue
                    sentences[i] = res
        elif i == 1:
            while True:
                output("\nChoose the sentence you want to remove.", colors["menu"])
                listSentences(sentences)
                i = input_number(len(sentences))
                if i == len(sentences):
                    break
                else:
                    del sentences[i]
        elif i == 2:
            while True:
                output("\nChoose the sentence you want to insert after.", colors["menu"])
                output("0) (Beginning)", colors['menu'])
                listSentences(sentences, start=1)
                max = len(sentences)+1
                i = input_number(max)
                if i == max:
                    break
                else:
                    res = input_line("\nEnter the new sentence: ", colors['menu']).strip()
                    if len(res) == 0:
                        output("Invalid sentence entered: returning to previous menu. ", colors['error'])
                        continue
                    sentences.insert(i, res)
        elif i == 3:
            output("\n" + " ".join(sentences), colors['menu'])
            res = input_line("\nEnter the new altered prompt: ", colors['menu']).strip()
            if len(res) == 0:
                output("Invalid prompt entered: returning to previous menu. ", colors['error'])
                continue
            text = res
            sentences = splitIntoSentences(res)
        elif i == 4:
            break
    return " ".join(sentences).strip()

def play(generator):
    print("\n")

    with open(Path("interface", "mainTitle.txt"), "r", encoding="utf-8") as file:
        output(file.read(), colors["title"], wrap=False)

    with open(Path("interface", "subTitle.txt"), "r", encoding="utf-8") as file:
        cols = termWidth
        for line in file:
            line=re.sub(r'\n', '', line)
            line=line[:cols]
            #fills in the graphic using reverse video mode substituted into the areas between |'s
            output(re.sub(r'\|[ _]*(\||$)', lambda x: '\x1B[7m' + x.group(0) + '\x1B[27m', line), colors['subtitle'], wrap=False)

    print()
    output("Go to https://github.com/cloveranon/Clover-Edition/ or email cloveranon@nuke.africa for bug reports, help, and feature requests.", colors['subsubtitle'])

    while True:
        # May be needed to avoid out of mem
        gc.collect()
        torch.cuda.empty_cache()

        print("\n\n")

        output("0: Pick Prompt From File (Default if you type nothing)\n1: Write Custom Prompt", colors['menu'])

        if input_number(1) == 1:
            with open(
                Path("interface", "prompt-instructions.txt"), "r", encoding="utf-8"
            ) as file:
                output(file.read(), colors["instructions"], wrap=False)
            prompt = input_line("Prompt>", colors["main-prompt"], colors["user-text"])
            context = input_line("Context>", colors["main-prompt"], colors["user-text"])
            filename = input_line(
                "Name to save prompt as? (Leave blank for no save): ",
                colors["query"],
                colors["user-text"],
            )
            filename = re.sub(
                "-$", "", re.sub("^-", "", re.sub("[^a-zA-Z0-9_-]+", "-", filename))
            )
            if filename != "":
                with open(
                    Path("prompts", filename + ".txt"), "w", encoding="utf-8"
                ) as f:
                    f.write(context + "\n" + prompt)
        else:
            prompt, context = selectFile()

        if len((prompt+context).strip()) == 0:
            output("Story has no prompt or context. Please enter a valid custom prompt. ", colors["error"])
            continue

        instructions()
        print()
        output("Generating story...", colors["loading-message"])
        story = newStory(generator, prompt, context)

        while True:
            # Generate suggested actions
            act_alts = settings.getint("action-sugg")
            if act_alts > 0:

                # TODO change this to two messages for different colors
                suggested_actions = []
                output("\nSuggested actions:", colors["selection-value"])
                action_suggestion_lines = 2
                for i in range(act_alts):
                    suggested_action = story.getSuggestion()
                    if len(suggested_action.strip()) > 0:
                        j = len(suggested_actions)
                        suggested_actions.append(suggested_action)
                        suggestion = "{}> {}".format(j, suggested_action)
                        action_suggestion_lines += output(suggestion, colors["selection-value"])
                print()

            bell()
            action = input_line("> You ", colors["main-prompt"], colors["user-text"])

            # Clear suggestions and user input
            if act_alts > 0:
                action_suggestion_lines += 2
                if not IN_COLAB:
                    clear_lines(action_suggestion_lines)

                    # Show user input again
                    # colPrint("\n> " + action.rstrip(), colors["user-text"], end="")

            cmdRegex = re.search("^/([^ ]+) *(.*)$", action)

            # If this is a command
            if cmdRegex:
                action = cmdRegex.group(1)
                cmdArgs = cmdRegex.group(2).strip().split()
                if action == "set":
                    if len(cmdArgs) < 2:
                        output("Invalid number of arguments for set command.\n", colors["error"])
                        instructions()
                        continue
                    if cmdArgs[0] in settings:
                        currentSettingValue = settings[cmdArgs[0]]
                        output(
                            "Current Value of {}: {}     Changing to: {}".format(
                                cmdArgs[0], currentSettingValue, cmdArgs[1]
                            )
                        )
                        settings[cmdArgs[0]] = cmdArgs[1]
                        output("Save config file?", colors["query"])
                        output(
                            "Saving an invalid option will corrupt file!", colors["error"]
                        )
                        if (
                            input_line(
                                "y/n? >",
                                colors["selection-prompt"],
                                colors["selection-value"],
                            )
                            == "y"
                        ):
                            with open("config.ini", "w", encoding="utf-8") as file:
                                config.write(file)
                    else:
                        output("Invalid setting", colors["error"])
                        instructions()

                elif action == "menu":
                    break

                elif action == "restart":
                    print()
                    output("Restarting story...", colors["loading-message"])
                    if len((prompt+context).strip()) == 0:
                        output("Story has no prompt or context. Please enter a valid prompt. ", colors["error"])
                        continue
                    story = newStory(generator, story.prompt, context)

                elif action == "quit":
                    exit()

                elif action == "help":
                    instructions()

                elif action == "print":
                    print("\nPRINTING\n")
                    #TODO colorize printed story
                    output(str(story), colors["print-story"])

                elif action == "retry":
                    if len(story.story) == 1:
                        print()
                        output("Restarting story...", colors["loading-message"])
                        if len((prompt+context).strip()) == 0:
                            output("Story has no prompt or context. Please enter a valid prompt. ", colors["error"])
                            continue
                        story = newStory(generator, story.prompt, context)
                        continue
                    else:
                        newaction = story.story[-1][0]
                    output(newaction, colors['user-text'], end='')
                    story.story=story.story[:-1]
                    result = "\n" + story.act(newaction)[0]
                    if len(story.story) >= 2:
                        similarity = get_similarity(result, story.story[-2][1][0])
                        if similarity > 0.9:
                            story.story = story.story[:-1]
                            output(
                                "Woops that action caused the model to start looping. Try a different action to prevent that.",
                                colors["error"],
                            )
                            continue
                    output(result, colors["ai-text"])
                    continue

                elif action == "revert":
                    if len(story.story) == 1:
                        output("You can't go back any farther. ", colors["error"])
                        continue
                    story.story=story.story[:-1]
                    output("Last action reverted. ", colors["message"])
                    if len(story.story) < 2:
                        output(story.prompt, colors["ai-text"])
                    output(story.story[-1][1][0], colors["ai-text"])
                    continue

                elif action == "alter":
                    story.story[-1][1][0] = alterText(story.story[-1][1][0])
                    if len(story.story) < 2:
                        output(story.prompt, colors["ai-text"])
                    else:
                        output("\n" + story.story[-1][0] + "\n", colors["transformed-user-text"])
                    output(story.story[-1][1][0], colors["ai-text"])

                elif action == "prompt":
                    story.prompt = alterText(story.prompt)
                    if len(story.story) < 2:
                        output(story.prompt, colors["ai-text"])
                    else:
                        output("\n" + story.story[-1][0] + "\n", colors["transformed-user-text"])
                    output(story.story[-1][1][0], colors["ai-text"])

                elif action == "remember":
                    memory = cmdRegex.group(2).strip()
                    if len(memory) > 0:
                        memory = re.sub("^[Tt]hat +(.*)", "\\1", memory)
                        memory = memory.strip('.')
                        memory = memory.strip('!')
                        memory = memory.strip('?')
                        story.longTermMemory.append(memory.capitalize() + ".")
                        output("You remember " + memory + ". ", colors["message"])
                    else:
                        output("Please enter something valid to remember. ", colors["error"])

                elif action == "forget":
                    while True:
                        i = 0
                        output("\nSelect a memory to forget: ", colors["menu"])
                        for mem in story.longTermMemory:
                            output(str(i) + ") " + mem, colors["menu"])
                            i += 1
                        output(str(i) + ") (Finish)\n", colors["menu"])
                        i = input_number(len(story.longTermMemory))
                        if i == len(story.longTermMemory):
                            break
                        else:
                            del story.longTermMemory[i]

                else:
                    output("Invalid command: " + action, colors["error"])

            # Otherwise this is just a normal action.
            else:
                if act_alts > 0:
                    # Options to select a suggestion action
                    if action in [str(i) for i in range(len(suggested_actions))]:
                        action = suggested_actions[int(action)]

                original_action=action
                action = action.strip()
                #TODO debug stuff to delete
                if action != original_action:
                    logger.debug("STRIPPED WHITE SPACE OFF ACTION %r vs %r", original_action, action)

                # Crop actions to a max length
                #action = action[:4096]

                if action != "":

                    # Roll a 20 sided dice to make things interesting
                    d = random.randint(1, 20)
                    logger.debug("roll d20=%s", d)

                    # If it says 'You say "' then it's still dialouge. Normalise it by removing `You say `, we will add again soon
                    action = re.sub("^ ?[Yy]ou say [\"']", '"', action)
                    if any(action.lstrip().startswith(t) for t in ['"', "'"]):
                        if settings.getboolean("action-d20"):
                            action = d20ify_speech(action, d)
                        else:
                            action = "You say " + action
                        logger.info("%r. %r, %r", action, any(action.lstrip().startswith(t) for t in ['"', "'"]), settings.getboolean("action-d20"))
                    else:
                        action = first_to_second_person(action)
                        if not action.lower().startswith(
                            "you "
                        ) and not action.lower().startswith("i "):
                            action = action[0].lower() + action[1:]
                            # roll a d20
                            if settings.getboolean("action-d20"):
                                action = d20ify_action(action, d)
                            else:
                                action = "You " + action

                        if action[-1] not in [".", "?", "!"]:
                            action = action + "."

                action = "\n> " + action + "\n"

                output(
                    "\n> " + action.lstrip().lstrip("> \n"),
                    colors["transformed-user-text"],
                )
                #TODO check if leading white space makes sense
                result = format_result(story.act(action)[0])

                #TODO: Replace all this nonsense
                if len(story.story) >= 2:
                    similarity = get_similarity(result, story.story[-2][1][0])
                    if similarity > 0.9:
                        story.story = story.story[:-1]
                        output(
                            "Woops that action caused the model to start looping. Try a different action to prevent that.",
                            colors["error"],
                        )
                        continue

                if player_won(result):
                    output(result + "\n CONGRATS YOU WIN", colors["message"])
                    break
                elif player_died(result):
                    output(result, colors["ai-text"])
                    output("YOU DIED. GAME OVER", colors["error"])
                    output(
                        "\nOptions:\n0)Start a new game\n1)\"I'm not dead yet!\" (If you didn't actually die)",
                        colors["menu"],
                    )
                    choice = input_number(1)
                    if choice == 0:
                        break
                    else:
                        output("Sorry about that...where were we?", colors["query"])
                output(result, colors["ai-text"])


# This is here for rapid development, without reloading the model. You import play into a jupyternotebook with autoreload
if __name__ == "__main__":
    with open(Path("interface", "clover"), "r", encoding="utf-8") as file:
        print(file.read())
    generator = getGenerator()
    play(generator)
