# Overview

This repo contains functions which should allow you to convert Jupyter Notebooks into Anki cards.

It also gives you the ability to add extra features, for instance:

* "Spoiler tags", like those found on LessWrong (which reveal when you hover over them)
* Input fields, which I've found especially useful for learning new programming libraries
* Cards with hints (click to reveal)

In particular, I'm pleased with the addition of input fields, which I expect will be useful to a lot of people who are learning new programming languages or libraries. You can mess around in a Jupyter Notebook, and then generate Anki cards from markdown files, like this:

<img src="https://raw.githubusercontent.com/callummcdougall/computational-thread-art/master/example_images/misc/anki-example.png" width=850>

Most of the features here already exist as Anki add-ons, but I think this will be especially useful to people because I've combined them all into a single way of generating cards, which can be done easily at the same time as you're learning. Also, there are other advantages to using something like Jupyter Notebooks rather than creating cards manually, for instance:

* You can duplicate cards easily and create slightly different versions of them
* You can see all your cards at once before adding them, rather than adding them one at a time
* You can go back through your notebook and review your cards alongside the rest of the Jupyter Notebook

In the near future, I plan to add the ability to use all these features when actually creating cards in the Anki interface (e.g. input fields, spoiler tags, quotes) because notebooks are less convenient when you want to just create one or two cards.

