import os
import ast
import json
import re 

from tabulate import tabulate
import pandas as pd
from pprint import pprint
from tqdm import tqdm


def get_all_pairs(filename, num_lines, above=False):
    """Extracts all inline comment and code pairs from a given file

    Args:
        filename (str): name of txt file with python source code.
        num_lines (int): number of lines of code paired with each comment
        above (bool, optional): Collects num_code_lines of code above comment 
        (if possible) in addition to below. Defaults to False.

    Returns:
        [type]: [description]
    """

    with open(filename, 'r') as f:
        lines = f.readlines()

    pairs = []
    num_comments = 0

    for i in range(len(lines)):
        line = lines[i]

        # Line contains no comments
        if '#' not in line:
            continue
        
        # Filters unwanted comments
        if not is_descriptive(line):
            continue 
    
        # Removes all trailing and preceding whitespaces from line (including tabs)
        line_stripped = re.sub('\s+',' ', line).strip()
        
        # TODOS
        # TODO should I even include same line comments? Or should i ignore them?
        # TODO How should i handle multiple line comments that use #? Could combine them all into single commment 
        # TODO Have a check to make sure comments are in English
        # TODO Could filter out ?'s as well 
        # TODO Not sure if I should remove newlines and tabs from code (probably not)
        # TODO Filter for lines which only contain # and no actual text



        # IGNORING SAME LINE COMMENTS FOR NOW (i.e some code #some comment)
        # Line does not start with a comment
        if line_stripped[0] != '#':
            continue

        num_comments += 1
        
        # Isolate just text of comment
        comment = line_stripped[1:]
        comment.strip() # removes potential space between # and actual comment

        # TODO right type for these? List or str?
        above_code = ""
        below_code = ""

        # Get code above 
        if above:
            num_above = num_lines
            if i - num_lines < 0: num_above = i + 1 # +1 because range is exclusive
            for j in range(1, num_above): above_code += lines[i-j]

        # Get code below 
        num_below = num_lines
        if i + num_lines >= len(lines): num_below = len(lines) - i
        for j in range(1, num_below): below_code += (lines[i+j])
        
        
        # print(comment)
        # for l in below_code:
        #     print(l)

        pair = {'comment': comment, 'below_code': below_code, 'above_code': above_code}
        pairs.append(pair)
        # For testing
        # if num_comments >= 10:
        #     break
    return num_comments
    # return pairs
    print(num_comments)

# TODO improve filtering
def is_descriptive(comment):
    # Filters for non-descriptive comments
    filters = ["#!", "#\n", "# \n", "-*-", "Copyright", "##", "TODO", "http" ]

    # Check for unwanted types of comments
    for filter in filters:
        if filter in comment: return False
    
    return True

all_filepaths = os.listdir('py_files')

file = "py_files/1adrianb--face-alignment.txt"

#TODO make sure to filter out duplicate comments
pairs = []
count = 0
new_bar = tqdm(all_filepaths)
for f in new_bar:
    if ".DS" in f:
        continue
    # pairs.extend(get_all_pairs("py_files/"+f, 3))
    count += get_all_pairs("py_files/"+f, 3)

print(count)
# df = pd.DataFrame.from_dict(pairs, orient='columns')
# df.style
# # calculate and assign new columns
# df['Characters'] = df['comment'].str.len()
# df['Words'] = df['comment'].str.split().str.len()
# print(df)

# mean_characters = df['Characters'].mean()
# mean_words = df['Words'].mean()

# print(mean_characters)
# print(mean_words)

# print(tabulate(df, headers = 'keys', tablefmt = 'psql'))
# print(count)

# pairs = get_all_pairs(file, 10)

# for p in pairs:
#     print("COMMENT: " + p['comment']+"\n")
#     print(p['below_code']+"\n")