from ctypes import alignment
from curses import raw
import requests
import time 
import os
import string 
import ssl

from github import Github as GH
from bs4 import BeautifulSoup as bs
from pprint import pprint
from tqdm import tqdm, trange

"""
Recursively explores Github Repo and writes raw python file links to file.
"""
def get_py_files(url, out_file, depth=0):
    """[summary]

    Args:
        url ([type]): [description]
        out_file ([type]): [description]
        depth (int, optional): [description]. Defaults to 0.
    """
    try:
        page = requests.get(url)
    except:
        return

    if depth > 4:
        return

    raw_prefix = "https://raw.githubusercontent.com" #raw text url prefix
    norm_prefix = "https://github.com"
    soup = bs(page.content, 'html.parser')
    for el in soup.find_all('a'):
        dict_att = el.attrs
        try:
            link = dict_att['href']
        except:
            continue
        
        if link[-3:] == '.py':
            new_link = link.replace('/blob', '')
            raw_content_url = raw_prefix+new_link

            with open(out_file, 'a') as f:
                f.write(f"{raw_content_url}\n")
            # page = requests.get(raw_content_url)
            # soup = bs(page.content, 'html.parser')
            # print(soup.get_text())
        else:
            next_url = norm_prefix + link
            prefixes = ['/tree/master', '/tree/main', '/tree/dev']
            avoid = ['login?', 'signup?']
            if url in next_url and 'github' in next_url: # next_url is a folder on repo
                for a in avoid:
                    if a in next_url: return
                for p in prefixes:
                    if p in next_url:
                        get_py_files(next_url, out_file, depth=(depth+1))
                        break


def get_used_repos(raw_links):
    """[summary]

    Args:
        raw_links ([type]): [description]

    Returns:
        [type]: [description]
    """
    used_repos = []
    curr_repo = ''

    with open(raw_links, 'r') as f:
        all_links = f.readlines()
    
    for link in all_links:
        com_ind = link.index('com')
        try:
            repo_name = link[com_ind:].split('/')[1] + '/' + link[com_ind:].split('/')[2]
        except:
            continue
        repo_name.rstrip()

        if repo_name in used_repos:
            continue
        if not curr_repo or curr_repo != repo_name:
            curr_repo = repo_name
            used_repos.append(curr_repo)
    
    return used_repos


def is_used_repo(url, repo_list):
    """[summary]

    Args:
        url ([type]): [description]
        repo_list ([type]): [description]

    Returns:
        [type]: [description]
    """
    com_ind = url.index('com')
    repo_name = url[com_ind:].split('/')[1] + '--' + url[com_ind:].split('/')[2]
    return (repo_name in repo_list, repo_name)


def download_files(raw_links, out_dir, error_file, num_files=0, debug=False, start_index=0):
    """[summary]

    Args:
        raw_links ([type]): [description]
        out_dir ([type]): [description]
        error_file ([type]): [description]
        num_files (int, optional): [description]. Defaults to 0.
        debug (bool, optional): [description]. Defaults to False.
        start_index (int, optional): [description]. Defaults to 0.
    """
    with open(raw_links, 'r') as f:
        all_links = f.readlines()

    if num_files == 0: num_files = len(all_links)

    num_errors = 0
    num_created = 0
    
    pbar = tqdm(range(start_index, num_files))
    curr_file = ''
    session = requests.Session()
    for i in pbar:
        #TODO handle already written files by searching for file existence before making request
        curr_link = all_links[i]
        curr_link = curr_link.rstrip()
        try:
            page = session.get(curr_link)
        except:
            with open(error_file, 'a') as f:
                f.write(f"{curr_link}   Index: {i+start_index}\n")
            num_errors += 1
            continue
        
        try:
            curr_repo = url_to_repo(curr_link)
        except:
            continue

        if not curr_file:
            curr_file = curr_repo
        
        if curr_file != curr_repo:
            curr_file = curr_repo


        raw_code = page.text
        if len(raw_code) == 14 and raw_code == "404: Not Found":
            with open(error_file, 'a') as f:
                f.write(f"{curr_link}     Index: {i+start_index}\n")
            num_errors += 1
            continue
        
        # curr_link = curr_link.replace("https://raw.githubusercontent.com/", "")
        # curr_link = curr_link.replace("/", "-")
        # curr_link = curr_link.replace(".py", "")

        with open(out_dir + f"/{curr_file}.txt", 'a') as f:
            url_and_code = "\n%%%%%%"+ curr_link + "%%%%%%\n" + raw_code
            f.write(url_and_code)
            num_created += 1
            pbar.set_description(f"E: {num_errors}, C: {num_created}, {curr_file}")

        
    if debug:
        print(f"Num Errors: {num_errors}")
        print(f"Success Rate: {(num_files-num_errors) / num_files}")
    
def url_to_repo(url):
    com_ind = url.index('com')
    repo_name = url[com_ind:].split('/')[1] + '--' + url[com_ind:].split('/')[2]
    return repo_name

error_file = 'errors.txt'
no_dups = 'raw_links_no_dups.txt'
num_files = 1000
out_dir = 'py_files'
start_num = 28004+48119+79488+288780
# repos = get_used_repos(no_dups)
# print(len(repos))
# print(repos)

download_files(no_dups, out_dir, error_file, start_index=start_num, debug=True)


















# url = "https://github.com/blaze/blaze"
# page = requests.get(url)

# alphabet_string = string.ascii_lowercase
# alphabet_list = list(alphabet_string)

# out_file = 'python_raw_links.txt'
# token = "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"
# g = GH(token)
# alphabet_list = alphabet_list[4:]


# print(alphabet_list)

# for letter in alphabet_list:
#     repositories = g.search_repositories(query=f'{letter}+language:python', sort='stars', order='desc')
#     count = 0
#     repo_list = get_used_repos('python_raw_links.txt')
#     # for r in repo_list:
#     #     print(r)
#     pbar = tqdm(total=1000)
#     for repo in repositories:
#         count += 1
#         url = repo.html_url 
#         stars = repo.stargazers_count 
#         used, repo_name = is_used_repo(url, repo_list)
#         if count % 5 == 0:
#             time.sleep(3)
#         if not used and stars >= 100:
#             pbar.set_description(repo_name)
#             get_py_files(url, out_file)
#         else:
#             pbar.set_description('USED')
#         pbar.update(1)
        
    
    # print(f"LETTER {letter}")



# test = "https://raw.githubusercontent.com/stamparm/maltrail/master/server.py"

# com_ind = test.index('com')
# print(test[com_ind:].split('/')[1])

# write_used_repos('python_raw_links.txt', 'already_used_repos.txt')