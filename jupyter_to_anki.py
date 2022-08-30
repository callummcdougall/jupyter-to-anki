from __future__ import unicode_literals
from pathlib import Path
import re
from collections import defaultdict
from bs4 import BeautifulSoup
import json
import os
import base64
import hashlib
import datetime
from typing import List, Dict, OrderedDict, Tuple
import traceback

p_media = Path("C:/Users/calsm/AppData/Roaming/Anki2/User 1/collection.media")


# Add in some basic checks that might cause the model to break.
# Things like:
# 
# > Do you have an even number of (S) spoiler tags on each line?


### MISC FUNCTIONS

def get_filename_from_json_data(json_data, filetype="jpg"):
    
    return hashlib.sha256(bytes(json_data, "utf-8")).hexdigest() + "." + filetype

def get_random_seed_for_inputs(i_value, increment):
    """
    Generates a random seed for use in the Anki input field.
    
    Note that the purpose of "increment" is to make sure the same field showing up twice doesn't lead to the same random seed
    """
    
    h = hashlib.sha256(bytes(i_value + str(increment), "utf-8")).hexdigest()
    h = "".join([ch for ch in h if ch.isdigit()])
    return f"{int(h[:8]):08d}"

def get_card_type_and_hint(card) -> Tuple[str, int, int]:
    """
    Figures out whether it's a front or front-back card, based on whether it contains a `-` separator.

    Also figures out whether it's got a hint, based on whether it contains a `-h` separator.
    """

    all_separators = [c.strip() for c in card if c.strip().startswith("-")]
    assert len(all_separators) <= 2, f"There should be at most separators (lines starting with '-'), instead we found {len(all_separators)} in one of your cards.\n\nSee the documentation pages for more detail:\n\nhttps://github.com/callummcdougall/jupyter-to-anki/blob/main/README.md"
    bad_separators = [sep for sep in all_separators if sep not in ["-", "-h"]]
    assert len(bad_separators) == 0, f"The only allowed separators (lines starting with '-') are '-' (for front/back) and '-h' (for hints). Instead we found the separators {bad_separators} in one of your cards.\n\nSee the documentation pages for more detail:\n\nhttps://github.com/callummcdougall/jupyter-to-anki/blob/main/README.md"
    
    separators = [(i, c.strip()) for i, c in enumerate(card) if c.strip() in ["-", "-h"]]
    has_back = ("-" in all_separators)
    fb_separator = min([i for i, c in separators if c == "-"]) if has_back else 0
    card_type = "front-back" if fb_separator else "front"
    has_hint = ("-h" in all_separators)
    hint_separator = min([i for i, c in separators if c == "-h"]) if has_hint else 0

    return (card_type, fb_separator, hint_separator)


### HIGH-LEVEL FUNCTIONS

