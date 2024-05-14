import os
import ast
import json
import re 
import collections
import itertools

import numpy as np
# from tabulate import tabulate
import pandas as pd
from pprint import pprint
from tqdm import tqdm
from nostril import nonsense
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from fuzzywuzzy import fuzz
import sklearn 


# TODOS
# TODO should I even include same line comments? Or should i ignore them?
# TODO How should i handle multiple line comments that use #? Could combine them all into single commment 
    # Right now each line in multi line comment is counting as individual comment. Need to change this
# TODO Find max sequence length of CODET5 and CODEBERT
# If note in for or if statement should only continue up to next line 
# TODO should i not remove whitespace from comments? 

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
    i = 0
    # print(len(lines))
    # while i < len(lines):
    for i in range(len(lines)):
        line = lines[i]
        comment, same_line, next_index = get_comment(lines, i)
        i = next_index
        # print(i)
        if not comment: 
            # i += 1
            continue

        # Excludes everything but single line comments FIXME 
        # if i != 0 and get_comment(lines[i-1]): continue
        # if i != (len(lines)-1) and get_comment(lines[i+1]): continue 


        # breakpoint()

        below_code = get_code(i, lines, max_length, same_line)
        # breakpoint()
        if not below_code: continue
        if below_code == '\n': continue
        pair = {'comment': comment, 'below_code': below_code} 
        # print(pair)
        pairs.append(pair)
        # i += 1

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
    """
    Given a line with a comment, return the code block that follows the comment.
    
    :param comm_line: The line number of the comment
    :param lines: the lines of the file
    :param max_length: The maximum length of the code snippet
    :param same_line: If the comment is on the same line as the code
    :return: A string of code that is the comment and the code block
    """
    # TODO right type for these? List or str?
    code = ""

    # Line Index of beginning of code block
    start_of_code = comm_line + 1
    if start_of_code >= len(lines) - 1: return None
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
        if not code: return "REMOVE ME PLS PLS"
        return code

    # Handle case where comment and one line at end of file
    index = start_of_code + 1
    if index > len(lines) - 1: return code
    # print(f"Index:{index}")
    # print(f"lines:{len(lines)}")
    # Get code until the next newline
    # breakpoint()
    #TODO maybe add a case so if the line directly after comment is newline its fine
    next_line = lines[index]
    while(next_line != "\n" and not is_just_comment(next_line)):
        if hit_token_limit(code + next_line, 199): break
        if len(code) > 500: break
        code +=  next_line

        if index >= len(lines) - 1: break
        index += 1
        next_line = lines[index]

    if has_unreadable_chars(code): return False
    
    #TODO maybe remove this

    if not is_valid_python(code): return False
    
    return code

#FIXME implement 
def hit_token_limit(string, max_size):
    return False

def get_code_within(start_index, lines):
    """
    Given a starting index, return the code within the function
    
    :param start_index: The index of the line where the code block starts
    :param lines: The lines of code to be searched
    :return: A string of code.
    """
    code = lines[start_index]
    indent = get_indent_level(code)

    index = start_index + 1
    if index >= len(lines) - 1: return ""
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
    """
    Return the number of leading whitespace characters in a string
    
    :param line: The line of code to be checked
    :return: The number of spaces at the beginning of the line.
    """
    leading_whitespace = len(line) - len(line.lstrip())
    return leading_whitespace

