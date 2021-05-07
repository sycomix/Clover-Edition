# AIDungeon2 Clover Edition

A fork of AIDungeon2, now driven by huggingface's transformers repository using PyTorch GPT2.

Take a look at [AIDungeonPastes](https://aidungeonpastes.github.io/AID2-Art/) for some drawn gameplay examples.


## Features
------------------------

* Complete rewrite of the user interface
  * Colored text
  * Suggested actions
  * Console bell dings when the AI finishes
  * Much improved prompt selection
  * Ability to save custom prompts
* Half precision floating point using significantly less GPU memory
* Repetition Penalty to reduce AI looping behavior
* A much larger library of fan made starting prompts
* Challenge added with your actions not always succeeding
* A simple config file
* Lots of changes to story history sampling/truncation to hopefully stay on track with longer games
* Eventually hope to improve the AI itself, but this will take some time

## Install Instructions
------------------------

Officially we only support local installs. We encourage and recommend installing and running the game locally. However since the beginning most people have been playing it for free on Google's servers through their Colab platform. Allegedly it requires no effort to get started. Try [this link](https://colab.research.google.com/drive/1kYVhVeE6z4sUyyKDVxLGrzI4OTV43eEa) and go to the [4chan threads](https://boards.4chan.org/search#/aidungeon%20OR%20%22ai%20dungeon%22) for help and info.

To play with GPU acceleration, you need an Nvidia GPU. The original "XL" 1558M parameter model requires at least 4GB of VRAM. Smaller models may consume less. On CPU response times vary from 30 to 90 seconds on the XL 1558M model, which is slow but usable.

1. Install [Python](https://www.python.org/downloads/). The installer should install `pip` and it should add it to your `PATH` automatically. Make sure you have the relevant options selected if the installer gives you any options.
2. Install PyTorch (aka the `torch` python module.) PyTorch's installation instructions are available [here](https://pytorch.org/get-started/locally/) on their official website. You do not need the `torchvision` nor the `torchaudio` packages.
    - For Windows or Linux CUDA (Nvidia GPU support), the command will look like the following: `pip3 install torch==1.8.1+cu111 -f https://download.pytorch.org/whl/torch_stable.html`
    - For Windows or Linux with only CPU support, it will look like: `pip3 install torch==1.8.1+cpu -f https://download.pytorch.org/whl/torch_stable.html`
    - For MacOS users, you just have to: `pip3 install torch`, as the binaries don't support CUDA and you probably don't have an Nvidia GPU anyway.
3. Install Transformers version 2.3.0: `pip3 install transformers==2.3.0`
4. If you're playing on your desktop (i.e. not on Google Colab), install Prompt-Toolkit: `pip3 install prompt_toolkit`
5. Download this repo. Github has a green download button to the top right that looks like: `[⤓ Code]`. Click it then select "Download Zip". Or you can use the git command `git clone --depth=1 "https://github.com/cloveranon/Clover-Edition/"` if you have git installed.

Then you will need to download a PyTorch model and put it in the models folder:


## Models

The PyTorch version of the original AID2 model is being distributed on bittorrent:

- [Torrent File](model.torrent) 
- [Magnet Link](magnet:?xt=urn:btih:17dcfe3d12849db04a3f64070489e6ff5fc6f63f&dn=model_v5_pytorch&tr=udp%3a%2f%2ftracker.opentrackr.org%3a1337%2fannounce&tr=udp%3a%2f%2fopen.stealth.si%3a80%2fannounce&tr=udp%3a%2f%2fp4p.arenabg.com%3a1337%2fannounce&tr=udp%3a%2f%2ftracker.coppersurfer.tk%3a6969%2fannounce&tr=udp%3a%2f%2ftracker.cyberia.is%3a6969%2fannounce&tr=udp%3a%2f%2ftracker.moeking.me%3a6969%2fannounce&tr=udp%3a%2f%2f9.rarbg.me%3a2710%2fannounce&tr=udp%3a%2f%2ftracker3.itzmx.com%3a6961%2fannounce)

The original model has 1558 million parameters. It is 5.9 GB and requires >8 GB of VRAM to run normally on a GPU and >4 GB of VRAM to run at our reduced 16 bit mode.

It is possible to play on a GPU with less than 4 GB of VRAM with smaller models. Several alternative models with only 774 million parameters can be found here: https://mega.nz/folder/4e5kRCIB#v7q0ItVjhhGcIqfZOZy9yA

Once downloaded, your model folder should look like this:
```
    ./models
    └── <MODEL-NAME>
        ├── config.json
        ├── merges.txt
        ├── pytorch_model.bin
        └── vocab.json
```

## Playing

Enter the folder and run `play.py` with Python.

- Windows: `py play.py`
- Linux: `python play.py`

## Color support on Windows

Install [Windows Terminal](https://aka.ms/terminal)(recommended) or [cmder](https://cmder.net/) and use that as your terminal.


## Troubleshooting for Linux

* If pip commands fail because of an unsupported default Python version, try it with
`[supported_Python_version] -m pip install -r requirements.txt` where `[supported_Python_version]` is replaced with a supported Python version (they might be 3.5 to 3.7.6 but don't quote me on that).


## Datasets and Finetuning the AI
---------------

I threw together a quick page of some tips [here](DATASETS.md). I plan to throw any links to interesting datasets or guides for training and finetuing the AI there. Please send me anything interesting.

Fine tunning is not currently a push button thing and requires some minimal technical ability. Most people are using the program gpt-simple. You may have more luck with the much more advanced [Huggingface-Transformers](https://github.com/huggingface/transformers) program that we use to power Clover-Edition. [This](https://huggingface.co/transformers/examples.html#language-model-fine-tuning) seems to be their documentation on fine-tuning.

Anon says: "Here's an ipynb you can train new models with using the transformers lib that clover edition uses directly, rather than having to convert it: https://0x0.st/zDRC.ipynb "


## Converting Tensorflow model to Pytorch
----------------

I have made the [convert_gpt2_model.py](convert_gpt2_model.py) script an idiot proof simple way of quickly converting tensorflow models to pytorch models. Just run it on the folder containing a tensorflow model and you will get a pytorch model. You can use the --full flag to get a full 32bit model, but do try 16bit models as they will be potentially half the size for the same accuracy.

See the [test-models.py](test-models.py) script to test the accuracy of 16 bit mode if you doubt the chad 16BIT models. My tests were well within expectations.


## Community
------------------------

See that github issues page? Post any questions, requests, or problems there if you are willing to create a github account. Unless MicroAndSoft deletes us.
Otherwise see:

* **Website**: [4chan Discussion](https://boards.4chan.org/search#/aidungeon%20OR%20%22ai%20dungeon%22)
* **Email**: cloveranon@nuke.africa


## Contributing
------------------------
Contributions are more than welcome. You can fork the thing and send a  [pull request](https://help.github.com/articles/using-pull-requests/) from your fork. Or you can possibly just edit the files from the github page if it lets you. If not fork the thing and try to edit your fork and submit it back.