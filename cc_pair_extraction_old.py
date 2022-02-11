import os
import ast
import json

from tqdm import tqdm


def is_valid_python(code):
   try:
       ast.parse(code)
   except SyntaxError:
       return False
   return True


"""Returns false if doesn't have, otherwise returns comment and end of comment position.
   
"""
def find_valid_comment(source_string, filter):

    comm_loc = source_string.find('#')

    # Currently only extracts 1 comment per file max 
    # Could do recursive function to get all pairs
    if comm_loc == -1:
      return False, False
    
    end_comm = source_string[comm_loc:].find('\n') + comm_loc
    comm = source_string[comm_loc: end_comm]

    # makes sure items in filter are not in comment
    if any(x in comm for x in filter) and len(comm) > 0:
      return False, False

    #TODO Only comments with code in next line 
    if "\n\n" in source_string[comm_loc: end_comm+5]:
      return False, False

    #excludes commented out code
    if is_valid_python(comm[1:].lstrip()):
      return False, False



    return comm, end_comm

"""Returns next chunk of code (before next empty line) after the eoc(end of comment)
   and the index of the end of the comment
"""
def get_commented_code(source_string, eoc):
    if not eoc or len(source_string) == 0:
      return False, False
    
    code_end = source_string[eoc:].find("\n\n") + eoc
    assert code_end != -1
    code = source_string[eoc:code_end]

    
    if len(code) == 0:
      return False, False
    
    #Checks if code is comment 
    if len(code.lstrip()) == 0 or code.lstrip()[0] == "#":
        return False, False

    return code, code_end

def get_code_comment_pairs(source_string, filter, debug=False):
    cc_pairs = []
    has_valid = True
    prev_end_comm = False
    # x = 0
    while has_valid:
      comm, end_comm = find_valid_comment(source_string, filter)

      code, code_end = get_commented_code(source_string, end_comm)

      if comm and code:
        pair = {"comm": comm, "code": code}
        cc_pairs.append(pair)
        source_string = source_string[code_end:]

      # x+= 1
      # print(prev_end_comm, end_comm)
      # if x > 5:
      #   break
      if prev_end_comm == end_comm:
        has_valid = False
      else:
        has_valid = comm
        prev_end_comm = end_comm


    if debug:
      # print(comm_loc, end_comm)
      print(f"\n COMMENT:\n {comm}")
      # print(len(comm))
      print(f"\n CODE:\n {code}")
    #   print(f"ALL CODE:\n {f}")
      print("-----------------------------------------------------------------")
      # COllect code as lines until an empty line (i.e two \n\n)
    
    if len(cc_pairs) == 0:
      return False
    return cc_pairs

def create_pairs(src_path, json_file_path, start_filters):
    # all_filepaths = os.listdir(src_path)
    all_cc_pairs = []
    num_failed = 0
    # for fpath in tqdm(all_filepaths, desc = 'Extracting Pairs'):
    # Read txt file as single string
    code = open(src_path)
    try:
        code_as_string = code.read()
    except:
        num_failed += 1
        code.close()
        return
        # continue

    code.close()

    # extract pairs
    cc_pairs = get_code_comment_pairs(code_as_string, start_filters)
    if cc_pairs:
        for pair in cc_pairs:
            all_cc_pairs.append(pair)
    else:
        num_failed += 1
    
    
    # # Save pairs to json file
    # with open(json_file_path, 'w') as out_file:
    #     json.dump(all_cc_pairs, out_file, indent=4)

    for pair in all_cc_pairs:
      print(f"COMMENT: \n{pair['comm']}\n")
      print(f"CODE: \n{pair['code']}\n\n")
      

    print(f"Num Files with no inline comments found: {num_failed}")
    print(f"Number of Pairs Extracted: {len(all_cc_pairs)}")

src_path = "py_files/1adrianb--face-alignment.txt"
start_filters = ["#!", "#\n", "# \n", "-*-", "Copyright", "##", "TODO", "http" ]
json_path = "cc_pairs.json"

create_pairs(src_path, json_path, start_filters)