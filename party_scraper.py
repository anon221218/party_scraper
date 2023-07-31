"""
Party-Scraper
Download posts from coomer.party & kemono.party

Based on coomer.party-scraper by https://github.com/EGirlEnthusiast/

Files (used for options/resuming)
.source.txt - the URL of the account to download from
.text.txt - if exists, script will save text from posts into .txt files, delete to disable text downloading
.attachments.txt - if exists, script will download attachments (and videos), delete to limit scrape to images only
.todo.txt - posts the script has detected but hasn't downloaded from yet
.posts.txt - all the posts the script has downloaded from
.files.txt - all the files the script has downloaded, automatic name, name from server & name from query string
.errors.txt - posts the script encountered an error downloading from (gets cleared when script runs again, since script re-scans/retries on each run)
.errors.old.txt - posts the script encountered an error downloading from the previous run (should not exist if script isn't running)
.skip_scan.txt - don't scan for updated posts, just download what's already in the .todo.txt file (note: errors will NOT be re-scanned and links to previous errors may be lost, re-scan account to find and try them again). This is useful when you keep having issues with an account with large amounts of pages, it allows you to keep trying till the todo list is empty, then delete this .skip_scan.txt file and let the script re-scan and retrieve the missing posts.

Dev Note on unfinished functionality: If a post has an error during download or is interrupted, all images/attachments for that post get re-downloaded (and over-write the existing same files), the plan was to prevent this (helping people with slow/limited bandwidth). Interrupted downloads would have been detected in scan_account with the top entry in .todo.txt, if not blank, having been the interrupted one, then would have to check during download_file if that post matched. Then skipping files found in .files.txt (via filename & name1) until no longer found, then it would stop skipping downloads for the post and start downloading files again. Posts in .errors.old.txt would also be checked in the same way to only download what previously errored out.

Dev Note: Set show_debug = True to break on and show error messages

"""
from bs4 import BeautifulSoup
from more_itertools import last
import requests as scraper
import time
import os
import sys
import re

from sqlalchemy import null

show_debug = False

file_path = None
domain = None

def script_exit(code): # code 1 = user aborted, code 0 = success, code -1 = error, code -2 = abort due to bad script inputs (URL/folder/files)
    #input("\nPress Enter to exit") # uncomment to keep script window open
    os._exit(code)

def crash():
    import traceback
    traceback.print_exc()
    input("\nPress Enter to exit")
    os._exit(-1)