def get_comment(lines, curr_line_index):
    """ Returns comment if line is a comment, None otherwise. Filters for descriptive comments
        as well.
    Args:
        line ([type]): [description]

    Returns:
        [type]: [description]
    """
    same_line = False
    last_line_ind = curr_line_index
    # if curr_line_index > 5:
    #     print(curr_line_index)
    line = lines[curr_line_index]
    multi_line = [line]

    if not line: return False, False, curr_line_index
    # Line contains no comments
    if '#' not in line: return False, False, curr_line_index

    # Check if not first line of multi-line comm
    if curr_line_index != 0 and is_just_comment(lines[curr_line_index-1]):
        return False, False, curr_line_index

    # Filters unwanted comments
    if not is_descriptive(line): return False, False, curr_line_index

    # Handle multi-line comments
    next_ind = curr_line_index + 1
    if next_ind < len(lines) - 1:
        next_line = lines[next_ind]

        while(is_just_comment(next_line)):
            multi_line.append(next_line)
            next_ind += 1

            if next_ind >= len(lines) - 1: break
            last_line_ind += 1
            next_line = lines[next_ind]

    # Clean up and combine multi-line comment
    if len(multi_line) > 1:
        comment = ""
        for c in multi_line:
            if not is_descriptive(c): return False, False, last_line_ind 
            comm, _ = isolate_comment(c)
            if not comment: comment = comm
            else: comment += "\n" + comm

        comment = comment.rstrip() # Not sure if this is needed
        return comment, False, last_line_ind

    comment, same_line = isolate_comment(line)
    return comment, same_line, last_line_ind 

def isolate_comment(line):
    """
    This function isolates the comment from a line of code.
    
    :param line: the line to be processed
    """
    line_stripped = re.sub('\s+',' ', line).strip()
    same_line = False

    if line_stripped[0] != '#':
        comm_start = line_stripped.find("#")
        line_stripped = line_stripped[comm_start:]
        same_line = True
        
    comment = line_stripped[1:]
    comment.strip() # removes potential space between # and actual comment

    return comment, same_line

# Returns true if line only contains comment, returns false if no comment or if same-line comment
def is_just_comment(line):
    """
    Given a line of text, return True if the line is a comment, False otherwise
    
    :param line: The line to be checked
    :return: A boolean value.
    """
    line_stripped = re.sub('\s+',' ', line).strip()
    if not line_stripped: return False
    # print(line_stripped)
    return line_stripped[0] == '#'

def has_too_many_repeating_chars(line):
    maximum = count = 0
    rep_char = None
    current = ''
    for c in line:

        if c == current:
            count += 1
        else:
            count = 1
            current = c

        maximum = max(count,maximum)

        if not rep_char or count == maximum:
            rep_char = current
    
    if rep_char == " ":
        return False

    if maximum >= 5:
        # print(line )
        return True
    return False
    
# TODO improve filtering
def is_descriptive(comment):
    # Filters for non-descriptive comments
    filters = ["#!", "#\n", "# \n", "-*-", "Copyright", "##", "TODO", "http", "?", "!/usr/bin/", "type:", "pylint" ]

    comment, _ = isolate_comment(comment)
    # print(type(comment))
    # print(comment)
    try:
        if has_url(comment):
            return False
        
        # Is commented out code
        if is_valid_python(comment.strip()): return False

        # Make sure comment contains some english letters 
        has_alpha = any(c.isalpha() for c in comment)

        if not has_alpha: return False

        if has_unreadable_chars(comment): return False

        if not is_english(comment): return False

        if has_too_many_repeating_chars(comment): return False
        # Check for unwanted types of comments
        for filter in filters:
            if filter in comment: return False
    except:
        return False
    
    return True

def has_unreadable_chars(line):
    _, unrdble_chars = re.subn(r'[^\x00-\x7f]',r'', line) 

    return unrdble_chars != 0; 
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
    num_comments = 0
    if num_files:
        total_num = num_files

    new_bar = tqdm(range(total_num))
    pairs = []
    for i in new_bar:
        f = all_filepaths[i]

        if ".DS" in f:
            continue
        file_name = directory + "/" + f
        curr_pairs = get_pairs(file_name, max_length)
        num_comments += len(curr_pairs)
        pairs.extend(curr_pairs)
        new_bar.set_description(f"Num Comments: {num_comments}")
    
    # Remove duplicates
    pairs = pd.DataFrame(pairs).drop_duplicates()
    pairs.groupby(pairs.columns.tolist(),as_index=False).size()

    # Saving pairs to multiple files 
    options = ['train', 'test', 'eval']
    opt_i = 0
    count = 0

    pairs.to_json(out_file, orient='records', lines=True)
    # print(len(pairs.index))
    print(len(pairs.index))

    return pairs

