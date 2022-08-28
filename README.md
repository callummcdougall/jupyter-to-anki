# Overview

This repo contains functions which should allow you to convert Jupyter Notebooks into Anki cards.

It also gives you the ability to add extra features, for instance:

* "Spoiler tags", like those found on LessWrong (which reveal when you hover over them)
* Input fields, which I've found especially useful for learning new programming libraries
* Cards with hints (click to reveal)

In particular, I'm pleased with the addition of input fields, which I expect will be useful to a lot of people who are learning new programming languages or libraries. You can mess around in a Jupyter Notebook, and then generate Anki cards from markdown files, like this:

<img src="https://raw.githubusercontent.com/callummcdougall/computational-thread-art/master/example_images/misc/anki-example.png" width=550>

Most of the features here already exist as Anki add-ons, but I think this will be especially useful to people because I've combined them all into a single way of generating cards, which can be done easily at the same time as you're learning. Also, there are other advantages to using something like Jupyter Notebooks rather than creating cards manually, e.g. the ability to duplicate cards easily and create slightly different versions of them, and the ability to back through your notebook and review your code and the cards you made at the same time.

You can read more about this on my personal website [here](https://www.perfectlynormal.co.uk/blog-how-i-use-anki).

# Instructions: first use

1. Install the files from this repo. The only two which matter are the Jupyter Notebook **`jupyter_to_anki_template.ipynb`** and the Python file **`jupyter_to_anki.py`**.
2. Open the notebook and run the first cell **`from jupyter_to_anki import *`**. This should import all the libraries and functions from **`jupyter_to_anki.py`**. If you get an error because one or more of these libraries is not installed, then install them (you can do this from the anaconda prompt, or from this notebook by prepending `!` to your commands, e.g. running **`!from pathlib import Path`** in a cell).
3. Install the free Anki for PC app [here](https://apps.ankiweb.net/), and login (or sign up). Note that you don't need to study Anki on your PC for this to work, the app is only necessary so you can use it to import cards.
4. The two text files in the GitHub repo are both cards, you need to import them. Do this by pressing **`File -> Import`** in the Anki app, then navigating to that directory, and selecting the Anki package. After this, you should have two new note types (**`front-back`** and **`front`**). You can check this by pressing **`Tools -> Manage Note Types`**. Once you've verified this, you can delete the two new cards you imported.
5. Find the directory called **`collections.media`**. The instructions for how to find the folder (for Mac, Windows and Linux) are [here](https://docs.ankiweb.net/files.html#:~:text=On%20Windows%2C%20the%20latest%20Anki,Anki%20in%20your%20Documents%20folder.). Once you have the path, copy it, then go into **`jupyter_to_anki.py`** and replace line 14 with **`p_media = Path("[path]")`**. Also, you can replace line 13 by filling in the path you want to write cards to (by default this will be the same folder as the notebook you're writing the cards in).
6. Run the second cell in the notebook, i.e the one containing **`read_cards(write=True, num_cells_below=2)`**.
7. Two text files should have appeared in the **`p_write`** directory, called **`one-sided`** and **`two-sided`**. You can import these cards into your Anki app, by following a similar process to the previous import. When prompted to choose import settings (separately each time), you should select the following:

    <img src="https://raw.githubusercontent.com/callummcdougall/computational-thread-art/master/example_images/misc/one-sided-settings.png" width="550"/>

    for the one-sided cards, and

    <img src="https://raw.githubusercontent.com/callummcdougall/computational-thread-art/master/example_images/misc/two-sided-settings.png" width="550"/>

    for the two-sided cards. Note that to get **`Fields separated by: Tab`**, you'll have to click on that box and type **`\t`**.
    
    (todo - remove "url")
    
8. You can preview the cards in the Anki app. If they've worked, then you're ready to start making your own this way!

# Instructions: regular use

1. Create a new Jupyter Notebook file
2. Write your Anki cards in Markdown files.
    * You can see examples of all the supported syntax in the **`jupyter_to_anki_template.ipynb`** file, also you can read the supported syntax in the section below.
    * You can convert a cell to markdown by pressing escape when you're inside it, then pressing **`M`**. To convert it back into code press **`Y`**
    * Note that you can use as many code cells as you want, and this won't be a problem when you run the function to create cards
3. You can optionally specify metadata **TAGS** by adding a markdown cell with the single line **`TAGS = ...`** (see the template notebook for an example). The tags in this cell will apply to every cell _below_ it, until you reach a cell which specifies a new tag.
4. When you're done, run the function **`read_cards`** in any of the cells. The important arguments to this function (along with their default values) are:
    * **`write=True`** - if **`True`** then this will write new cards, if `False` then this will just print out information like how many of each card type you have (useful for running final checks before you create cards)
    * **`filename="."`** - this is the file which your cards will be written to (by default this is the same directory as the notebook file)
    * **`num_cells_below=None`** - if **`None`** then every single markdown cell will be converted into an Anki card; if type **`int`** then this is the number of markdown cells below this one that you intend to convert (this is useful when you only want to convert a few new cards that you've added).
5. Running the cell with **`write=True`** will have created text files, which you can import just like you did in the **Instructions: first use** section.
    * If this cell returns an error, it's probably because one of the cards was incorrectly formatted. Instructions for how to write cards can be found in the section below - this has to be carefully stuck to, because the code is quite brittle.
    * The cards will always be organised into (up to) two text files, regardless of how many cards there are.

# Card syntax

Basically all the features this code offers for designing cards should be visible in the **`jupyter_to_anki_template.ipynb`**. They are also listed here for completeness.

Note that this code is quite fragile (since it works by parsing lines of markdown and using string formatting), so if you don't stick to these guidelines then it may well fail to run. For that reason, the simpler you make your cards, the better!

There are two types of cards: **`front-back`** (standard Anki cards, where you flip them over to see extra information) and **`front`** (where the card only has one side, but might have features like spoiler text or input fields. A card is interpreted as front-back if it has a dash **`-`** on one line (which is interpreted as a separator between the front and back of the card).

* **Spoiler text**
  * Wrap text with **`%...%`**
* **Code blocks**
  * Indenting text turns it into an inline block
* **Input fields** 
  * Wrap text with **`{{{...}}}`**
* **Images**
  * Literally just copy and paste them into markdown cells
  * Make sure each image is on its own line
* **Quote boxes**
  * **`(Q)`**, **`(A)`** and **`(E)`** stand for quote, author and end, and they separate the different parts of the quotebox
  * You can put the quote between **`(Q)`** and **`(A)`**, and the author (or source of the quote) between **`(A)`** and **`(E)`**
  * You can also omit **`(A)`** if you only want a quote (i.e. no author)
* **Bullet points or numbered lists**
  * Normal markdown syntax: use **`*`** or **`1.`** followed by a space
  * Note that the items within a list shouldn't have empty lines between them
* **Hints**
  * These go at the end of the card, separated by two dashes: **`--`**
* **Other standard markdown**: **`**...**`** for bold text, **`*...*`** or **`_..._`** for italics, **``...``** for inline code font

Every one of these features works for both front-back and front card types, even input fields (since you can have front-back cards which _also_ have input fields on the front).

A couple more notes on card syntax:
* Each line or block of text (e.g. quotebox or bullet points) should be separated from each other by an empty line
* Make sure not to mix up front/back separator **`-`** and hint separator **`--`**

# Some final notes

* I'll emphasise it once more - this code is quite brittle, and if you don't conform to the card syntax guide above then it probably won't run! If in doubt, just go back to the template notebook in this repo and compare your cards to this.
* If you run the **`read_cards`** function multiple times, then multiple text files will be created, with names like `front-01.txt`, `front-02.txt`, etc (so you don't overwrite the cards you've already made). This can get confusing, so it's recommended to only generate codes once for each notebook you're working on!
