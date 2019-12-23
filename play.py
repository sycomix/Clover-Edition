import gc
import textwrap
from pathlib import Path
from random import shuffle
from shutil import get_terminal_size

from getconfig import settings, colors, logger
from story.story_manager import *
from story.utils import *
from gpt2generator import GPT2Generator


#TODO: Move all these utilty functions to seperate utily file

#add color for windows users that install colorama
#   It is not necessary to install colorama on most systems
try:
    import colorama
    colorama.init()
except ModuleNotFoundError:
    pass

with open(Path('interface', 'clover'), 'r', encoding='utf-8') as file:
    print(file.read())


#ECMA-48 set graphics codes for the curious. Check out "man console_codes"
def colPrint(str, col='0', wrap=True):
        if wrap and settings.getint('text-wrap-width') > 1:
            str = textwrap.fill(str, settings.getint('text-wrap-width'), replace_whitespace=False)
        print("\x1B[{}m{}\x1B[{}m".format(col, str, colors["default"]))

def colInput(str, col1=colors["default"], col2=colors["default"]):
    val=input("\x1B[{}m{}\x1B[0m\x1B[{}m".format(col1,str,col1))
    print('\x1B[0m', end='')
    return val

def getNumberInput(n):
    val=colInput("Enter a number from above (default 0):", colors["selection-prompt"], colors["selection-value"])
    if val=='':
        return 0
    elif not re.match('^\d+$', val) or 0>int(val) or int(val)>n:
        colPrint("Invalid choice.", colors["error"])
        return getNumberInput(n)
    else:
        return int(val)

def selectFile(p=Path('prompts')):
    if p.is_dir():
        files=[x for x in p.iterdir()]
        shuffle(files)
        for n in range(len(files)):
            colPrint(
                    '{}: {}'.format(n, re.sub(r'\.txt$', '', files[n].name)),
                    colors["menu"])
        return selectFile(files[getNumberInput(len(files)-1)])
    else:
        with p.open('r', encoding='utf-8') as file:
            line1=file.readline()
            rest=file.read()
        return (line1, rest)

#print files done several times and probably deserves own function
def instructions():
    with open('interface/instructions.txt', 'r', encoding='utf-8') as file:
         colPrint(file.read(), colors["instructions"], False)

def getGenerator():
    colPrint(
            "\nInitializing AI Engine! (This might take a few minutes)\n",
            colors["loading-message"])
    return GPT2Generator(
            generate_num=settings.getint('generate-num'),
            temperature=settings.getfloat('temp'),
            top_k=settings.getint('top-keks'),
            top_p=settings.getfloat('top-p'),
            repetition_penalty=settings.getfloat('repetition-penalty')
        )
    
if not Path('prompts', 'Anime').exists():
    try:
        import pastebin
    except:
        logger.warning('Failed to scrape pastebin: %e', e)
        colPrint("Failed to scrape pastebin, possible connection issue.\nTry again later. Continuing without downloading prompts...", colors['error'])

class AIPlayer:
    def __init__(self, generator):
        self.generator = generator

    def get_action(self, prompt):
        result_raw = self.generator.generate_raw(
                prompt, generate_num=settings.getint('action-generate-num'), temperature=settings.getint('action-temp'))
        return clean_suggested_action(result_raw, min_length=settings.getint('action-min-length'))

    def get_actions(self, prompt):
        suggested_actions = [
                self.get_action(prompt)
                for _ in range(settings.getint('action-alternatives')) 
            ]
        logger.debug("Suggested actions before filter and dedup %s", suggested_actions)
        #remove short ones
        suggested_actions = [
                s
                for s in suggested_actions
                if len(s) > settings.getint('action-min-length')
            ]
        #remove dups
        suggested_actions = list(set(suggested_actions))
        return suggested_actions

