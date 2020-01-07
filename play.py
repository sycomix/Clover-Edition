import traceback
from pathlib import Path
from datetime import datetime

# remove this in a few days
with open(Path('interface', 'start-message.txt'), 'r') as file_:
    print('\x1B[7m' + file_.read() + '\x1B[27m')
import gc
import torch

from getconfig import config, setting_info
from storymanager import Story
from utils import *
from gpt2generator import GPT2Generator
from interface import instructions

# add color for windows users that install colorama
#   It is not necessary to install colorama on most systems
try:
    import colorama

    colorama.init()
except ModuleNotFoundError:
    pass

logger.info("Colab detected: {}".format(in_colab()))


def get_generator():
    output(
        "\nInitializing AI Engine! (This might take a few minutes)",
        "loading-message", end="\n\n"
    )
    models = [x for x in Path('models').iterdir() if x.is_dir()]
    generator = None
    while True:
        try:
            if not models:
                raise FileNotFoundError(
                    'There are no models in the models directory! You must download a pytorch compatible model!')
            elif len(models) > 1:
                output("You have multiple models in your models folder. Please select one to load:", 'message')
                list_items([m.name for m in models] + ["(Exit)"], "menu")
                model_selection = input_number(len(models))
                if model_selection == len(models):
                    output("Exiting. ", "message")
                    exit(0)
                else:
                    model = models[model_selection]
            else:
                model = models[0]
                logger.info("Using model: " + str(model))
            generator = GPT2Generator(
                model_path=model,
                generate_num=settings.getint("generate-num"),
                temperature=settings.getfloat("temp"),
                top_k=settings.getint("top-keks"),
                top_p=settings.getfloat("top-p"),
                repetition_penalty=settings.getfloat("rep-pen"),
            )
            break
        except OSError:
            output("Model could not be loaded. Please try another model. ", "error")
            continue
        except KeyboardInterrupt:
            output("Model load cancelled. ", "error")
            exit(0)
    return generator


if not Path("prompts", "Anime").exists():
    try:
        import pastebin
    except:
        output("Continuing without downloading prompts...", "error")


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
        adjective = random.sample(adjective_action_d01, 1)[0]
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
        adjective = random.sample(adjective_action_d20, 1)[0]
        action = "You " + adjective + " " + action
    return action


def settings_menu():
    all_settings = list(setting_info.keys())
    while True:
        list_items([pad_text(k, 19) + v[0] + (" " if v[0] else "") +
                    "Default: " + str(v[1]) + " | "
                                              "Current: " + settings.get(k) for k, v in setting_info.items()] + [
                       "(Finish)"])
        i = input_number(len(all_settings), default=-1)
        if i == len(all_settings):
            output("Done editing settings. ", "menu")
            return
        else:
            key = all_settings[i]
            output(key + ": " + setting_info[key][0], "menu")
            output("Default: " + str(setting_info[key][1]), "menu", beg='')
            output("Current: " + str(settings[key]), "menu", beg='')
            new_value = input_line("Enter the new value: ", "query")
            if len(new_value.strip()) == 0:
                output("Invalid value; cancelling. ", "error")
                continue
            output(key + ": " + setting_info[key][0], "menu")
            output("Current: " + str(settings[key]), "menu", beg='')
            output("New: " + str(new_value), "menu", beg='')
            output("Saving an invalid option will corrupt file! ", "message")
            if input_bool("Change setting? (y/N): ", "selection-prompt"):
                settings[key] = new_value
                try:
                    with open("config.ini", "w", encoding="utf-8") as file:
                        config.write(file)
                except IOError:
                    output("Permission error! Changes will not be saved for next session.", "error")


def load_prompt(f):
    with f.open('r', encoding="utf-8") as file:
        try:
            lines = file.read().strip().split('\n')
            if len(lines) < 2:
                context = lines[0]
                prompt = ""
            elif len(lines) == 2:
                context = lines[0]
                prompt = lines[1]
            else:
                context = ' '.join(lines[0:-1])
                prompt = lines[-1]
            return context, prompt
        except IOError:
            output("Something went wrong; aborting. ", "error")
    return None, None


def new_story(generator, context, prompt, memory=None, first_result=None):
    if memory is None:
        memory = []
    context = context.strip()
    prompt = prompt.strip()
    story = Story(generator, context, memory)
    if first_result is None:
        story.act(prompt)
    else:
        story.actions.append(prompt)
        story.results.append(first_result)
    story.print_story()
    return story