def download_data():
    global file_path, domain
    had_error = False
    try:
        if os.path.exists(file_path+".errors.old.txt"):
            os.remove(file_path+".errors.old.txt")
    except:
        print("!!! Error deleting previous .errors.old.txt file\n")
        if show_debug == True:
            crash()
    try:
        if os.path.exists(file_path+".errors.txt"):
            os.rename(file_path+".errors.txt", file_path+".errors.old.txt")
    except:
        print("!!! Error moving previous .errors.txt file\n")
        if show_debug == True:
            crash()
    get_text = False
    if os.path.exists(file_path+".text.txt"):
        get_text = True
    get_attachments = False
    if os.path.exists(file_path+".attachments.txt"):
        get_attachments = True
    open(file_path+".files.txt", "a").close() # create .files.txt if it doesn't exist, before downloads in-case an error happens
    with open(file_path+".todo.txt", "r") as todo_file:
        todo = todo_file.readlines()
    if len(todo) == 0:
        print("\nNo new content detected, nothing to download")
        script_exit(0)
    print("\nDownloading Files...")
    for url_path in todo:
        had_error_on_current = False
        url_path = str(url_path).strip()
        if url_path == '':
            with open(file_path+".todo.txt", "r+") as todo_file:
                lines = todo_file.readlines()
                todo_file.seek(0)
                todo_file.truncate()
                todo_file.writelines(lines[1:]) # remove first line and write remainder back to file
            continue
        print("\nNew Entry Started: "+url_path)
        website = scraper.get("https://"+domain+url_path)
        website_content = BeautifulSoup(website.content, "html.parser")
        post_id = url_path.split("/")[-1].strip()
        file_count = 0 # start at 0 and increment before downloads, if failure it will still increment skipping failed entry

        if get_text == True:
            try:
                text = website_content.find("div", class_="post__content")
                if text == None:
                    print("No text detected")
                else:
                    text = text.prettify("utf8")
                    with open(file_path+post_id+".txt", "wb") as post_content_file:
                        post_content_file.write(text)
                    # remove outer html tag
                    with open(file_path+post_id+".txt", "r+", encoding="utf8") as post_content_file: # force UTF-8 in-case of foreign characters
                        lines = post_content_file.readlines()
                        post_content_file.seek(0)
                        post_content_file.truncate()
                        post_content_file.writelines(lines[1:-1]) # remove first & last line and write remainder back to file
            except:
                had_error = True
                had_error_on_current = True
                print("!!! Error saving post content")
                if show_debug == True:
                    crash()

        def download_file(link):
            name1 = link.split("?")[0].split("/")[-1] # filename on server
            name2 = link.split("?f=")[-1] # filename from query-string
            extension = link.split("?")[0].split(".")[-1]
            if extension.lower() == "bin" and name2.find(".") >= 0: # server only supports a few extensions, take from query-string for others
                extension = name2.split(".")[-1]
            filename = post_id+"_"+str(file_count)+"."+extension
            # if name2 is not a uuid or common hash, append URL-decoded filename (also, uses server extension instead of file extension, just because)
            if not re.match("^(?:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})|(?:[0-9a-f]{32})|(?:[0-9a-f]{40})|(?:[0-9a-f]{56})|(?:[0-9a-f]{64})\.", name2.lower()):
                if not name2[:4] == "http": # Patch for new file url not containing filename querystring
                    filename = post_id+"_"+str(file_count)+"_"+scraper.utils.unquote(name2.rsplit(".", 1)[0])+"."+extension
            # TODO: Check this line in both services
            contents = scraper.get(link).content
            with open(file_path+filename, "wb") as data_file:
                data_file.write(contents)
            with open(file_path+".files.txt", "a") as downloaded_files:
                downloaded_files.write(filename+"\t"+name1+"\t"+name2+"\n")

        # images
        try:
            images = website_content.find("div", class_="post__files")
            html_links = images.find_all("a")
            for html_link in html_links:
                file_count += 1
                try:
                    link = html_link["href"].strip()
                    print(link)
                    download_file(link)
                except KeyboardInterrupt:
                    print("\n\n!!! Keyboard interrupt detected, exiting...")
                    script_exit(1)
                except:
                    had_error = True
                    had_error_on_current = True
                    print("!!! Error downloading")
                    if show_debug == True:
                        crash()

        except:
            print("No images detected")

        # attachments
        if get_attachments == True:
            try:
                attachments = website_content.find("ul", class_="post__attachments")
                html_links = attachments.find_all("a")
                for html_link in html_links:
                    file_count += 1
                    try:
                        link = html_link["href"].strip()
                        print(link)
                        download_file(link)
                    except KeyboardInterrupt:
                        print("\n\n!!! Keyboard interrupt detected, exiting...")
                        script_exit(1)
                    except:
                        had_error = True
                        had_error_on_current = True
                        print("!!! Error downloading")
                        if show_debug == True:
                            crash()
            except:
                print("No attachments detected")

        # update link files
        if had_error_on_current == True:
            with open(file_path+".errors.txt", "a") as errors_file:
                errors_file.write(url_path+"\n")
        else:
            with open(file_path+".posts.txt", "a") as posts_file:
                posts_file.write(url_path+"\n")
        with open(file_path+".todo.txt", "r+") as todo_file:
            lines = todo_file.readlines()
            todo_file.seek(0)
            todo_file.truncate()
            todo_file.writelines(lines[1:]) # remove first line and write remainder back to file
    try:
        if os.path.exists(file_path+".errors.old.txt"):
            os.remove(file_path+".errors.old.txt")
    except:
        print("!!! Error deleting previous .errors.old.txt file\n")
        if show_debug == True:
            crash()
    if had_error:
        print("\n!!! An error occurred on one or more downloads, please scroll up to check which ones\n")
    print("\nScript has finished, enjoy your files!")

