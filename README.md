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
  * Color text output
  * Suggested actions
  * Roll 20 sided dice for speech or action
  * Console Bell when AI finishes
  * Much improved prompt selection
  * Ability to save custom prompts
* A much larger library of fan made starting prompts
* Better config file
* Repetition Penalty to reduce AI looping behavior
* Half precision floating point using less GPU memory (you still need ~~11~~ ~~8~~ 4-6GB)
* Lots of changes to story history sampling/truncation to hopefully stay on track with longer games
* Eventually hope to improve the AI itself, but this will take some time

#### Installation Instructions:
------------------------

--insert colab instructions/guide here--

[![Install AI Dungeon Locally - Clover Edition w/Pytorch](images/install-video-screenshot.png)](https://www.youtube.com/watch?v=X3jd4c8rHAA "Install AI Dungeon Locally - Clover Edition w/Pytorch")

To play with GPU, you need an NVIDA GPU with >4 GB of memory (exact minimum requirements still very untested), and CUDA installed. On CPU response times vary from 30 to 90 seconds, which is slow but usable.

Windows Installer is hopefully coming someday. I'm not 100% sure how to do it. In the meantime you can manually install pretty easily:

Install python, pytorch (`torch`), and `transformers`. Windows users may need to add the location of pip and python to their `PATH` variable manually (look up how to do that, it's not that hard.) Instructions to install pytorch can be found [here](https://pytorch.org/get-started/locally/). You do not need to install the package "torchvision". On Windows, with CUDA 10 and python 3, the command should look like the following. Older versions of CUDA or CPU only are also possible with a different download, see the pytorch install link.

```
pip3 install torch -f https://download.pytorch.org/whl/torch_stable.html
```

Then install `transformers` and `pyjarowinkler`:
```
pip3 install transformers pyjarowinkler
```
That should cover all the dependencies needed to run Clover-Edition.

Windows users *may* want to install another module called "colorama". Though it may already be installed. If you see `[27m` glyphs, the color codes aren't working See  the color support section.

Then to install just download this repo. Github has a download option somewhere. Or you can use the git command `git clone "https://github.com/cloveranon/Clover-Edition/"`

Then you will need to download the model. Put it in the models folder. Rename it to `pytorch-gpt2-xl-aid2-v5` until we support arbitrary model names. The current torrent file and magnet links are here, please seed them if you have a seedbox or homelab:

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


##### Color support on Windows (All methods untested. Please report if they do or do not work.):

* Install a python package called `colorama` and it should work. This may already be installed by pip. Which I believe is installed automatically with python. Tell me if color works out of the box on windows now.
* Install a windows program called "ansi.sys"
* Windows 10 users can edit a registry key (look up `Registry Editor`) at `HKEY_CURRENT_USER\Console\VirtualTerminalLevel` to `1` to permanently enable color support
* user a bat program to enable the `ENABLE_VIRTUAL_TERMINAL_PROCESSING` flag via the `SetConsoleMode` API (not sure what the exact .bat command would be), then run the python script. (If someone figures this out I can put it in the repo and windows users can just run it without doing anything.)
* use the new "Windows Terminal" which allegedly supports color by default and is in beta. You currently have to install it from the windows store until it is officially released

#### Datasets and retraining the AI
---------------

I threw together a quick page of some tips [here](DATASETS.md). I plan to throw any links to interesting datasets or guides for training and finetuing the AI there. Please send me anything interesting.

#### Community
------------------------

See that github issues page? Post any questions, requests, or problems there if you are willing to create a github account. Unless MicroAndSoft deletes us.
Otherwise see:

* **Website**: [4chan Discussion](https://boards.4chan.org/search#/aidungeon%20OR%20%22ai%20dungeon%22)
* **Email**: cloveranon@nuke.africa


#### Contributing
------------------------
Contributions are more than welcome. You can fork the thing and send a  [pull request](https://help.github.com/articles/using-pull-requests/) from your fork. Or you can possibly just edit the files from the github page if it lets you. If not fork the thing and try to edit your fork and submit it back.