def save_story(story, file_override=None, autosave=False):
    """Saves the existing story to a json file in the saves directory to be resumed later."""
    if not file_override:
        savefile = story.savefile
        while True:
            print()
            temp_savefile = input_line("Please enter a name for this save: ", "query")
            savefile = savefile if not temp_savefile or len(temp_savefile.strip()) == 0 else temp_savefile
            if not savefile or len(savefile.strip()) == 0:
                output("Please enter a valid savefile name. ", "error")
            else:
                break
        savefile = os.path.splitext(remove_prefix(savefile, "saves/").strip())[0]
        story.savefile = savefile
    else:
        savefile = file_override
    savedata = story.to_json()
    finalpath = "saves/" + savefile + ".json"
    try:
        os.makedirs(os.path.dirname(finalpath), exist_ok=True)
    except OSError:
        if not autosave:
            output("Error when creating subdirectory; aborting. ", "error")
    with open(finalpath, 'w') as f:
        try:
            f.write(savedata)
            if not autosave:
                output("Successfully saved to " + savefile, "message")
        except IOError:
            if not autosave:
                output("Unable to write to file; aborting. ", "error")


def load_story(f, gen):
    with f.open('r', encoding="utf-8") as file:
        try:
            story = Story(gen, "")
            story.savefile = os.path.splitext(file.name.strip())[0]
            story.from_json(file.read())
            return story, story.context, story.actions[-1] if len(story.actions) > 0 else ""
        except FileNotFoundError:
            output("Save file not found. ", "error")
        except IOError:
            output("Something went wrong; aborting. ", "error")
    return None, None, None


def alter_text(text):
    if use_ptoolkit():
        return edit_multiline(text).strip()

    sentences = sentence_split(text)
    while True:
        output(" ".join(sentences), 'menu')
        list_items(
            [
                "Edit a sentence.",
                "Remove a sentence.",
                "Add a sentence.",
                "Edit entire prompt.",
                "Save and finish."
            ], 'menu')
        try:
            i = input_number(4)
        except:
            continue
        if i == 0:
            while True:
                output("Choose the sentence you want to edit.", "menu")
                list_items(sentences + ["(Back)"], "menu")
                i = input_number(len(sentences), default=-1)
                if i == len(sentences):
                    break
                else:
                    output(sentences[i], 'menu')
                    res = input_line("Enter the altered sentence: ", 'menu').strip()
                    if len(res) == 0:
                        output("Invalid sentence entered: returning to previous menu. ", 'error')
                        continue
                    sentences[i] = res
        elif i == 1:
            while True:
                output("Choose the sentence you want to remove.", "menu")
                list_items(sentences + ["(Back)"], "menu")
                i = input_number(len(sentences), default=-1)
                if i == len(sentences):
                    break
                else:
                    del sentences[i]
        elif i == 2:
            while True:
                output("Choose the sentence you want to insert after.", "menu")
                list_items(["(Beginning)"] + sentences + ["(Back)"], "menu")
                maxn = len(sentences) + 1
                i = input_number(maxn, default=-1)
                if i == maxn:
                    break
                else:
                    res = input_line("Enter the new sentence: ", 'menu').strip()
                    if len(res) == 0:
                        output("Invalid sentence entered: returning to previous menu. ", 'error')
                        continue
                    sentences.insert(i, res)
        elif i == 3:
            output(" ".join(sentences), 'menu')
            res = input_line("Enter the new altered prompt: ", 'menu').strip()
            if len(res) == 0:
                output("Invalid prompt entered: returning to previous menu. ", 'error')
                continue
            sentences = sentence_split(res)
        elif i == 4:
            break
    return " ".join(sentences).strip()


def print_intro():
    print()

    with open(Path("interface", "mainTitle.txt"), "r", encoding="utf-8") as file:
        output(file.read(), "title", wrap=False, beg='')

    with open(Path("interface", "subTitle.txt"), "r", encoding="utf-8") as file:
        cols = termWidth
        for line in file:
            line = re.sub(r'\n', '', line)
            line = line[:cols]
            # fills in the graphic using reverse video mode substituted into the areas between |'s
            if use_ptoolkit():
                style = Style.from_dict({
                    'nor': ptcolors['subtitle'],
                    'rev': ptcolors['subtitle'] + ' reverse',
                })
                text = re.sub(r'\|[ _]*(\||$)', lambda x: '<rev>' + x.group(0) + '</rev>', line)
                print_formatted_text(HTML('<nor>' + text + '</nor>'), style=style)
            else:
                output(re.sub(r'\|[ _]*(\||$)', lambda x: '\x1B[7m' + x.group(0) + '\x1B[27m', line), 'subtitle',
                       wrap=False, beg='')

    output("Go to https://github.com/cloveranon/Clover-Edition/ "
           "or email cloveranon@nuke.africa for bug reports, help, and feature requests.",
           'subsubtitle')