def scan_account(url):
    global file_path
    try:
        with open(file_path+".posts.txt", "a+") as posts_file: # opened with a+ to create if doesn't exist while allowing reading without truncate
            posts_file.seek(0) # move pointer to top
            completed_posts = posts_file.readlines()
        with open(file_path+".todo.txt", "a+") as todo_file: # opened with a+ to create if doesn't exist while allowing reading without truncate
            todo_file.seek(0) # move pointer to top
            todo_posts = todo_file.readlines()
    except:
        print("Unable to write to directory")
        if show_debug == True:
            crash()
        script_exit(-1)

    try:
        website = scraper.get(url)
        website_content = BeautifulSoup(website.content, "html.parser")
    except KeyboardInterrupt:
        print("\n\n!!! Keyboard interrupt detected, exiting...")
        script_exit(1)
    except:
        print("Error opening URL, please check internet connection and URL")
        if show_debug == True:
            crash()
        script_exit(-1)

    #calculate number of pages
    try:
        next_page_button = website_content.find(title="Next page")
        if not next_page_button == None:
            articles_per_page = int(str(next_page_button["href"]).split("=")[-1])
            last_page_offset = int(str(next_page_button.parent.find_previous("li").find("a")["href"]).split("=")[-1])
        else:
            next_page_button = website_content.find(class_="paginator").find(class_="next")
            articles_per_page = int(str(next_page_button["href"]).split("=")[-1])
            last_page_offset = int(str(next_page_button.find_previous("a")["href"]).split("=")[-1])
        print("\nTotal Pages: "+str(int(last_page_offset/articles_per_page)+1))
    except:
        articles_per_page = 1 # only one page, set to 1 (can't be zero due to division by below)
        last_page_offset = 0
        print("\nTotal Pages: 1")

    posts = []

    def get_posts_on_page():
        html_posts = website_content.find_all("article",class_="post-card")
        for html_post in html_posts:
            html_link = html_post.find("a")
            link = html_link["href"]
            posts.append(link)
            print("Discovered entry: "+link)

    #fetch first page links then iterate through pages until last page
    article_offset = 0
    while article_offset <= last_page_offset:
        article_offset += articles_per_page
        print("\nFetching posts on page "+str(int(article_offset/articles_per_page)))
        get_posts_on_page()
        if article_offset > 1: # single page just has value of 1 from above
            time.sleep(1)
            try:
                website = scraper.get(url+"?o="+str(article_offset))
                website_content = BeautifulSoup(website.content, "html.parser")
            except KeyboardInterrupt:
                print("\n\n!!! Keyboard interrupt detected, exiting...")
                script_exit(1)
            except:
                print("\nError opening URL, please check internet connection and URL")
                if show_debug == True:
                    crash()
                script_exit(-1)

    for post in posts:
        found = False
        for line in completed_posts:
            if line.strip() == post:
                found = True
                break # already in files, check next post
        if not found:
            for line in todo_posts:
                if line.strip() == post:
                    found = True
                    break # already in files, check next post
        if not found:
            with open(file_path+".todo.txt", "a") as todo_file:
                todo_file.write(post+"\n")

