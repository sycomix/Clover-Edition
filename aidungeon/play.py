from pathlib import Path

from .getconfig import config, setting_info
from .storymanager import Story
from .utils import *
from .gpt2generator import GPT2Generator
from .interface import instructions


def get_generator():
    output(
        "\nInitializing AI Engine! (This might take a few minutes)",
        "loading-message", end="\n\n"
    )
    models = [x for x in Path('models').iterdir() if x.is_dir()]
    generator = None
    failed_env_load = False
    while True:
        try:
            transformers_pretrained = os.environ.get("TRANSFORMERS_PRETRAINED_MODEL", False)
            if transformers_pretrained and not failed_env_load:
                # Keep it as a string, so that transformers library will load the generic model
                model = transformers_pretrained
                assert isinstance(model, str)
            else:
                # Convert to path, so that transformers library will load the model from our folder
                if not models:
                    raise FileNotFoundError(
                        'There are no models in the models directory! You must download a pytorch compatible model!')
                if os.environ.get("MODEL_FOLDER", False) and not failed_env_load:
                    model = Path("models/" + os.environ.get("MODEL_FOLDER", False))
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
                    logger.info(f"Using model: {str(model)}")
                assert isinstance(model, Path)
            generator = GPT2Generator(
                model_path=model,
                generate_num=settings.getint("generate-num"),
                temperature=settings.getfloat("temp"),
                top_k=settings.getint("top-keks"),
                top_p=settings.getfloat("top-p"),
                repetition_penalty=settings.getfloat("rep-pen"),
                repetition_penalty_range=settings.getint("rep-pen-range"),
                repetition_penalty_slope=settings.getfloat("rep-pen-slope"),
            )
            break
        except OSError:
            if len(models) == 0:
                output("You do not seem to have any models installed.", "error")
                output("Place a model in the 'models' subfolder and press enter", "error")
                input("")
                # Scan for models again
                models = [x for x in Path('models').iterdir() if x.is_dir()]
            else:
                failed_env_load = True
                output("Model could not be loaded. Please try another model. ", "error")
            continue
        except KeyboardInterrupt:
            output("Model load cancelled. ", "error")
            exit(0)
    return generator


def d20ify_speech(action, d):
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
        adjectives_say_d01 = [
            "mumble",
            "prattle",
            "incoherently say",
            "whine",
            "ramble",
            "wheeze",
        ]
        adjective = random.sample(adjectives_say_d01, 1)[0]
        action = f"You {adjective} {action}"
    elif d == 20:
        adjective = random.sample(adjectives_say_d20, 1)[0]
        action = f"You {adjective} say {action}"
    else:
        action = f"You say {action}"
    return action


def d20ify_action(action, d):
    if d == 1:
        adjective_action_d01 = [
            "disastrously",
            "incompetently",
            "dangerously",
            "stupidly",
            "horribly",
            "miserably",
            "sadly",
        ]
        adjective = random.sample(adjective_action_d01, 1)[0]
        action = f"You {adjective} fail to {action}"
    elif d < 5:
        action = f"You attempt to {action}"
    elif d < 10:
        action = f"You try to {action}"
    elif d < 15:
        action = f"You start to {action}"
    elif d < 20:
        action = f"You {action}"
    else:
        adjective_action_d20 = [
            "successfully",
            "expertly",
            "conclusively",
            "adroitly",
            "aptly",
            "masterfully",
        ]
        adjective = random.sample(adjective_action_d20, 1)[0]
        action = f"You {adjective} {action}"
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
            output(f"{key}: {setting_info[key][0]}", "menu")
            output(f"Default: {str(setting_info[key][1])}", "menu", beg='')
            output(f"Current: {str(settings[key])}", "menu", beg='')
            new_value = input_line("Enter the new value: ", "query")
            if len(new_value.strip()) == 0:
                output("Invalid value; cancelling. ", "error")
                continue
            output(f"{key}: {setting_info[key][0]}", "menu")
            output(f"Current: {str(settings[key])}", "menu", beg='')
            output(f"New: {str(new_value)}", "menu", beg='')
            output("Saving an invalid option will corrupt file! ", "message")
            if input_bool("Change setting? (y/N): ", "selection-prompt"):
                settings[key] = new_value
                try:
                    with open("config.ini", "w", encoding="utf-8") as file:
                        config.write(file)
                except IOError:
                    output("Permission error! Changes will not be saved for next session.", "error")


