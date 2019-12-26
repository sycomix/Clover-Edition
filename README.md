# AIDungeon2
## Clover Edition
### Pytorch Edition

In 2016, Donald Trump ran for president on a campaign of Making Anime Real. Four years later this promise is finally being fullfilled. Behold AID2: Clover Edition. The only video game where you can truly Do Anything:

![img](https://i.4cdn.org/v/1576830028034.png)
![img](https://i.4cdn.org/v/1576564400002.png)
![img](http://i.imgur.com/NqC0lxG.png)

Also take a look at [AIDungeonPastes](https://aidungeonpastes.github.io/AID2-Art/) for some drawn gameplay examples.


A fork of AIDungeon2, now driven by huggingface's transformers repository using PyTorch GPT2.


#### Features:
------------------------

* Complete rewrite of the user interface
  * Colored text
  * Suggested actions
  * Console Bell dings when the AI finishes
  * Much improved prompt selection
  * Ability to save custom prompts
* Half precision floating point using significantly less GPU memory
* Repetition Penalty to reduce AI looping behavior
* A much larger library of fan made starting prompts
* Challenge added with your actions not always succeedeing
* A simple config file
* Lots of changes to story history sampling/truncation to hopefully stay on track with longer games
* Eventually hope to improve the AI itself, but this will take some time

#### Installation Instructions:
------------------------

Officially we only support local installs. We encourage and recommend installing and running the game locally. However since the beginning most people have been playing it for free on Google's servers through their Colab platform. Allegedly it requires no effort to get started. Try [this link](https://colab.research.google.com/github/Kornilov1/AI-Dungeon-2-Anons-modded-Versions-Colab/blob/master/Open_CYOAI_Colab.ipynb) and go to the [4chan threads](https://boards.4chan.org/search#/aidungeon%20OR%20%22ai%20dungeon%22) for help and info.

Video walkthrough of Windows install:

[![Install AI Dungeon Locally - Clover Edition w/Pytorch](images/install-video-screenshot.png)](https://www.youtube.com/watch?v=X3jd4c8rHAA "Install AI Dungeon Locally - Clover Edition w/Pytorch")

To play with GPU acceleration, you need an NVIDA GPU with CUDA installed (and possibly cuDNN, read ahead). The original "XL" 1558M parameter model requires at least 4GB of VRAM. Smaller models may consume much less. On CPU response times vary from 30 to 90 seconds on the XL 1558M model, which is slow but usable.

We would love to have an easy to use Windows Installer, but we don't know how to make one. In the meantime you can manually install pretty easily:

I should mention a program called [Anaconda](https://docs.anaconda.com/anaconda/install/) that claims to make it easy to install most of this stuff with a few commands in the terminal (although it already is easy to install most this stuff.) Including installing CUDA and cuDNN. Literally no one has tested this yet or created a guide for it. Report if it works. Otherwise:

First [install python](https://www.python.org/downloads/). Some users reported problems with python 3.8 so start with version 3.7. The installer should install `pip` and it should add it to your `PATH` automatically. Make sure you have the relevant options selected if the installer gives you any options.

Next install pytorch (aka the `torch` python module.) For GPU support pytorch requires a recent version of NVIDIA's CUDA and may require or benefit from an NVIDIA software called "cuDNN". For just CPU select "None" as your CUDA version. Pytorch's installation instructions are available [here](https://pytorch.org/get-started/locally/) on their official website. You do not need the `torchvision` package. On Windows the command should look like the following:

```
pip3 install torch -f https://download.pytorch.org/whl/torch_stable.html
```

Next install the necessary python modules: `transformers` and `pyjarowinkler`. This should be done with pip by entering a command like this:

```
pip3 install transformers pyjarowinkler
```

Windows users *may* want to install another module called "colorama". Though it may already be installed. If you see `[27m` glyphs, the color codes aren't working See the color support section.

Then to install just download this repo. Github has a download option somewhere. Or you can use the git command `git clone --depth=1 "https://github.com/cloveranon/Clover-Edition/"`

Then you will need to download a pytorch model. Put it in the models folder. Rename it to `pytorch-gpt2-xl-aid2-v5` until we support arbitrary model names. The pytorch version of the original AID2 model is being distributed by bittorrent. Please seed them if you have a seedbox or homelab:

[Torrent File](model.torrent) 

[Magnet Link](magnet:?xt=urn:btih:17dcfe3d12849db04a3f64070489e6ff5fc6f63f&dn=model_v5_pytorch&tr=udp%3a%2f%2ftracker.opentrackr.org%3a1337%2fannounce&tr=udp%3a%2f%2fopen.stealth.si%3a80%2fannounce&tr=udp%3a%2f%2fp4p.arenabg.com%3a1337%2fannounce&tr=udp%3a%2f%2ftracker.coppersurfer.tk%3a6969%2fannounce&tr=udp%3a%2f%2ftracker.cyberia.is%3a6969%2fannounce&tr=udp%3a%2f%2ftracker.moeking.me%3a6969%2fannounce&tr=udp%3a%2f%2f9.rarbg.me%3a2710%2fannounce&tr=udp%3a%2f%2ftracker3.itzmx.com%3a6961%2fannounce)

```
magnet:?xt=urn:btih:17dcfe3d12849db04a3f64070489e6ff5fc6f63f&dn=model_v5_pytorch&tr=udp%3a%2f%2ftracker.opentrackr.org%3a1337%2fannounce&tr=udp%3a%2f%2fopen.stealth.si%3a80%2fannounce&tr=udp%3a%2f%2fp4p.arenabg.com%3a1337%2fannounce&tr=udp%3a%2f%2ftracker.coppersurfer.tk%3a6969%2fannounce&tr=udp%3a%2f%2ftracker.cyberia.is%3a6969%2fannounce&tr=udp%3a%2f%2ftracker.moeking.me%3a6969%2fannounce&tr=udp%3a%2f%2f9.rarbg.me%3a2710%2fannounce&tr=udp%3a%2f%2ftracker3.itzmx.com%3a6961%2fannounce
```

Once downloaded your model folder should look like this:
```
    ./models
    └── pytorch-gpt2-xl-aid2-v5
        ├── config.json
        ├── merges.txt
        ├── pytorch_model.bin
        └── vocab.json
```

To play, just enter the folder and run "play.py" with python3. From the command line:
```
cd Clover-Edition
python3 play.py
```

##### Color support on Windows:

* Install a python package called `colorama` and it should work. This may already be installed by pip. Which I believe is installed automatically with python. Some users report this does not fix all of the color codes, especially on user input.
* Install a windows program called "ansi.sys"
* Use an alternative terminal emulator to the default **command prompt**.
  * **Powershell** generally works better than the default terminal and is already installed with Windows. But it doesn't support color by default either.
  * The new **Windows Terminal** supports color by default and is in beta. You currently have to install it from the windows store until it is officially released.
  * An anon has reported that **ConEmu** works great.
  * There are a number of other terminal emulators for windows, I think one even comes with git for windows.
* Windows 10 users can edit a registry key (look up `Registry Editor`) at `HKEY_CURRENT_USER\Console\VirtualTerminalLevel` to `1` to permanently enable color support
* Try using the Windows Subsystem for Linux.
* use a bat program to enable the `ENABLE_VIRTUAL_TERMINAL_PROCESSING` flag via the `SetConsoleMode` API (not sure what the exact .bat command would be), then run the python script. (If someone figures this out I can put it in the repo and windows users can just run it without doing anything.)

#### Datasets and Finetuning the AI
---------------

I threw together a quick page of some tips [here](DATASETS.md). I plan to throw any links to interesting datasets or guides for training and finetuing the AI there. Please send me anything interesting.

Fine tunning is not currently a push button thing and requires some minimal technical ability. Most people are using the program gpt-simple. You may have more luck with the much more advanced [Huggingface-Transformers](https://github.com/huggingface/transformers) program that we use to power Clover-Edition.

#### Converting Tensorflow model to Pytorch
----------------

See [this](https://github.com/huggingface/transformers/blob/17ea43cf985829634bd86b36b44e5410c6f83e36/docs/source/converting_tensorflow_models.rst) and checkout the script in the pytorch-scripts folder of this repo, and comments near the bottom.

#### Community
------------------------

See that github issues page? Post any questions, requests, or problems there if you are willing to create a github account. Unless MicroAndSoft deletes us.
Otherwise see:

* **Website**: [4chan Discussion](https://boards.4chan.org/search#/aidungeon%20OR%20%22ai%20dungeon%22)
* **Email**: cloveranon@nuke.africa


#### Contributing
------------------------
Contributions are more than welcome. You can fork the thing and send a  [pull request](https://help.github.com/articles/using-pull-requests/) from your fork. Or you can possibly just edit the files from the github page if it lets you. If not fork the thing and try to edit your fork and submit it back.