class GameManager:

    def __init__(self, gen: GPT2Generator):
        self.generator = gen
        self.story, self.context, self.prompt = None, None, None

    def init_story(self) -> bool:
        self.story, self.context, self.prompt = None, None, None
        list_items(["Pick Prompt From File (Default if you type nothing)",
                    "Write Custom Prompt",
                    "Load a Saved Game",
                    "Change Settings"],
                   'menu')
        new_game_option = input_number(3)

        if new_game_option == 0:
            prompt_file = select_file(Path("prompts"), ".txt")
            if prompt_file:
                self.context, self.prompt = load_prompt(prompt_file)
            else:
                return False
        elif new_game_option == 1:
            with open(
                    Path("interface", "prompt-instructions.txt"), "r", encoding="utf-8"
            ) as file:
                output(file.read(), "instructions", wrap=False)
            if use_ptoolkit():
                output("Context>", "main-prompt")
                self.context = edit_multiline()
                output("Prompt>", "main-prompt")
                self.prompt = edit_multiline()
            else:
                self.context = input_line("Context> ", "main-prompt")
                self.prompt = input_line("Prompt> ", "main-prompt")
            filename = input_line("Name to save prompt as? (Leave blank for no save): ", "query")
            filename = re.sub("-$", "", re.sub("^-", "", re.sub("[^a-zA-Z0-9_-]+", "-", filename)))
            if filename != "":
                try:
                    with open(Path("prompts", filename + ".txt"), "w", encoding="utf-8") as f:
                        f.write(self.context + "\n" + self.prompt)
                except IOError:
                    output("Permission error! Unable to save custom prompt. ", "error")
        elif new_game_option == 2:
            story_file = select_file(Path("saves"), ".json")
            if story_file:
                self.story, self.context, self.prompt = load_story(story_file, self.generator)
            else:
                return False
        elif new_game_option == 3:
            settings_menu()
            return False

        if len((self.context + self.prompt).strip()) == 0:
            output("Story has no prompt or context. Please enter a valid custom prompt. ", "error")
            return False

        if self.story is None:
            auto_file = ""
            if settings.getboolean("autosave"):
                while True:
                    auto_file = input_line("Autosaving enabled. Please enter a save name: ", "query")
                    if not auto_file or len(auto_file.strip()) == 0:
                        output("Please enter a valid savefile name. ", "error")
                    else:
                        break
            instructions()
            output("Generating story...", "loading-message")
            self.story = new_story(self.generator, self.context, self.prompt)
            self.story.savefile = auto_file
        else:
            instructions()
            output("Loading story...", "loading-message")
            self.story.print_story()

        if settings.getboolean("autosave"):
            save_story(self.story, file_override=self.story.savefile, autosave=True)

        return True

    # returns true if going back to menu
    def process_cmd(self, cmd_regex) -> bool:
        action = cmd_regex.group(1).strip().lower()
        cmd_args = cmd_regex.group(2).strip().split()
        if action == "set":
            if len(cmd_args) < 2:
                output("Invalid number of arguments for set command. ", "error")
                instructions()
                return False
            if cmd_args[0] in settings:
                curr_setting_val = settings[cmd_args[0]]
                output(
                    "Current Value of {}: {}     Changing to: {}".format(
                        cmd_args[0], curr_setting_val, cmd_args[1]
                    )
                )
                output("Saving an invalid option will corrupt file! ", "error")
                if input_bool("Save setting? (y/N): ", "selection-prompt"):
                    settings[cmd_args[0]] = cmd_args[1]
                    try:
                        with open("config.ini", "w", encoding="utf-8") as f:
                            config.write(f)
                    except IOError:
                        output("Permission error! Changes will not be saved for next session.", "error")
            else:
                output("Invalid setting", "error")
                instructions()

        elif action == "settings":
            settings_menu()
            self.story.print_last()

        elif action == "menu":
            if input_bool("Do you want to save? (y/N): ", "query"):
                save_story(self.story)
            # self.story, self.context, self.prompt = None, None, None
            return True

        elif action == "restart":
            output("Restarting story...", "loading-message")
            if len((self.context + self.prompt).strip()) == 0:
                output("Story has no prompt or context. Please enter a valid prompt. ", "error")
                return False
            self.story = new_story(self.generator, self.story.context, self.prompt)

        elif action == "quit":
            if input_bool("Do you want to save? (y/N): ", "query"):
                save_story(self.story)
            exit()

        elif action == "help":
            instructions()

        elif action == "print":
            use_wrap = input_bool("Print with wrapping? (y/N): ", "query")
            use_color = input_bool("Print with colors? (y/N): ", "query")
            output("Printing story...", "message")
            self.story.print_story(wrap=use_wrap, color=use_color)

        elif action == "retry":
            if len(self.story.actions) < 2:
                output("Restarting story...", "loading-message")
                if len((self.context + self.prompt).strip()) == 0:
                    output("Story has no prompt or context. Please enter a valid prompt. ", "error")
                    return False
                self.story = new_story(self.generator, self.story.context, self.prompt)
                return False
            else:
                new_action = self.story.actions[-1]
                self.story.revert()
                result = self.story.act(new_action)
                if self.story.is_looping():
                    self.story.revert()
                    output("That action caused the model to start looping. Try something else instead. ",
                           "error")
                    return False
                self.story.print_last()

        elif action == "revert":
            if len(self.story.actions) < 2:
                output("You can't go back any farther. ", "error")
                return False
            self.story.revert()
            output("Last action reverted. ", "message")
            self.story.print_last()

        elif action == "alter":
            self.story.results[-1] = alter_text(self.story.results[-1])
            self.story.print_last()

        elif action == "context":
            self.story.context = alter_text(self.story.context)
            self.story.print_last()

        elif action == "remember":
            memory = cmd_regex.group(2).strip()
            if len(memory) > 0:
                memory = re.sub("^[Tt]hat +(.*)", "\\1", memory)
                memory = memory.strip('.')
                memory = memory.strip('!')
                memory = memory.strip('?')
                self.story.memory.append(memory[0].upper() + memory[1:] + ".")
                output("You remember " + memory + ". ", "message")
            else:
                output("Please enter something valid to remember. ", "error")

        elif action == "forget":
            while True:
                output("Select a memory to forget: ", "menu")
                list_items(self.story.memory + ["(Finish)"], "menu")
                i = input_number(len(self.story.memory), default=-1)
                if i == len(self.story.memory):
                    break
                else:
                    del self.story.memory[i]

        elif action == "save":
            save_story(self.story)

        elif action == "load":
            story_file = select_file(Path("saves"), ".json")
            if story_file:
                tstory, tcontext, tprompt = load_story(story_file, self.generator)
                if tstory:
                    output("Loading story...", "message")
                    self.story = tstory
                    self.context = tcontext
                    self.prompt = tprompt
                    self.story.print_story()
                else:
                    self.story.print_last()
            else:
                self.story.print_last()

        elif action == "summarize":
            first_result = self.story.results[-1]
            output(self.story.context, "user-text", "(YOUR SUMMARY HERE)", "message")
            output(self.story.results[-1], "ai-text")
            new_prompt = input_line("Enter the summary for the new story: ", "query")
            new_prompt = format_result(new_prompt)
            if len(new_prompt) == 0:
                output("Invalid new prompt; cancelling. ", "error")
                self.story.print_last()
                return False
            if input_bool("Do you want to save your previous story? (y/N): ", "query"):
                save_story(self.story)
            self.story = new_story(self.generator, self.context, new_prompt, memory=self.story.memory,
                                   first_result=first_result)

        else:
            output("Invalid command: " + action, "error")
        return False

    def process_action(self, action, suggested_actions=[]):
        action = format_result(action)

        story_insert_regex = re.search("^ *(?:you)? *! *(.*)$", action, flags=re.IGNORECASE)

        # If the player enters a story insert.
        if story_insert_regex:
            action = story_insert_regex.group(1)
            if not action or len(action.strip()) == 0:
                output("Invalid story insert. ", "error")
                return
            output(format_result(action), "user-text")

        # If the player enters a real action
        elif action != "":
            # Roll a die. We'll use it later if action-d20 is enabled.
            d = random.randint(1, 20)
            logger.debug("roll d20=%s", d)

            # Add the "you" if it's not prompt-toolkit
            if not settings.getboolean("prompt-toolkit"):
                action = re.sub("^ *(?:you)? *(?! *you)(.+)$", "You \\1", action, flags=re.IGNORECASE)

            sugg_action_regex = re.search(r"^ *(?:you)? *([0-9]+)$", action, flags=re.IGNORECASE)
            user_speech_regex = re.search(r"^ *you *say *([\"'].*[\"'])$", action, flags=re.IGNORECASE)
            user_action_regex = re.search(r"^ *you *(.+)$", action, flags=re.IGNORECASE)

            if sugg_action_regex:
                action = sugg_action_regex.group(1)
                if action in [str(i) for i in range(len(suggested_actions))]:
                    action = "You " + suggested_actions[int(action)].strip()

            if user_speech_regex:
                action = user_speech_regex.group(1)
                if settings.getboolean("action-d20"):
                    action = d20ify_speech(action, d)
                else:
                    action = "You say " + action

            elif user_action_regex:
                action = first_to_second_person(user_action_regex.group(1))
                if settings.getboolean("action-d20"):
                    action = d20ify_action(action, d)
                else:
                    action = "You " + action

            if action[-1] not in [".", "?", "!"]:
                action = action + "."

            # If the user enters nothing but leaves "you", treat it like an empty action (continue)
            if re.match(r"^ *you *[.?!]? *$", action, flags=re.IGNORECASE):
                action = ""

            # Prompt the user with the formatted action
            output("> " + format_result(action), "transformed-user-text")

        result = self.story.act(action)

        if settings.getboolean("autosave"):
            save_story(self.story, file_override=self.story.savefile, autosave=True)

        # Check for loops
        if self.story.is_looping():
            self.story.revert()
            output("That action caused the model to start looping. Try something else instead. ",
                   "error")

        pwon, pdied = player_won(result), player_died(result)
        # If the player won or died, ask them if they want to continue.
        if pwon or pdied:
            output(result, "ai-text")
            if pwon:
                output("YOU WON. CONGRATULATIONS", "message")
                list_items(["Start a New Game", "\"I'm not done yet!\" (If you still want to play)"])
            else:
                output("YOU DIED. GAME OVER", "message")
                list_items(["Start a New Game", "\"I'm not dead yet!\" (If you didn't actually die)"])
            choice = input_number(1)
            if choice == 0:
                return True
            else:
                output("Sorry about that...where were we?", "query")

        # Output the AI's result.
        output(result, "ai-text")

    def play_story(self):
        if not self.init_story():  # Failed init
            return

        while True:
            # Generate suggested actions
            act_alts = settings.getint("action-sugg")
            suggested_actions = []
            if act_alts > 0:
                # TODO change this to two messages for different colors
                output("Suggested actions:", "selection-value")
                action_suggestion_lines = 2
                for i in range(act_alts):
                    suggested_action = self.story.get_suggestion()
                    if len(suggested_action.strip()) > 0:
                        j = len(suggested_actions)
                        suggested_actions.append(suggested_action)
                        suggestion = "{}) {}".format(j, suggested_action)
                        action_suggestion_lines += \
                            output(suggestion, "selection-value", beg='' if i != 0 else None)

            bell()
            print()

            if use_ptoolkit():
                action = input_line("> ", "main-prompt", default="%s" % "You ")
            else:
                action = input_line("> You ", "main-prompt")

            # Clear suggestions and user input
            if act_alts and not IN_COLAB:
                clear_lines(action_suggestion_lines + 2)

            # Users can type in "/command", or "You /command" if prompt_toolkit is on and they left the "You" in
            cmd_regex = re.search(r"^(?: *you *)?/([^ ]+) *(.*)$", action, flags=re.IGNORECASE)

            # If this is a command
            if cmd_regex:
                if self.process_cmd(cmd_regex):  # Go back to the menu
                    return

            # Otherwise this is just a normal action.
            else:
                if self.process_action(action, suggested_actions):  # End of story
                    return


# This is here for rapid development, without reloading the model. You import play into a jupyternotebook with autoreload
if __name__ == "__main__":
    with open(Path("interface", "clover"), "r", encoding="utf-8") as file_:
        print(file_.read())
    try:
        gm = GameManager(get_generator())
        while True:
            # May be needed to avoid out of mem
            gc.collect()
            torch.cuda.empty_cache()
            print_intro()
            gm.play_story()
    except Exception as e:
        traceback.print_exc()
        output("A fatal error has occurred. ", "error")
        if gm and gm.story:
            save_story(gm.story, file_override=datetime.now().strftime("crashes/%d-%m-%Y_%H%M%S"))
        exit(1)