def read_cards(filename, write=True, num_cells_below=None):
    """
    Opens a Jupyter Notebook, reads all the cards in non-tag markdown cells, and writes them (separated by note type) to a text file
    
    INPUTS
        filename    | should be a path (either starting from C:/ or with this directory as reference point) minus the .ipynb suffix
        write       | if false, it doesn't write to a text file (only do True when you're sure you're done with the cards)
        date        | it can be either "today", a specific reference to a date, or "ignore" (to get all cells)
        sample_len  | determines how many characters to print out from the card (if zero, nothing is printed, and if "all", it's all printed)
        
    OUTPUTS
        soup                 | BeautifulSoup object, got from reading the notebook
        cells_json_dict_list | list of raw markdown cells, each one a dictionary with keys like "source" and "cell_type"
        markdown_cells_dict  | dictionary of tuples (cell, image) (where cell is raw markdown, i.e. "source"), sorted into lists and indexed by (deck, tag, url) tuples
        cards_processed_dict | dictionary of cell html, i.e. a single string with \t to separate fields, sorted into lists and indexed by card type
    """

    # get global error messages (to print at the end)
    global error_messages
    error_messages = []

    # if filename includes a stem, deal with this
    if not filename.endswith(".ipynb"):
        filename += ".ipynb"
    
    # initialises these variables so that in the event of an error they can be returned, which helps me to do bug-fixing
    soup, cells_json_dict_list = None, None
    markdown_cells_dict, cards_processed_dict = defaultdict(list), defaultdict(list)

    try:
    
        with open(filename, encoding="utf_8") as f:
            
            # read notebook, check if there are any classes in the notebook, and if so then removes them (this can fuck with the json loading)
            soup = BeautifulSoup(f, "html.parser", from_encoding="utf_8")
            soup = BeautifulSoup(soup.text, "html.parser")
            
        # get the notebook data in the form of a dictionary, and also get all the attachments
        cells_json_dict_list = json.loads(soup.decode_contents())["cells"]
        markdown_cells = [(i, cell_dict["source"]) for i, cell_dict in enumerate(cells_json_dict_list) if cell_dict["cell_type"] == "markdown"]
        code_cells = [(i, cell_dict["source"]) for i, cell_dict in enumerate(cells_json_dict_list) if cell_dict["cell_type"] == "code"]
        images = [cell_dict.get("attachments", {}) for cell_dict in cells_json_dict_list if cell_dict["cell_type"] == "markdown"]
        markdown_cells_dict = defaultdict(list)
        tags = ""

        # do some type checking of arguments
        n = num_cells_below
        assert any([n is None, n == "all", (isinstance(n, int) and n >= 1)]), f"{num_cells_below = }, this is not allowed. Expected values are `None`, 'all' or positive integer.\n\nSee the documentation pages for more detail:\n\nhttps://github.com/callummcdougall/jupyter-to-anki/blob/main/README.md"

        # find the cell that contains the function you ran, and find the next markdown cell (needed for determining which cells to Ankify)
        read_cards_cells = [i for i, c in code_cells if any("read_cards(" in line for line in c)]
        assert len(read_cards_cells) == 1, f"Expected exactly one code cell containing an instance of the `read_cards` function, instead found {len(read_cards_cells)}.\n\n. See the documentation pages for more detail:\n\nhttps://github.com/callummcdougall/jupyter-to-anki/blob/main/README.md"
        read_cards_cell = read_cards_cells[0]
        first_markdown = 0 if n is None else min([i for i, c in markdown_cells if i > read_cards_cell])
        markdown_counter = 0

        # loop through the cells and images, and sort the Anki cards into a dictionary by tag & url
        for (i, cell), images_dict in zip(markdown_cells, images):

            # update either the url, date or tag variables
            if len(cell) == 1 and any(cell[0].startswith(f"{deckstring} = ") for deckstring in ["TAGS", "tags", "Tags"]):
                tags = cell[0][7:]

            # A markdown cell is Anki iff it doesn't start w/ a header
            elif (not cell[0].startswith("#")):
                if tags == "":
                    print("Reminder - some of your cards don't have tags. You can add tags by putting a markdown cell with `TAGS = ...` before your cards.\n")
                if i >= first_markdown:
                    markdown_cells_dict[tags].append((cell, images_dict))
                    markdown_counter += 1
                    if isinstance(n, int) and markdown_counter == n:
                        break

        # get a dictionary of cards, sorted by the card type (and print out samples of the card)
        counter = 0
        print("Creating cards:\n")
        for tags, card_and_images_list in markdown_cells_dict.items():
            for card, images_dict in card_and_images_list:
                card_type, card_content = read_single_card(card, images_dict, tags)
                cards_processed_dict[card_type].append(card_content)
            print(f"\t{len(markdown_cells_dict[tags])} cards with tag '{tags}'")
        print("\nSaving cards:\n")

        # iterate through cards by card type
        for card_type, card_list in cards_processed_dict.items():

            # get a new file name for the text file
            filename_write = Path(f"./{card_type}.txt")
            counter = 0
            while filename_write.exists():
                counter += 1
                filename_write = Path(f"./{card_type}-{counter:03}.txt")

            print(f"\t{len(card_list)} card{' ' if len(card_list) == 1 else 's'} with filename '{filename_write.name}'")
                
            # write to a text file
            if write:
                with open(filename_write, "w", encoding="utf-8") as f:
                    f.write("\n".join(card_list))

        if len(error_messages) > 0:
            print("\n======== ERROR MESSAGES ========\n")
            for msg in error_messages: print(msg)
    
    except:
        error = traceback.format_exc()
        print(error)
        if "json.decoder.JSONDecodeError: Expecting ',' delimiter" in error:
            print("There was some kind of error when the notebook was opened. Try restarting kernel, clearing all output, and saving, then running the cell again.")
            
