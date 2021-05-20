import configparser
import torch
import gc
from os import scandir
from random import choice
from random import shuffle
from gpt2generator import GPT2Generator
from numpy.random import beta
from numpy import greater
from numpy import mean
#from numpy import std
samplesize=1024*16
config = configparser.ConfigParser()
config.read('AB.ini')
A = config['A']
B = config['B']
settings = config['All']
files=list(scandir("AB-prompts"))
def genResponses(settings, n, responses, name):
    gc.collect()
    torch.cuda.empty_cache()
    generator = GPT2Generator(
            model_path = settings['model-path'],
            dtype = torch.float16,
            max_history_tokens=settings.getint('max-history-tokens')
    )
    generator.top_p_first=settings.getboolean('top-p-first')
    for i in range(n):
        with open(choice(files)) as file:
            prompt=file.read()
        responses.append({
            'name':name,
            'prompt':prompt, 
            'output':generator.generate(
                context=prompt,
                temperature=settings.getfloat('temp'),
                top_p = settings.getfloat('top-p'),
                top_k = settings.getint('top-keks'),
                repetition_penalty=settings.getfloat('repetition-penalty')
            )
        })
    generator=None
    gc.collect()
    torch.cuda.empty_cache()


totals={'A':{'y':0, 'n':0}, 'B':{'y':0, 'n':0}}
while True:
    responses=[]
    genResponses(A, settings.getint('num-samples'), responses, 'A')
    genResponses(B, settings.getint('num-samples'), responses, 'B')
    shuffle(responses)
    for r in responses:
        print(r['prompt']+r['output'])
        while True:
            v=input('Good? y/n:')
            if v=='y' or v=='n':
                break
        totals[r['name']][v]+=1
        print(totals)
        asamp=beta(totals['A']['y']+1, totals['A']['n']+1, samplesize)
        bsamp=beta(totals['B']['y']+1, totals['B']['n']+1, samplesize)
        prob=mean(greater(asamp, bsamp))
        print("The probability that A is better than B is:", prob)
        input("press enter to continue")