def load_prompt(f, format=True):
    with f.open('r', encoding="utf-8") as file:
        try:
            lines = file.read().strip().split('\n')
            prompt = "" if len(lines) < 2 else ' '.join(lines[1:])
            context = lines[0]
            if format:
                return format_result(context), format_result(prompt)
            else:
                return context, prompt
        except IOError:
            output("Something went wrong; aborting. ", "error")
    return None, None


def new_story(generator, context, prompt, memory=None, first_result=None):
    if memory is None:
        memory = []
    context = context.strip()
    prompt = prompt.strip()
    erase = 0
    if use_ptoolkit():
        erase = output(context, 'user-text', prompt, 'user-text', sep="\n\n")
    story = Story(generator, context, memory)
    if first_result is None:
        story.act(prompt)
    else:
        story.actions.append(prompt)
        story.results.append(first_result)
    clear_lines(erase)
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
    else:
        savefile = file_override
    savefile = os.path.splitext(savefile.strip())[0]
    savefile = re.sub(r"^ *saves *[/\\] *(.*) *(?:\.json)?", "\\1", savefile).strip()
    story.savefile = savefile
    savedata = story.to_json()
    finalpath = f"saves/{savefile}.json"
    try:
        os.makedirs(os.path.dirname(finalpath), exist_ok=True)
    except OSError:
        if not autosave:
            output("Error when creating subdirectory; aborting. ", "error")
    with open(finalpath, 'w') as f:
        try:
            f.write(savedata)
            if not autosave:
                output(f"Successfully saved to {savefile}", "message")
        except IOError:
            if not autosave:
                output("Unable to write to file; aborting. ", "error")


def load_story(f, gen):
    with f.open('r', encoding="utf-8") as file:
        try:
            story = Story(gen, "")
            savefile = os.path.splitext(file.name.strip())[0]
            savefile = re.sub(r"^ *saves *[/\\] *(.*) *(?:\.json)?", "\\1", savefile).strip()
            story.savefile = savefile
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


