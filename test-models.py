#a little script to test if 16 bit degrades accuracy of the model. Not a perfect experiment but I think it's good enough
#must be moved to the clover-edition directory or it will not run
    #I can not figure out why. According to pythons documentation, only the current directory matters, not the placement of the file
from gpt2generator import GPT2Generator
import torch
import numpy as np
import gc
from pathlib import Path

seed=0
top_p=0.5
top_k=0
temp=0.2
prompt='1234abcd'

print('\x1B[0m') #I really am addicted to color output
with open(Path('interface', 'clover', encoding='utf-8')) as file:
    print(file.read())

print('\x1B[35m')
np.random.seed(seed)
torch.cuda.manual_seed(seed)
torch.manual_seed(seed)
gen16 = GPT2Generator(dtype=torch.float16, top_k=top_k, top_p=top_p)
print('\n\x1B[34;7m'+gen16.generate_raw(prompt, temperature=temp)+'\x1B[27;35m\n')

del gen16
gc.collect()

np.random.seed(seed)
torch.cuda.manual_seed(seed)
torch.manual_seed(seed)
gen32 = GPT2Generator(dtype=torch.float32, top_k=top_k, top_p=top_p)
print('\n\x1B[34;7m'+gen32.generate_raw(prompt, temperature=temp)+'\n\x1B[0m')
print('\x1B[35m', end='')

print('\x1B[36m',end='')
print("This should print 2 identical lines if the models are identical. From the starting prompt of {}".format(prompt))
print("If they are close, then the output should be similar for awhile and then diverge.")
print("The first is running 16bit on GPU. The second running 32 bit on CPU")
print("They are both using the same random seed, {}, the same temperature={} and top_p={}".format(seed, temp, top_p))
print("They do diverge half way through the sequence at higher temperatures.")
print("So there is some difference in the models but they produce exactly the same output 99% of the time.")
print("A sequence of random characters is literally the worst case scenario and output should be more similar on typical English text.")
print('\x1B[0m',end='')
