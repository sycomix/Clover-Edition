import json
import re
from getconfig import settings, colors
from utils import output, format_result, get_similarity

class Story:
    #the initial prompt is very special.
    #We want it to be permanently in the AI's limited memory (as well as possibly other strings of text.)
    def __init__(self, generator, prompt=''):
        self.generator = generator
        self.prompt = prompt
        self.memory = []
        self.actions = []
        self.results = []
        self.savefile = None

    def act(self, action):
        assert (self.prompt.strip() + action.strip())
        assert (settings.getint('top-keks') is not None)
        self.actions.append(format_result(action))
        result = self.generator.generate(
                    self.get_story() + action,
                    self.prompt + ' '.join(self.memory),
                    temperature=settings.getfloat('temp'),
                    top_p=settings.getfloat('top-p'),
                    top_k=settings.getint('top-keks'),
                    repetition_penalty=settings.getfloat('rep-pen'))
        self.results.append(format_result(result))
        return self.results[-1]

    def print_story(self, wrap=True):
        first_result = format_result(self.actions[0] + ' ' + self.results[0])
        output(self.prompt, colors['user-text'], first_result, colors['ai-text'], wrap=wrap)
        maxactions = len(self.actions)
        maxresults = len(self.results)
        for i in range(1, max(maxactions, maxresults)):
            if i < maxactions and self.actions[i].strip() != "":
                output("> " + self.actions[i], colors['user-text'], wrap=wrap)
            if i < maxresults and self.results[i].strip() != "":
                output(self.results[i], colors['ai-text'], wrap=wrap)

    def get_story(self):
        lines = [val for pair in zip(self.actions, self.results) for val in pair]
        return '\n\n'.join(lines)

    def get_last_action_result(self):
        return self.actions[-1] + ' ' + self.results[-1]

    def revert(self):
        self.actions = self.actions[:-1]
        self.results = self.results[:-1]

    def get_suggestion(self):
        return re.sub('\n.*', '',
                self.generator.generate_raw(
                    self.get_story() + "\n\n> You",
                    self.prompt,
                    temperature=settings.getfloat('action-temp'),
                    top_p=settings.getfloat('top-p'),
                    top_k=settings.getint('top-keks'),
                    repetition_penalty=1))

    def __str__(self):
        return self.prompt + ' ' + self.get_story()

    def to_dict(self):
        res = {}
        res["temp"] = settings.getfloat('temp')
        res["top-p"] = settings.getfloat("top-p")
        res["top-keks"] = settings.getint("top-keks")
        res["rep-pen"] = settings.getfloat("rep-pen")
        res["prompt"] = self.prompt
        res["memory"] = self.memory
        res["actions"] = self.actions
        res["results"] = self.results
        return res

    def from_dict(self, d):
        settings["temp"] = str(d["temp"])
        settings["top-p"] = str(d["top-p"])
        settings["top-keks"] = str(d["top-keks"])
        settings["rep-pen"] = str(d["rep-pen"])
        self.prompt = d["prompt"]
        self.memory = d["memory"]
        self.actions = d["actions"]
        self.results = d["results"]

    def to_json(self):
        return json.dumps(self.to_dict())

    def from_json(self, j):
        self.from_dict(json.loads(j))

    def is_looping(self, threshold=0.9):
        if len(self.results) >= 2:
            similarity = get_similarity(self.results[-1], self.results[-2])
            if similarity > threshold:
                return True
        return False

#    def save()
#        file=Path('saves', self.filename)
