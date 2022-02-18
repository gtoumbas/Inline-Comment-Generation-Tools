import os
import ast
import json
import re 

import numpy as np
from tabulate import tabulate
import pandas as pd
from pprint import pprint
from tqdm import tqdm

# TODOS
# TODO should I even include same line comments? Or should i ignore them?
# TODO How should i handle multiple line comments that use #? Could combine them all into single commment 
    # Right now each line in multi line comment is counting as individual comment. Need to change this
# TODO Have a check to make sure comments are in English
# TODO Could filter out ?'s as well 
# TODO Not sure if I should remove newlines and tabs from code (probably not)
# TODO Take code structure into account (i.e tab structure) 
    # Could write a function to find end line
    # Count number of tabs maybe? 
    # 
# TODO Find max sequence length of CODET5 and CODEBERT
# TODO 


def get_pairs(filename, num_lines, above=False):
    """Extracts inline comment and code pairs from a given file

    Args:
        filename (str): name of txt file with python source code.
        num_lines (int): number of lines of code paired with each comment
        above (bool, optional): Collects num_code_lines of code above comment 
        (if possible) in addition to below. Defaults to False.

    Returns:
        pairs (list): list of comment / code pairs (str) found in file
    """
    with open(filename, 'r') as f:
        lines = f.readlines()
    pairs = []
    # num_comments = 0

    for i in range(len(lines)):
        line = lines[i]
        comment = get_comment(line)

        if not comment: continue

        # Excludes everything but single line comments
        if i != 0 and get_comment(lines[i-1]): continue
        if i != (len(lines)-1) and get_comment(lines[i+1]): continue 



        above_code, below_code = get_code(i, lines, num_lines, above=above)

        if above:
            pair = {'comment': comment, 'below_code': below_code, 'above_code': above_code}
        else:
            pair = {'comment': comment, 'below_code': below_code} 
        
        pairs.append(pair)

    return pairs


# -*- coding: utf-8 -*-
def is_english(s):
    try:
        s.encode(encoding='utf-8').decode('ascii')
    except UnicodeDecodeError:
        return False
    else:
        return True

def get_code(index, lines, num_lines, above=False):
    # TODO right type for these? List or str?
    above_code = ""
    below_code = ""

    # Get code above 
    if above:
        num_above = num_lines
        if index - num_lines < 0: num_above = index + 1 # +1 because range is exclusive
        for j in range(1, num_above): above_code += lines[index-j]

    # Get code below 
    num_below = num_lines
    if index + num_lines >= len(lines): num_below = len(lines) - index
    for j in range(1, num_below): below_code += (lines[index+j])

    return above_code, below_code
    

# Currently only gets comments above code, not on same line
def get_comment(line):
    """ Returns comment if line is a comment, None otherwise. Filters for descriptive comments
        as well.
    Args:
        line ([type]): [description]

    Returns:
        [type]: [description]
    """

    # Line contains no comments
    if '#' not in line: return

    # Filters unwanted comments
    if not is_descriptive(line): return 

    # Removes all trailing and preceding whitespaces from line (including tabs)
    line_stripped = re.sub('\s+',' ', line).strip()
    
    # Line does not start with a comment
    if line_stripped[0] != '#': return

    # Isolate just text of comment
    comment = line_stripped[1:]
    comment.strip() # removes potential space between # and actual comment

    # Is commented out code
    if is_valid_python(comment): return 

    # Make sure comment contains some english letters 
    has_alpha = any(c.isalpha() for c in comment)

    if not has_alpha: return

    if not is_english(comment): return

    return comment


# TODO improve filtering
def is_descriptive(comment):
    # Filters for non-descriptive comments
    filters = ["#!", "#\n", "# \n", "-*-", "Copyright", "##", "TODO", "http" ]

    # Check for unwanted types of comments
    for filter in filters:
        if filter in comment: return False
    
    return True


# TODO Link Stackoverflow source for this function
def is_valid_python(code):
   try:
       ast.parse(code)
   except SyntaxError:
       return False
   return True


def get_all_pairs(directory, num_lines, out_file, above=False, num_files=0):
    all_filepaths = os.listdir(directory)
    total_num = len(all_filepaths)
    if num_files:
        total_num = num_files

    new_bar = tqdm(range(total_num))
    pairs = []
    for i in new_bar:
        f = all_filepaths[i]

        if ".DS" in f:
            continue
        file_name = directory + "/" + f
        pairs.extend(get_pairs(file_name, num_lines))
    
    # Remove duplicates
    pairs = pd.DataFrame(pairs).drop_duplicates()

    # Saving pairs to multiple files 
    # for idx, group in pairs.groupby(np.arange(len(pairs))//150000): 
    #     group.to_json(f'{idx}_pairs.json', orient='records')

    # pairs.to_json(out_file, orient='records')
    print(len(pairs.index))
    return pairs

#TODO make sure to filter out duplicate comments

directory = 'py_files'
out_file = 'test.json'
pairs = get_all_pairs(directory, 5, out_file, num_files=4)

print(len(pairs))
for index, p in pairs.iterrows():
    print(f"((((({p['comment']})))))")
    print(p['below_code'])