def read_single_card(card: List[str], images_dict: Dict, tags: str) -> Tuple[str, str]:
    
    card_type, fb_separator, hint_separator = get_card_type_and_hint(card)
    
    # if card has a hint, then read it
    hint = read_single_field(card[hint_separator+2:], images_dict) if hint_separator else ""

    # get front-back (or just front)
    if card_type == "front-back":
        front = read_single_field(card[:fb_separator-1], images_dict)
        back = read_single_field(card[fb_separator+2:hint_separator-1 if hint_separator else None], images_dict)
        fields = [front, back, hint, tags]
    else:
        front = read_single_field(card[:hint_separator-1 if hint_separator else None], images_dict)
        fields = [front, hint, tags]
        
    # return the fields, ready for Anki
    return (card_type, "\t".join(fields))


def read_single_field(field: List, images_dict: Dict) -> str:

    # general convention: my end indices are the last line on which the thing appears, so the actual slices are often [start_idx : end_idx + 1]
    indices_dict = {}
    
    # remove the line breaks at the end of lines
    field = [line.rstrip() for line in field]
    
    # ============== GET ALL INDICES OF CODEBLOCKS AND STUFF ==============
    
    # get a list of quotebox positions
    # it's a list of tuples corresponding to the start of the content, split between content and source, and end of source (if no source, then (S) is omitted)
    quotebox_indices_temp = []
    quotebox_indices = []
    num_qs_seen = 0
    for i, c in enumerate(field):
        # (Q) splits up the quotebox into sections
        if c.strip() == "(Q)":
            quotebox_indices_temp.append(i)
        # (Q) check if a quotebox has been finished, if so then add the indices to the list
        if c.strip() == "" or i == len(field) - 1:
            if len(quotebox_indices_temp) > 0:
                quotebox_indices.append(tuple(quotebox_indices_temp))
                assert len(quotebox_indices_temp) in [2, 3], f"Your quoteboxes must contain either 2 or 3 (Q)'s, but this one contains {len(quotebox_indices_temp)}.\n\nSee the documentation pages for more detail:\n\nhttps://github.com/callummcdougall/jupyter-to-anki/blob/main/README.md"
            quotebox_indices_temp = []
    indices_dict["quotebox"] = quotebox_indices
                
    # get a list of codeblock positions
    codeblock_line_indices = [i for i, c in enumerate(field) if c.startswith("    ") and c.strip() != ""]
    # codeblock_line_indices will look like [2, 4, 5, 6, 12, 13, 15, 17], i.e. sequences separated by <= 2 lines
    # from this we want start indices [2, 12], and end indices [7, 18]
    if len(codeblock_line_indices) <= 1:
        codeblock_start_indices = codeblock_line_indices
        codeblock_end_indices = codeblock_line_indices
    else:
        codeblock_start_indices = [codeblock_line_indices[0]] + [j for (i, j) in zip(codeblock_line_indices, codeblock_line_indices[1:]) if j - i > 2]
        codeblock_end_indices =  [i for (i, j) in zip(codeblock_line_indices, codeblock_line_indices[1:]) if j - i > 2] + [codeblock_line_indices[-1]]
    indices_dict["codeblock"] = list(zip(codeblock_start_indices, codeblock_end_indices))
    
    # get a list of bullet point lines (each tuple is a set of separate bullet points)
    ul_indices_raw = [i for i, c in enumerate(field) if c.startswith("* ")]
    # ul_indices_filledin = [i for i, c in enumerate(field) if i in ul_indices_raw or (c.strip() == "" and all(j in ul_indices_raw for j in [i + 1, i - 1]))]
    ul_start_indices = [idx for idx, i in enumerate(ul_indices_raw) if i - 1 not in ul_indices_raw]
    ul_end_indices = [idx for idx, i in enumerate(ul_indices_raw) if i + 1 not in ul_indices_raw]
    indices_dict["ul"] = [tuple(ul_indices_raw[start_idx : end_idx + 1]) for start_idx, end_idx in zip(ul_start_indices, ul_end_indices)]
    
    # get a list of bullet point lines (each tuple is a set of separate ordered list items)
    ol_indices_raw = [i for i, c in enumerate(field) if re.match("\d{1,2}\. ", c)]
    # ol_indices_filledin = [i for i, c in enumerate(field) if i in ol_indices_raw or (c.strip() == "" and all(j in ol_indices_raw for j in [i + 1, i - 1]))]
    ol_start_indices = [idx for idx, i in enumerate(ol_indices_raw) if i - 1 not in ol_indices_raw]
    ol_end_indices = [idx for idx, i in enumerate(ol_indices_raw) if i + 1 not in ol_indices_raw]
    indices_dict["ol"] = [tuple(ol_indices_raw[start_idx : end_idx + 1]) for start_idx, end_idx in zip(ol_start_indices, ol_end_indices)]
    
    # get a list of positions of image lines
    image_indices = [i for i, c in enumerate(field) if re.match("!\[(.*)\]", c)]
    indices_dict["image"] = image_indices
                    
    # ============== CONNECT ALL CODEBLOCKS TOGETHER ==============
    
    # replace all bullet point lists with full html bullet points (note this will also replace lines that will eventually go inside of quoteblocks)
    for ul_indices in indices_dict["ul"]:
        ul_length = ul_indices[-1] - ul_indices[0]
        field = field[:ul_indices[0]] + [build_ul(field, ul_indices),] + ["XXX",] * ul_length + field[ul_indices[-1] + 1:]

    # replace all bullet point lists with full html bullet points (note this will also replace lines that will eventually go inside of quoteblocks)
    for ol_indices in indices_dict["ol"]:
        ol_length = ol_indices[-1] - ol_indices[0]
        field = field[:ol_indices[0]] + [build_ol(field, ol_indices),] + ["XXX",] * ol_length + field[ol_indices[-1] + 1:]
        
    # replace all codeblocks sections by full codeblocks
    for codeblock_indices in indices_dict["codeblock"]:
        codeblock_length = codeblock_indices[-1] - codeblock_indices[0]
        field = field[:codeblock_indices[0]] + [build_codeblock(field, codeblock_indices),] + ["XXX",] * codeblock_length + field[codeblock_indices[-1] + 1:]
        
    # replace all quotebox sections by full quoteboxes
    for quotebox_indices in indices_dict["quotebox"]:
        quotebox_length = quotebox_indices[-1] - quotebox_indices[0]
        field = field[:quotebox_indices[0]] + [build_quotebox(field, quotebox_indices)] + ["XXX",] * quotebox_length + field[quotebox_indices[-1] + 1:]
        
    # replace all images
    for image_index in indices_dict["image"]:
        field[image_index] = build_image_line(field[image_index], images_dict)
    
    # remove the "X" strings (these were a hacky addition, to make sure the length of `field` doesn't change during modification)
    field = [re.sub("XXX", "", line) for line in field if line != "XXX"]
    
    # join it all together
    field = "<br>".join(field)
    
    # remove the instances of line breaks which we don't actually want
    replace_dict = {"(<br>)+<ul>": "<ul>", "</ul>(<br>)+": "</ul>", "(<br>)+<ol>": "<ol>", "</ol>(<br>)+": "</ol>", "</pre></div><br><br>": "</pre></div><br>", "</div><br><br>": "</div><br>"}
    for key, value in replace_dict.items():
        field = re.sub(key, value, field)
    
    # ============== CONVERT MARKDOWN TO HTML ==============
    
    return markdown_to_html_ignoring_codeblock(field)