def split_pairs(filename, perform_shuffle=True):
    """
    The function splits the data into train, validation, and test sets.
    """
    with open(filename, encoding="utf-8") as f:
        all_pairs = f.readlines()
    all_pairs = [json.loads(pair) for pair in all_pairs]

    examples = []
    count = 0

    bar = tqdm(all_pairs)
    for js in bar:
        # line = line.strip()
        # js = json.loads(line)
        # print(js)
        try:
            code = js["below_code"]
            comment = js["comment"]
        except:
            code = js['code']
            comment = js['comm']

        if " " not in comment.strip():
            continue

        # Check if code == comment
        if code.strip() == comment.strip():
            continue

        if is_valid_python(comment.strip()):
            continue

        if "%%%%%%" in code or "%%%%%%" in comment:
            continue
        if "--------" in comment:
            continue
        if len(code) < 50 or len(comment) < 15:
            continue
        
        if "\\x" in code or "\\x" in comment:
            continue

        if len(code) > 1000 or len(comment) > 500:
            continue

        try:
            if nonsense(comment):
                with open("nonsense_coms.txt", 'a') as nf:
                    nf.write(comment + "\n")
                continue 
        except:
            pass
        count += 1
        bar.set_description(f"COUNT: {count}")
        # if count % 10000 == 0:
        #     print(count)
        examples.append({"comm": comment, "code": code})


    examples = pd.DataFrame(examples).drop_duplicates()
    examples.drop_duplicates('comm', inplace=True)
    # examples.reset_index(inplace=True)
    examples.drop_duplicates('code', inplace=True)
    # examples.reset_index(inplace=True)

    examples = sklearn.utils.shuffle(examples)

    train, valid, test = np.split(examples.sample(frac=1, random_state=42),[int(.8 * len(examples)), int(.9 * len(examples))])


    train = pd.DataFrame(train)
    validate = pd.DataFrame(valid)
    test = pd.DataFrame(test)

    train.to_json("train.jsonl", orient='records', lines=True)
    validate.to_json("valid.jsonl", orient='records', lines=True)
    test.to_json("test.jsonl", orient='records', lines=True)
    print(len(train.index))
    print(len(validate.index))
    print(len(test.index))
    print()
    print(examples['comm'].str.len().mean())
    print(examples['comm'].str.len().max())
    print()
    print(examples['code'].str.len().mean())
    print(examples['code'].str.len().max())
    # return examples


def get_n_most_similar(n, pairs):
    # Calculate similarity score for each pair of code and comments
    bar = tqdm(pairs)
    for p in bar:      
        # p = pon.loads(p)
        try:
            code = p["below_code"]
            comm = p["comment"]
        except:
            code = p['code']
            comm = p['comm']
        p["sim"] = get_similarity(code, comm)

    # Sort pairs by similarity score
    pairs = sorted(pairs, key=lambda x: x["sim"], reverse=True)

    # Get the n most similar pairs
    pairs = pairs[:n]

    return pairs

def get_similarity(code, comment):
    """
    The function returns the similarity between the code and comment.
    Uses bleu score.
    """
    # Converting strings into lists
    code_list = code.split()
    comment_list = comment.split()

    # TODO try some other similarity metrics

    # Similarity using levenshtein distance from fuzzywuzzy
    # sim = fuzz.ratio(code, comment)
    # return sim

    # Calculating bleu score
    smoothing = SmoothingFunction().method4
    bleu_score = sentence_bleu([code_list], comment_list, smoothing_function=smoothing)
    return bleu_score

# Checking similarity functions 
with open("all_pairs.jsonl", encoding="utf-8") as f:
    pairs = f.readlines()
