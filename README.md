# AIDungeon2
## Clover Edition
### Coming: Soon.

In 2016, Donald Trump ran for president on a campaign of Making Anime Real. Four years later this promise is finally being fullfilled. Behold AIDungeon(no space): Clover Edition. The only video game where you can truly Do Anything:

![img](https://i.4cdn.org/v/1576564400002.png)

--insert screenshots here--

A fork of AIDungeon2.


#### Features:
------------------------

* Complete rewrite of the user interface
 * Color text output
 * Console Bell when AI finishes
 * Much improved prompt selection
 * Ability to save custom prompts
* A much larger library of fan made starting prompts
* Better config file
* Eventually hope to improve the AI itself, but this will take some time

#### Installation Instructions:
------------------------

--insert colab instructions/guide here--

To play the game locally, it is recommended that you have an nVidia GPU with 12 GB or more of memory, and CUDA installed. If you do not have such a GPU, each turn can take about a minute.

Windows Installer is hopefully coming someday. I'm not 100% sure how to do it. In the meantime you can manually install pretty easily:

Install python (version 3.7 or lower), tensorflow (1.14 or possibly 1.15 are known to work), numpy, and regex (e.g. `pip install numpy` (or `pip3`) from the command line, after installing python. Windows users may need to add it to their PATH. Look up how to do these things if you don't know, it's not too hard). Windows users may want to install another module called "colorama", if it is not already installed. See color support section. Then:
```
git clone "https://github.com/cloveranon/Clover-Edition/"
cd Clover-Edition
python play.py
```
(If that doesn't work try `python3` instead of python. This also assumes git is installed, but you can download a zip file from github and extract it yourself if you don't want to install git.)
(Tell me if you have a problem installing regex. Any version will work so far as I know. I want to remove it. It is used only twice in the code to do something that can be trivially done with pythons built in regular expressions.)

##### Color support on Windows (All methods untested. Please report if they do or do not work.):

* Install a python package called `colorama` and it should work. This may already be installed by pip. Which I believe is installed automatically with python. Tell me if color works out of the box on windows now.
* Install a windows program called "ansi.sys"
* Windows 10 users can edit a registry key (look up `Registry Editor`) at `HKEY_CURRENT_USER\Console\VirtualTerminalLevel` to `1` to permanently enable color support
* user a bat program to enable the `ENABLE_VIRTUAL_TERMINAL_PROCESSING` flag via the `SetConsoleMode` API (not sure what the exact .bat command would be), then run the python script. (If someone figures this out I can put it in the repo and windows users can just run it without doing anything.)
* use the new "Windows Terminal" which allegedly supports color by default and is in beta. You currently have to install it from the windows store until it is officially released

#### Datasets and retraining the AI
---------------

I threw together a quick page of some tips [here](DATASETS.md). I plan to throw any links to interesting datasets or guides for training and finetuing the AI there.

#### Community
------------------------

See that github issues page? Post any questions, requests, or problems there if you are willing to create a github account. Unless MicroAndSoft deletes us.
Otherwise see:

* **Website**: [4chan Discussion](https://boards.4chan.org/search#/aidungeon%20OR%20%22ai%20dungeon%22)
* **Email**: cloveranon@nuke.africa


#### Contributing
------------------------
Contributions are more than welcome. You can fork the thing and send a  [pull request](https://help.github.com/articles/using-pull-requests/) from your fork. Or you can possibly just edit the files from the github page if it lets you. If not fork the thing and try to edit your fork and submit it back.