### LOW-LEVEL FUNCTIONS

def build_quotebox(card: List[str], quotebox_indices: List[int]) -> str:
    """
    Constructs a quotebox (note that bullet points have to have been dealt with first for this to work)
    """
    
    # get the content of the card (i.e. between the first two (Q)'s)
    content = "<br>".join(card[quotebox_indices[0] + 1: quotebox_indices[1]])
        
    # case 1: no source
    if len(quotebox_indices) == 2:
        quotebox = "<div class='quotebox'>" + content + "</div>"
    
    # case 2: source, 1 line
    elif quotebox_indices[2] - quotebox_indices[1] == 2:
        source = card[quotebox_indices[1] + 1]
        quotebox = f"<div class='quotebox'>{content}<div class='q-desc q-desc-1'>{source}</div></div>"
    
    # case 3: source, more than one line
    else:
        source1 = card[quotebox_indices[1] + 1]
        source2 = "<br>".join(card[quotebox_indices[1] + 2: quotebox_indices[2]])
        quotebox = f"<div class='quotebox'>{content}<div class='q-desc q-desc-1'>{source1}</div><div class='q-desc q-desc-2'>{source2}</div></div>"
        
    return quotebox

def build_ul(card: List[str], ul_indices: List[List[int]]) -> str:
    """
    Constructs an unordered list.
    """
    ul = "<ul>"
    for i in range(ul_indices[0], ul_indices[-1] + 1):
        if i in ul_indices:
            ul += f"<li>{card[i][2:]}</li>"
        else:
            ul = re.sub("</li>$", "<br><br></li>", ul)
    ul += "</ul>"
    
    return ul