class GameManager:

    def __init__(self, gen: GPT2Generator):
        self.generator = gen
        self.story, self.context, self.prompt = None, None, None

    def init_story(self) -> bool:
        """
        Initializes the story. Called by play_story.
        :return: True if the GameManager should progress to the story, false otherwise.
        """
        self.story, self.context, self.prompt = None, None, None
        list_items(["Pick Prompt From File (Default if you type nothing)",
                    "Write Custom Prompt",
                    "Load a Saved Game",
                    "Change Settings"],
                   'menu')
        new_game_option = input_number(3)

        if new_game_option == 0:
            if prompt_file := select_file(Path("prompts"), ".txt"):
                self.context, self.prompt = load_prompt(prompt_file)
            else:
                return False
        elif new_game_option == 1:
            with open(
                    Path("interface/", "prompt-instructions.txt"), "r", encoding="utf-8"
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
                    with open(Path("prompts", f"{filename}.txt"), "w", encoding="utf-8") as f:
                        f.write(self.context + "\n" + self.prompt)
                except IOError:
                    output("Permission error! Unable to save custom prompt. ", "error")
        elif new_game_option == 2:
            if story_file := select_file(Path("saves"), ".json"):
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
    def process_command(self, cmd_regex) -> bool:
        """
        Processes an in-game command.
        :param cmd_regex: The regular expression for the command.
        :return: True if the command causes the game to exit, false otherwise.
        """
        command = cmd_regex.group(1).strip().lower()
        args = cmd_regex.group(2).strip().split()
        if command == "set":
            if len(args) < 2:
                output("Invalid number of arguments for set command. ", "error")
                instructions()
                return False
            if args[0] in settings:
                curr_setting_val = settings[args[0]]
                output(
                    f"Current Value of {args[0]}: {curr_setting_val}     Changing to: {args[1]}"
                )
                output("Saving an invalid option will corrupt file! ", "error")
                if input_bool("Save setting? (y/N): ", "selection-prompt"):
                    settings[args[0]] = args[1]
                    try:
                        with open("config.ini", "w", encoding="utf-8") as f:
                            config.write(f)
                    except IOError:
                        output("Permission error! Changes will not be saved for next session.", "error")
            else:
                output("Invalid setting", "error")
                instructions()

        elif command == "settings":
            settings_menu()
            self.story.print_last()

        elif command == "menu":
            if input_bool("Do you want to save? (y/N): ", "query"):
                save_story(self.story)
            # self.story, self.context, self.prompt = None, None, None
            return True

        elif command == "restart":
            output("Restarting story...", "loading-message")
            if len((self.context + self.prompt).strip()) == 0:
                output("Story has no prompt or context. Please enter a valid prompt. ", "error")
                return False
            self.story = new_story(self.generator, self.story.context, self.prompt)

        elif command == "quit":
            if input_bool("Do you want to save? (y/N): ", "query"):
                save_story(self.story)
            exit()

        elif command == "help":
            instructions()

        elif command == "print":
            use_wrap = input_bool("Print with wrapping? (y/N): ", "query")
            use_color = input_bool("Print with colors? (y/N): ", "query")
            output("Printing story...", "message")
            self.story.print_story(wrap=use_wrap, color=use_color)

        elif command == "retry":
            if len(self.story.actions) < 2:
                output("Restarting story...", "loading-message")
                if len((self.context + self.prompt).strip()) == 0:
                    output("Story has no prompt or context. Please enter a valid prompt. ", "error")
                    return False
                self.story = new_story(self.generator, self.story.context, self.prompt)
                return False
            else:
                output("Retrying...", "loading-message")
                new_action = self.story.actions[-1]
                self.story.revert()
                result = self.story.act(new_action)
                if self.story.is_looping():
                    self.story.revert()
                    output("That action caused the model to start looping. Try something else instead. ",
                           "error")
                    return False
                self.story.print_last()

        elif command == "revert":
            if len(self.story.actions) < 2:
                output("You can't go back any farther. ", "error")
                return False
            self.story.revert()
            output("Last action reverted. ", "message")
            self.story.print_last()

        elif command == "alter":
            self.story.results[-1] = alter_text(self.story.results[-1])
            self.story.print_last()

        elif command == "context":
            self.story.context = alter_text(self.story.context)
            self.story.print_last()

        elif command == "remember":
            memory = cmd_regex.group(2).strip()
            if len(memory) > 0:
                memory = re.sub("^[Tt]hat +(.*)", "\\1", memory)
                memory = memory.strip('.')
                memory = memory.strip('!')
                memory = memory.strip('?')
                self.story.memory.append(memory[0].upper() + memory[1:] + ".")
                output(f"You remember {memory}. ", "message")
            else:
                output("Please enter something valid to remember. ", "error")

        elif command == "memalt":
            while True:
                output("Select a memory to alter: ", "menu")
                list_items(self.story.memory + ["(Finish)"], "menu")
                i = input_number(len(self.story.memory), default=-1)
                if i == len(self.story.memory):
                    break
                self.story.memory[i] = alter_text(self.story.memory[i])
                if self.story.memory[i] == 0:
                    del self.story.memory[i]

        elif command == "memswap":
            while True:
                output("Select two memories to swap: ", "menu")
                list_items(self.story.memory + ["(Finish)"], "menu")
                i = input_number(len(self.story.memory), default=-1)
                if i == len(self.story.memory):
                    break
                j = input_number(len(self.story.memory), default=-1)
                if j == len(self.story.memory):
                    break
                else:
                    self.story.memory[i], self.story.memory[j] = self.story.memory[j], self.story.memory[i]

        elif command == "forget":
            while True:
                output("Select a memory to forget: ", "menu")
                list_items(self.story.memory + ["(Finish)"], "menu")
                i = input_number(len(self.story.memory), default=-1)
                if i == len(self.story.memory):
                    break
                else:
                    del self.story.memory[i]

        elif command == "save":
            save_story(self.story)

        elif command == "load":
            if story_file := select_file(Path("saves"), ".json"):
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

        elif command == "summarize":
            first_result = self.story.results[-1]
            output(self.story.context, "user-text", "(YOUR SUMMARY HERE)", "message")
            output(self.story.results[-1], "ai-text")
            new_prompt = input_line("Enter the summary for the new story: ", "query")
            new_prompt = new_prompt.strip()
            if len(new_prompt) == 0:
                output("Invalid new prompt; cancelling. ", "error")
                self.story.print_last()
                return False
            if input_bool("Do you want to save your previous story? (y/N): ", "query"):
                save_story(self.story)
            self.prompt = new_prompt
            self.story = new_story(self.generator, self.context, self.prompt, memory=self.story.memory,
                                   first_result=first_result)
            self.story.savefile = ""

        elif command == "altergen":
            result = alter_text(self.story.results[-1])
            self.story.results[-1] = ""
            output("Regenerating result...", "message")
            result += f' {self.story.act(result, record=False)}'
            self.story.results[-1] = result
            self.story.print_last()

        else:
            output(f"Invalid command: {command}", "error")
        return False

    def process_action(self, action, suggested_actions=[]) -> bool:
        """
        Processes an action to be submitted to the AI.
        :param action: The action being submitted to the AI.
        :param suggested_actions: The suggested actions generated (if action-sugg > 0)
        :return: True if the action ends the game, false otherwise.
        """
        action = format_input(action)

        if story_insert_regex := re.search(
            "^(?: *you +)?! *(.*)$", action, flags=re.I
        ):
            action = story_insert_regex.group(1)
            if not action or len(action.strip()) == 0:
                output("Invalid story insert. ", "error")
                return False
            output(format_result(action), "user-text")

        elif action != "":
            # Roll a die. We'll use it later if action-d20 is enabled.
            d = random.randint(1, 20)
            logger.debug("roll d20=%s", d)

            # Add the "you" if it's not prompt-toolkit
            if not use_ptoolkit():
                action = re.sub("^(?: *you +)*(.+)$", "You \\1", action, flags=re.I)

            sugg_action_regex = re.search(r"^(?: *you +)?([0-9]+)$", action, flags=re.I)
            user_speech_regex = re.search(r"^(?: *you +say +)?([\"'].*[\"'])$", action, flags=re.I)
            user_action_regex = re.search(r"^(?: *you +)(.+)$", action, flags=re.I)

            if sugg_action_regex:
                action = sugg_action_regex.group(1)
                if action in [str(i) for i in range(len(suggested_actions))]:
                    action = f"You {suggested_actions[int(action)].strip()}"

            elif user_speech_regex:
                action = user_speech_regex.group(1)
                if settings.getboolean("action-d20"):
                    action = d20ify_speech(action, d)
                else:
                    action = f"You say {action}"
                action = end_sentence(action)

            elif user_action_regex:
                action = first_to_second_person(user_action_regex.group(1))
                if settings.getboolean("action-d20"):
                    action = d20ify_action(action, d)
                else:
                    action = f"You {action}"
                action = end_sentence(action)

            # If the user enters nothing but leaves "you", treat it like an empty action (continue)
            if re.match(r"^(?: *you *)*[.?!]? *$", action, flags=re.I):
                action = ""
            else:
                # Prompt the user with the formatted action
                output(f"> {format_result(action)}", "transformed-user-text")

        if action == "":
            output("Continuing...", "message")

        result = self.story.act(action)

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
        """The main in-game loop"""
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
                        suggestion = f"{j}) {suggested_action}"
                        action_suggestion_lines += \
                                output(suggestion, "selection-value", beg='' if i != 0 else None)

            bell()
            print()

            if use_ptoolkit():
                action = input_line("> ", "main-prompt", default='You ')
            else:
                action = input_line("> You ", "main-prompt")

            # Clear suggestions and user input
            if act_alts and not in_colab():
                clear_lines(action_suggestion_lines + 2)

            if cmd_regex := re.search(
                r"^(?: *you *)?/([^ ]+) *(.*)$", action, flags=re.I
            ):
                if self.process_command(cmd_regex):  # Go back to the menu
                    return

            elif self.process_action(action, suggested_actions):  # End of story
                return

            # Autosave after every input from the user (if it's enabled)
            if settings.getboolean("autosave"):
                save_story(self.story, file_override=self.story.savefile, autosave=True)