def play():
    generator = getGenerator()
    story_manager = UnconstrainedStoryManager(generator)
    ai_player = AIPlayer(generator)
    print("\n")

    with open(Path('interface', 'mainTitle.txt'), 'r', encoding='utf-8') as file:
        colPrint(file.read(), colors['title'])

    with open(Path('interface', 'subTitle.txt'), 'r', encoding='utf-8') as file:
        cols=get_terminal_size()[0]
        for line in file:
            line=re.sub(r'\n', '', line)
            line=line[:cols]
            #fills in the graphic using reverse video mode substituted into the areas between |'s
            colPrint(re.sub(r'\|[ _]*\|', lambda x: '\x1B[7m'+x.group(0)+'\x1B[27m', line), colors["subtitle"], False)

    colPrint("Go to https://github.com/cloveranon/Clover-Edition/ or email cloveranon@nuke.africa for bug reports, help, and feature requests.", colors['subsubtitle'])

    while True:
        if story_manager.story != None:
            del story_manager.story

        print("\n\n")

        colPrint("0: Pick Prompt From File (Default if you type nothing)\n1: Write Custom Prompt", colors["menu"])

        if getNumberInput(1) == 1:
            with open(Path('interface', 'prompt-instructions.txt'), 'r', encoding='utf-8') as file:
                colPrint(file.read(), colors['instructions'], False)
            context = colInput('Context>', colors['main-prompt'], colors['user-text'])
            prompt = colInput('Prompt>', colors['main-prompt'], colors['user-text'])
            filename=colInput('Name to save prompt as? (Leave blank for no save): ', colors['query'], colors['user-text'])
            filename=re.sub('-$','',re.sub('^-', '', re.sub('[^a-zA-Z0-9_-]+', '-', filename)))
            if filename != '':
                with open(Path('prompts', filename+'.txt'), 'w', encoding='utf-8') as f: 
                    f.write(context+'\n'+prompt)
        else:
            context, prompt = selectFile()

        instructions()

        print()
        colPrint("Generating story...", colors['loading-message'])

        #TODO:seperate out AI generated part of story and print with different color
        story_manager.start_new_story(prompt, context=context)
        print("\n")
        colPrint(str(story_manager.story), colors["ai-text"])

        while True:
            #Generate suggested actions
            if settings.getint('action-alternatives') > 0:

                #TODO change this to two messages for different colors
                action_prompt = (
                        story_manager.story.results[-1]
                        if story_manager.story.results
                        else "\nWhat do you do now?"
                    ) + "\n>"
                #can this just be a for loop?
                suggested_actions = ai_player.get_actions(action_prompt)
                if len(suggested_actions):
                    suggested_actions_enum = [
                            "{}> {}\n".format(i, a) for i, a in enumerate(suggested_actions)
                        ]
                    suggested_action = "".join(suggested_actions_enum)
                    #TODO: check color
                    colPrint('Suggested actions\n' + suggested_action, colors['selection-value'])
                    print()

            if settings.getboolean('console-bell'):
                print('\x07', end='')
            action = colInput("> ", colors["main-prompt"], colors["user-text"])
            
            #TODO:Clear suggestions and user input

            setRegex = re.search('^set ([^ ]+) ([^ ]+)$', action)
            if setRegex:
                if setRegex.group(1) in settings:
                    currentSettingValue = settings[setRegex.group(1)]
                    colPrint("Current Value of {}: {}     Changing to: {}".format(setRegex.group(1), currentSettingValue, setRegex.group(2)))
                    settings[setRegex.group(1)] = setRegex.group(2)
                    colPrint('Save config file?', colors['query'])
                    colPrint('Saving an invalid option will corrupt file!', colors['error'])
                    if colInput('y/n? >', colors['selection-prompt'], colors['selection-value']) == 'y':
                        with open('config.ini', 'w', encoding='utf-8') as file:
                            config.write(file)
                else:
                    colPrint('Invalid Setting', colors['error'])
                    instructions()
            elif action == "restart":
                break
            elif action == "quit":
                exit()
            elif action == "help":
                instructions()
            elif action == "print":
                print("\nPRINTING\n")
                colPrint(str(story_manager.story), colors['print-story'])
            elif action == "revert":

                if len(story_manager.story.actions) == 0:
                    colPrint("You can't go back any farther. ", colors['error'])
                    continue

                story_manager.story.actions = story_manager.story.actions[:-1]
                story_manager.story.results = story_manager.story.results[:-1]
                colPrint("Last action reverted. ", colors["message"])
                if len(story_manager.story.results) > 0:
                    colPrint(story_manager.story.results[-1], colors["ai-text"])
                else:
                    colPrint(story_manager.story.story_start, colors["ai-text"])
                continue

            else:
                if action == "":
                    action = ""
                    result = story_manager.act(action)
                    colPrint(result, colors["ai-text"])

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
                    colPrint(result + "\n CONGRATS YOU WIN", colors["message"])
                    break
                elif player_died(result):
                    colPrint(result, colors["ai-text"])
                    colPrint("YOU DIED. GAME OVER", colors["error"])
                    colPrint("\nOptions:\n0)Start a new game\n1)\"I'm not dead yet!\" (If you didn't actually die)", colors["menu"])
                    choice = getNumberInput(1)
                    if choice == 0:
                        break
                    else:
                        colPrint("Sorry about that...where were we?", colors["query"])
                        colPrint(result, colors["ai-text"])

                else:
                    colPrint(result, colors["ai-text"])

#TODO: there's no reason for this to be enclosed in a function
play()
