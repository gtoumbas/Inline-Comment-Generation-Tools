import os
import ast
import json
import re 


from pprint import pprint
from tqdm import tqdm

"""
Extracts all inline comment and code pairs from a given file

Args:
filename (str): name of txt file with python source code.
num_lines (int): number of lines of code paired with each comment 
above (boolean): Collects num_code_lines of code above comment (if possible) in addition to below

"""
def get_all_pairs(filename, num_lines, above=False):
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    pairs = []
    num_comments = 0
    for i in range(len(lines)):

        #Remove all preceding whitespaces from line
        line = lines[i]

        # Not sure if I should remove newlines and tabs from code (probably not)

        # Line contains no comments
        if '#' not in line:
            continue
        line_stripped = re.sub('\s+',' ', line).strip()
        
        # TODO should I even include same line comments? Or should i ignore them?
        # TODO How should i handle multiple line comments that use #? Could combine them all into single commment 
        # IGNORING SAME LINE COMMENTS FOR NOW
        # Checks if entire line is comment 
        # Is it useful to store the distance each line is from a comment? 

        # Line does not start with a comment
        if line_stripped[0] != '#':
            continue:

        num_comments += 1
        
        # Isolate just text of comment
        comment = line_stripped[1:]
        comment.strip() # removes potential space between # and actual comment

        # above_code = []
        below_code = []

        # # Get code above 
        # if above:
        #     num_above = num_lines
        #     if i - num_lines < 0: num_above = i + 1 # +1 because range is exclusive
        #     for j in range(1, num_above): above_code.append(lines[i-j])

        # Get code below 
        num_below = num_lines
        if i + num_lines >= len(lines): num_below = len(lines) - i
        for j in range(1, num_below): below_code.append(lines[i+j])
        
        
        print(comment)
        for l in below_code:
            print(l)
    
        # For testing
        if num_comments >= 10:
            break

    print(num_comments)

file = "py_files/1adrianb--face-alignment.txt"
get_all_pairs(file, 3)