def build_ol(card: List[str], ol_indices: List[List[int]]) -> str:
    """
    Constructs an unordered list.
    """
    ol = "<ol>"
    for i in range(ol_indices[0], ol_indices[-1] + 1):
        if i in ol_indices:
            ol += f"<li>{card[i][2:]}</li>"
        else:
            ol = re.sub("</li>$", "<br><br></li>", ol)
    ol += "</ol>"
    
    return ol

def build_codeblock(card: List[str], codeblock_indices: List[str]) -> str:
    """
    Constructs a codeblock
    """
    
    lines = [line[4:].rstrip() for line in card[codeblock_indices[0]: codeblock_indices[1] + 1]]
    
    codeblock = "<div class='exerciseprecontainer'><pre>" + "<br>".join(lines) + "</pre></div>"
             
    input_values = re.findall("{{{[^{}]*}}}", codeblock)
        
    for i, i_substring in enumerate(input_values):
        i_value = i_substring[3:-3]
        i_rand = get_random_seed_for_inputs(i_value, increment=len([j for (j, j_substring) in enumerate(input_values[:i]) if j_substring == i_substring]))
        i_length = len(i_value) - 3 * len(re.findall("\&[gl]t;", i_value))
        i_elem = f"<input maxlength='{i_length}' name='{i_value}_{i_rand}' style='width: {i_length}ch;'>"
        codeblock = codeblock.replace(i_substring, i_elem, 1)
        
    return codeblock