def main():
    global file_path, domain
    # get any drag/drop files or command line parameters
    parameters = sys.argv[1:]
    if len(parameters) == 1: # artificial limit: single folder drag/drop or URL as only parameter
        parameter = parameters[0]
        if os.path.isdir(parameter): # drag/drop or command-line directory as parameter (resume functionality)
            file_path = os.path.join(parameter, "") # make sure path has trailing slash (OS independent)
            if not os.path.exists(file_path+".source.txt"):
                print("Folder doesn't contain a .source.txt file") # resuming requires this file
                script_exit(-2)
            with open(file_path+".source.txt", "r") as source_url:
                url = source_url.readline().strip()
            try:
                url_parts = re.search("^https://([^/]+)/[^/]+/user/[^/\?#]+$", url) # check URL format and extract domain
                domain = url_parts.group(1)
            except:
                print("Invalid .source.txt contents, should contain single line with a URL like:\nhttps://coomer.party/onlyfans/user/janedoe")
                script_exit(-2)
            if not os.path.exists(file_path+".skip_scan.txt"):
                scan_account(url)
            download_data()
            script_exit(0)
        else: # command-line with URL as a parameter
            try:
                url_parts = re.search("^(https://([^/]+)/([^/]+)/user/([^/\?#]+)$)", parameter) #check URL format and extract domain/service/user
                url = url_parts.group(1)
                domain = url_parts.group(2)
                directory = url_parts.group(3)+"-"+url_parts.group(4) # e.g. onlyfans-janedoe (user can rename later, name doesn't affect scripting)
            except:
                print("Invalid URL, must be of form: https://site.party/service/user/username\ne.g. https://coomer.party/onlyfans/user/janedoe")
                script_exit(-2)
            file_path = os.path.join(os.getcwd(), directory, "") # create path: current directory + above directory name + trailing slash (OS independent)
            if os.path.exists(file_path):
                print("A directory '"+directory+"' already exists. To update, run the script with the directory as a parameter instead, e.g.\n"+os.path.basename(__file__)+" "+directory)
                script_exit(-2)
            try:
                os.mkdir(file_path)
                with open(file_path+".source.txt", "w") as file_for_source:
                    file_for_source.write(url)
                open(file_path+".text.txt", "w").close() # enable saving text by default for automation script-ability
                open(file_path+".attachments.txt", "w").close() # enable attachments (& videos) by default for automation script-ability
            except:
                print("Unable to create directory or files")
                if show_debug == True:
                    crash()
                script_exit(-1)
            scan_account(url)
            download_data()
            script_exit(0)
    elif len(parameters) > 1: # multiple parameters detected (multiple folder drag/drop or script invoked with multiple command-line parameters)
        if os.path.isdir(parameters[0]) and os.path.isdir(parameters[1]): # artificial limit to single folder drag/drop
            print("Only a single directory is allowed for drag/drop")
            script_exit(-1)
        else:
            print("Unknown request")
            script_exit(-1)
    else: # no parameters
        print("To resume, drag/drop a folder to the script or run the script with the directory as a parameter.")
        print("Otherwise, answer the prompts below to download content\n")
        print("Please Enter URL of form: https://site.party/service/user/username\ne.g. https://coomer.party/onlyfans/user/janedoe")
        print("(Ensure no text exists after the creator's name in the link)")
        url = input("URL: ")
        try:
            url_parts = re.search("^https://([^/]+)/[^/]+/user/[^/\?#]+$", url) # check URL format and extract domain
            domain = url_parts.group(1)
        except:
            print("\nInvalid URL, must be of form: https://site.party/service/user/username\ne.g. https://coomer.party/onlyfans/user/janedoe")
            script_exit(-2)
        print("\nPlease enter the directory where you want to save the downloads\n(leave blank and press enter for current directory)")
        file_path = input("FILE PATH: ").strip()
        if file_path == '':
            file_path = os.getcwd()
        try:
            if not os.path.isdir(file_path):
                os.mkdir(file_path)
            if os.path.exists(os.path.join(file_path, "")+".source.txt"):
                print("\n !!! This folder already contains data, try updating it instead by using the directory as a parameter, e.g.\n"+os.path.basename(__file__)+" "+file_path)
                script_exit(-2)
            file_path = os.path.join(file_path, "") # make sure path has trailing slash (OS independent)
            with open(file_path+".source.txt", "w") as file_for_source:
                file_for_source.write(url)
        except:
            print("Unable to create directory or files")
            if show_debug == True:
                crash()
            script_exit(-1)
        question_include_attachements = input("Include attachments (& videos)?\nY / N: ").lower().strip()
        if question_include_attachements == "y":
            open(file_path+".attachments.txt", "w").close()
        question_include_text = input("Save text from posts?\nY / N: ").lower().strip()
        if question_include_text == "y":
            open(file_path+".text.txt", "w").close()
        question_scrape_now = input("\nBegin scraping now?\nY / N: ").lower().strip()
        if question_scrape_now == "y":
            scan_account(url)
            download_data()
        script_exit(0)

#START
print("\nStarting Party-Scraper...\n")
try:
    main()
except KeyboardInterrupt:
    print("\n\n!!! Keyboard interrupt detected, exiting...")
    script_exit(1)
