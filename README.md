# **Party-Scraper**
Download posts/images/videos/attachments from coomer.party & kemono.party

Based on coomer.party-scraper by https://github.com/EGirlEnthusiast/

##### Note: If these sites change a part of their framework or functionality this script relies on, this script will not function properly, often it is just a selector change. if you come across this, feel free to fix and push or at least report the issue. The script will be repaired when available.

## **Features**
- Download options
  - Images only
  - Include attachments/videos
  - Include post text
- Resume interrupted scans/downloads
- Update previous scans/downloads (see notes if last download used EGirlEnthusiast's script)
- Drag & Drop folder to script for easy resume/update
- Pass URL as parameter for scripted use (downloads attachments/videos/text by default)
- Pass folder as parameter for scripted update use

## **Installation**
The following dependencies are required:
- BeautifulSoup4
- Requests
- More-itertools
- sqlalchemy

Install the dependencies like this
```
pip install bs4
pip install requests
pip install more-itertools
pip install sqlalchemy
```

## **Running**

If \*.py files are associated with python, you can just double click the script (or drag/drop folders on it to update)

Otherwise, for windows, 'cd' to this scripts file directory in command prompt and use:
```
python.exe party-scraper.py
```
That will create a prompt for a URL

## **Commands**
|   |   |
| --- |--- |
|Interactive:|```party-scraper.py```|
|Just Download:|```party-scraper.py URL```|
|Resume/Update:|```party-scraper.py folder```|
Note: 'Just Download' (using the URL parameter) uses the following defaults: folder name = service-user, download attachments/videos/text, scan/download immediately.

## **URL Formatting**
```
https://coomer.party/service/user/username
https://kemono.party/service/user/number
```
**For Example**
```
https://coomer.party/onlyfans/user/belledelphine
```
or
```
https://kemono.party/patreon/user/42747530
```
Note: Include https prefix & no text after creator name/number

## **Notes**
- Download order: newest to oldest (because of how the sites display the links).
- Files named as follows: [post#]\_[image#].extension or [post#]\_[image#]\_[filename].extension so they sort in the order they where posted (not all services use sequential numbering though).
- This script creates a few hidden files in the selected download directory to facilitate it's functionality, see header of script for details.
- Posts that incur download errors get put in .errors.txt, re-run the script to retry (all files for that post will be re-downloaded).
- To update previous scan/download from EGirlEnthusiast's script (folder has 'Entry List.txt' instead of hidden txt files): try renaming 'Entry List.txt' to '.posts.txt' and adding a file '.source.txt' with just the URL as it's contents, then try to update.
- A list of successfully downloaded files is in .files.txt (duplicates may exist) along with original filenames from the server/html (format: post#\_image#.extension SHA256.extension filename.extension; filename is uuid_v4 in some cases and creators chosen filename in others). This file is written by the script but not used further; the plan was to check all downloads' name1 (the SHA256 hash) against .files.txt before downloading to save bandwidth and storage, but that may create gaps in naming if creators post the exact same file to multiple posts and site is de-duplicating. I kept the creation of this file around for reference purposes.

## **Tricks**
- Need to re-download a post? Remove it from .posts.txt and re-run the script against the directory.
- Need to skip a post? After scanning, cut it from .todo.txt and paste it into .posts.txt .

## **Known Issues**
- Files around 1GB and larger may fail to download
- Keyboard escape not very reliable, just send a few times to quit
- Close button not very reliable while script running, just keep clicking until it closes
- Embedded YouTube video's won't download
- Some errors may not get caught by the built-in error handlers (one known one: internet failure during download throws a long error message )

## **License**
GPLv3