You can read more about this on my personal website [here](https://www.perfectlynormal.co.uk/blog-how-i-use-anki).

# Anki editor

All the features I've designed should be usable in the Anki editor, without downloading any files from this editor (except for the Anki deck). You'll need to download and install the Anki deck so that the right note types are created in your app. There are only three cards in this deck, and you can delete them after importing them.

Once you've done this, you then need to get [this Anki add-on](https://ankiweb.net/shared/info/1899278645). Once you install it, you should restart the Anki app, then go to **`Tools -> Add-ons`**, select the name of the add on, and click **`Config`**. This will open a large table of entries. Each one corresponds to a formatting option you can apply with a keyboard shortcut (or button on the Anki editor). You can delete every row, then add five new ones, making the table look like this:

![image](https://user-images.githubusercontent.com/45238458/187589685-11039d3b-c098-46f1-bb34-728fb26bd950.png)

You can choose whichever hotkeys you like. The most important entries are the **`Category`** (left column) and the **`class`** (third column), so make sure these are exactly right.

Once you've done this, you should be able to use these tools in your editor, when you create new cards of the same types as the ones you imported. Here is a link to a video showing how this works for a few of the different buttons.

# Jupyter

## Instructions: before use

1. Install the [Anki app](https://apps.ankiweb.net/), and log in.
2. Find the **`collections.media`** folder. This is where Anki stores all the images used in your cards. See [this link](https://docs.ankiweb.net/files.html#:~:text=On%20Windows%2C%20the%20latest%20Anki,Anki%20in%20your%20Documents%20folder.) for how to find it (the location depends on your OS).
3. Install the files from this repo: a Jupyter Notebook, a Python file, and a folder of text files.
4. Open the Python file, and replace line 13 (which defines a path **`p_media`**) by replacing the string argument with the path name of your **`collections.media`** folder. Note - use forward slashes rather than backward slashes (these are interpreted as escape characters).

## Instructions: main

The Jupyter Notebook in the repo should provide a template for how to use this function. The first cell reads:

![image](https://user-images.githubusercontent.com/45238458/187583129-d9ac52dc-fe95-4e8c-9d1f-77d0581d4dc2.png)

Let's explain each of these lines.

The first line is a simple import statement. You'll need to run this import each time you create Anki cards (you can move the Python folder to a directory in your path if that makes it easier).

The second line is what actually writes the cards, and it's the only function you'll need to run from the library. The arguments to this function are:

* **`filename`** - you should always pass the filename of the notebook you're running this function in
* **`write`** - boolean, determining whether to write cards or not (if false then it just prints info about the cards, which can be useful for checking total numbers of cards before actually writing them, or checking if there are any errors)
* **`num_cells_below`** - this has three possible values. If **`None`** (the default value), then it Ankifies every markdown cell in the notebook. If **`"all"`**, then it Ankifies every markdown cell below the one containing this function. Finally, if it is a positive integer, then that's how many markdown cells below this one are Ankified[^1].
* **`overwrite`** - if **`True`**, then any Anki decks in the current directory will be overwritten when you run this function. If **`False`** (the default value), then new Anki decks will have suffixes like `_001`, `_002` appended to them so they don't overwrite.
* **`mode`** - ignore this argument, it should always be zero

What exactly does this function do? Well, it reads in a certain number of markdown cells, converts them to Anki cards, and writes them to a **`.apkg`** file. This file will have the same name as the current notebook, with the deck name appended, plus maybe a suffix like `_001`, `_002` (see point above).

Note that the function will ignore code cells, and only count markdown cells - this means it's easy to open a notebook of code, add some markdown cells in between them and turn them into Anki cards. You can toggle a cell between markdown and code by pressing escape when you're inside the cell (or clicking to the left of the cell), and pressing **`y`** (for code) or **`m`** (for markdown).

Card **tags** and **deck** are determined by adding markdown cells starting with **`TAGS = `** or **`DECK = `**. These cells will fix the tags and deck for all markdown cells below them, so you can define more than one different tag or deck within the same notebook. You don't have to define them both in the same markdown cell; you can only change the tag or only change the deck if you want. Multiple tags are supported (separated by spaces), and so are hierarchical tags (indicated by **`::`**).

## Card types

There are three types of cards:

* **`front-back`** (standard Anki cards, where you flip them over to see extra information). A card is interpreted as **`front-back`** if it has a dash **`-`** on one line (which is interpreted as a separator between the front and back of the card).
* **`image`** (same as front-back, but when you flip it over you no longer see the front, only the back). A card is interpreted as **`image`** if it has **`-i`** on one line (which is interpreted as a separator between the front and back of the card). This kind of card is useful if you want to occlude certain parts of an image.
* **`front`** (the card only has one side, but might have features like spoiler text or input fields). This card is useful for programming syntax, or making nice-looking cloze cards (or combining the two!).

Additionally, any of these types of card can also accept **hints**. They are indicated at the end of the card, by using the **`h`** separator.

## Card syntax

The Jupyter Notebook should give you a good idea of what features are available for formatting cards. They are all listed below:

* **Spoiler text**
  * Wrap text with **`%...%`**
* **Code blocks**
  * Indenting text turns it into an inline block
* **Input fields** 
  * Wrap text with **`{{{...}}}`**
  * Note this doesn't have to be done in a code block (but ususally I combine these two)
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
  * Double indentations are not supported
* **Hints**
  * These go at the end of the card, separated by a line **`-h`**
  * Make sure not to mix this up with the front-back separator, which is just a single dash
* **Other standard markdown**: **`**...**`** for bold text, **`*...*`** or **`_..._`** for italics, **``...``** for inline code font

All these features work for all three different card types (with a couple of exceptions for **`image`** cards, e.g. since having input fields for these kinds of cards wouldn't make sense).

Each line of text (or feature in the list above, e.g. quotebox / codeblock / set of bullet points) should be separated from each other by an empty line.

Note that this code is quite fragile (since it works by parsing lines of markdown and using string formatting), so if you don't stick to these guidelines then it may well break. For that reason, the simpler you make your cards, the better! If in doubt, just go back to the template notebook in this repo and compare your cards to this.

Happy Anki-ing!

[^1]: Markdown cells with meta information (deck and tags) don't get counted in this argument. Additionally, markdown cells that start with headers (i.e. with some number of **`#`** characters) don't get converted into Anki cards and don't get counted in this argument. This is because headers are quite useful in notebooks, and I didn't want them to disrupt the function.