def build_image_line(s: str, img_name_dict: Dict) -> str:
    """
    Converts an image line such as ![image.png](attachment:image.png) into an html image reference, and saves it to collections.media
    
    Note, this now deals with lines that have more than one image.
    """

    img_names = re.findall("!\[(.*?)\]", s)
    s = ""
    
    for img_name in img_names:
        
        filetype = "gif" if img_name.endswith(".gif") else "jpg"
    
        assert img_name in img_name_dict, f"img_name_orig ({img_name}) not in img_name_dict: {list(img_name_dict.keys())}.\n\nThis probably happened because you copied or uploaded or named an image in your notebook in a weird way.\n\nIf you can't fix this problem, please contact me at my GitHub page:\n\nhttps://github.com/callummcdougall/jupyter-to-anki/blob/main/README.md"
        img_code = list(img_name_dict[img_name].values())[0]    # json data (needs to be decoded to write to a file)
        img_name_new = get_filename_from_json_data(img_code, filetype=filetype)   # hash of the data, so it has a unique filename

        with open(p_media / img_name_new, 'wb') as f:
            f.write(base64.b64decode(img_code))
            # print(f"{img_name_orig} written to collections.media")

        s += f"<img src='{img_name_new}'>"
    
    return s

def markdown_to_html_ignoring_codeblock(s: str) -> str:
    """
    Makes substitutions like *...* -> <i>...</i> (other ones are bold and codefont)
    Doesn't affect code blocks
    """
    
    # first, extract all of the codeblocks and codelines (because we don't want those asterisks to be removed)
    codeblock_list = []
    while True:
        r = "<div class='exerciseprecontainer'><pre>(.{5,}?)</pre></div>"
        srch = re.search(r, s)
        if not srch: break
        s = re.sub(re.escape(srch.group(1)), f"&B{len(codeblock_list):02d}", s, 1)
        codeblock_list.append(srch.group(1))
    codeline_list = []
    while True:
        r = "`([^`]{5,})`"
        srch = re.search(r, s)
        if not srch: break
        s = re.sub(re.escape(srch.group(1)), f"&L{len(codeline_list):02d}", s, 1)
        codeline_list.append(srch.group(1))
        
    # second, now that these have been extracted, you can make all the normal markdown -> html swaps
    # also I've added some stuff to make it more robust, e.g. if you only include one "**" then it adds another on the end.
    replace_dict_words = {"**": "bold", "*": "italic", "`": "code font", "(S)": "a spoiler"}
    replace_dict = {"\*\*": ["<b>", "</b>"], "\*": ["<i>", "</i>"], "\`": ["<font color='#ff5500'>", "</font>"], "\(S\)": ["<span class='spoiler'>", "</span>"]}
    for k, v in replace_dict.items():
        counter = 0
        num_matches = len(re.findall(k, s))
        if num_matches % 2 == 1:
            k_ = k.replace('\\', '')
            global error_messages
            error_messages.append(f"We found a single '{k_}'-character in one one of the lines of your card. This will be interpreted as {replace_dict_words[k_]} by the Python code, and they should come in even numbers. If you don't fix this error then it might mess up your card.")
            break_points = [i for i in range(len(s)-4) if s[i:i+4] == "<br>"]
            if len(break_points) == 0:
                s += k_
            else:
                s = s[:break_points[0]] + k_ + s[break_points[0]:]
        while True:
            srch = re.search(k, s)
            if not srch: break
            s = re.sub(re.escape(srch.group()), v[counter], s, 1)
            counter = 1 - counter
            
    # finally, go back through the string and add back in the codeblocks and codelines
    while len(codeblock_list) > 0:
        codeblock_content = codeblock_list.pop()
        placeholder_string = f"&B{len(codeblock_list):02d}"
        s = re.sub(placeholder_string, codeblock_content, s)
    while len(codeline_list) > 0:
        codeline_content = codeline_list.pop()
        placeholder_string = f"&L{len(codeline_list):02d}"
        s = re.sub(placeholder_string, codeline_content, s)
        
    return s
