import os
import ast
import json
import re 

import numpy as np
# from tabulate import tabulate
import pandas as pd
from pprint import pprint
from tqdm import tqdm

# TODOS
# TODO should I even include same line comments? Or should i ignore them?
# TODO How should i handle multiple line comments that use #? Could combine them all into single commment 
    # Right now each line in multi line comment is counting as individual comment. Need to change this
# TODO Find max sequence length of CODET5 and CODEBERT
# If note in for or if statement should only continue up to next line 


def get_pairs(filename, max_length, above=False):
    """Extracts inline comment and code pairs from a given file

    Args:
        filename (str): name of txt file with python source code.
        max_length (int): number of lines of code paired with each comment
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
        comment, same_line = get_comment(line)

        if not comment: continue

        # Excludes everything but single line comments FIXME 
        # if i != 0 and get_comment(lines[i-1]): continue
        # if i != (len(lines)-1) and get_comment(lines[i+1]): continue 


        # breakpoint()

        below_code = get_code(i, lines, max_length, same_line)
        # breakpoint()
        pair = {'comment': comment, 'below_code': below_code} 
        # print(pair)
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

def get_code(comm_line, lines, max_length, same_line):
    # TODO right type for these? List or str?
    code = ""

    # Line Index of beginning of code block
    start_of_code = comm_line + 1

    # Same line comments
    if same_line:
        code_and_comm = lines[comm_line];
        comm_index = code_and_comm.find("#")
        code = code_and_comm[:comm_index]
        return code
    
    code = lines[start_of_code]

    # Handle if statements and for loops
    is_if = "if" in code and ":" in code
    is_for =  "for" in code and ":" in code
    is_else = "else" in code and ":" in code
    is_elif = "elif" in code and ":" in code
    is_def = "def" in code and ":" in code

    if is_if or is_for or is_else or is_elif or is_def:
        # print("MADE HERE")
        code = get_code_within(start_of_code, lines)
        return code

    # Handle case where comment and one line at end of file
    index = start_of_code + 1
    if index >= len(lines) - 1: return code
    print(f"Index:{index}")
    print(f"lines:{len(lines)}")
    # Get code until the next newline
    # breakpoint()
    next_line = lines[index]
    is_com, _ = get_comment(next_line)
    while(next_line != "\n" and not is_com):
        if hit_token_limit(code + next_line, 199): break
        if index == len(lines) - 1: break
        code +=  next_line
        index += 1
        next_line = lines[index]
        is_com, _ = get_comment(next_line)

    
    return code

#FIXME implement 
def hit_token_limit(string, max_size):
    return False

def get_code_within(start_index, lines):
    code = lines[start_index]
    indent = get_indent_level(code)

    index = start_index + 1
    next_line = lines[index]


    # pprint(next_line)

    while(get_indent_level(next_line) > indent or next_line == '\n'):
        # breakpoint()
        if hit_token_limit(code + next_line, 100): break
        if index == len(lines) - 1: break
        # print(get_indent_level(next_line))
        # print(next_line)
        code += next_line   
        index += 1
        next_line = lines[index]


    return code

def get_indent_level(line):
    leading_whitespace = len(line) - len(line.lstrip())
    return leading_whitespace

# Currently only gets comments above code, not on same line
def get_comment(line):
    """ Returns comment if line is a comment, None otherwise. Filters for descriptive comments
        as well.
    Args:
        line ([type]): [description]

    Returns:
        [type]: [description]
    """
    same_line = False

    if not line: return False, False
    # Line contains no comments
    if '#' not in line: return False, False

    # Filters unwanted comments
    if not is_descriptive(line): return False, False

    # Removes all trailing and preceding whitespaces from line (including tabs)
    line_stripped = re.sub('\s+',' ', line).strip()
    
    # Same line comments
    # Add support for same line comment FIXME
    if line_stripped[0] != '#':
        comm_start = line_stripped.find("#")
        line_stripped = line_stripped[comm_start:]
        same_line = True

    # Isolate just text of comment
    comment = line_stripped[1:]
    comment.strip() # removes potential space between # and actual comment

    # Is commented out code
    if is_valid_python(comment): return False, False

    # Make sure comment contains some english letters 
    has_alpha = any(c.isalpha() for c in comment)

    if not has_alpha: return False, False

    if not is_english(comment): return False, False

    return comment, same_line


# TODO improve filtering
def is_descriptive(comment):
    # Filters for non-descriptive comments
    filters = ["#!", "#\n", "# \n", "-*-", "Copyright", "##", "TODO", "http", "?" ]

    if has_url(comment):
        return False
    
    # Check for unwanted types of comments
    for filter in filters:
        if filter in comment: return False
    
    return True

def has_url(string):
# Regular expression for url
    ck_url = re.search("(?P<url>https?://[^\s]+)", string)
    if ck_url:
        return True
    else:
        return False
       
# TODO Link Stackoverflow source for this function
def is_valid_python(code):
   try:
       ast.parse(code)
   except SyntaxError:
       return False
   return True


def get_all_pairs(directory, max_length, out_file, above=False, num_files=0):
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
        pairs.extend(get_pairs(file_name, max_length))
    
    # Remove duplicates
    pairs = pd.DataFrame(pairs).drop_duplicates()

    # Saving pairs to multiple files 
    # for idx, group in pairs.groupby(np.arange(len(pairs))//150000): 
    #     group.to_json(f'{idx}_pairs.json', orient='records')

    # pairs.to_json(out_file, orient='records')
    # print(len(pairs.index))
    return pairs

#TODO make sure to filter out duplicate comments

# directory = 'py_files'
# out_file = 'test.json'
# pairs = get_all_pairs(directory, 5, out_file, num_files=1)

# print(len(pairs))
# for index, p in pairs.iterrows():
#     # print(f'(({pairs['comment']})))')
#     print(f"((({p['comment']})))")
#     print('\n')
#     print(p['below_code'])


test = 'for_test.txt'
if_pairs = get_pairs(test, 124141)
for p in if_pairs:
    print(f"((({p['comment']})))")
    print(p['below_code'])



# with open(test, 'r') as f:
#     lines = f.readlines()

# pairs = []

# for l in lines:
#     # print(get_indent_level(l))
#     print(l == '\n')
#     print(l)
