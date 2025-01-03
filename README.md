# ISMIS Crawler by Zach Riane Machacon
# IMPROVED BY CHRYS SEAN SEVILLA

## Context
Recently, I've been fascinated by the concept of webscraping using Python. Therefore, I will be using it to my advantage to solve my laziness by letting a script view my grades for me. 

## Current ideas
I'm planning to use Selenium through a headless Chromium webdriver to do authentication for me and accessing the grades URL itself. The grades are enclosed in tables which could be parsed by the script easily with a bit of experimentation.

## Progress report
January 19, 2021
- Managed to impelement authentication and scraping capability.
- Need to implement a catch function in case of site crash or incorrect credentials.

January 20, 2021
- Implemented checking for login status and site crash.
- Next plan would be to implement a checker for remaining balance for the semester.

January 3, 2025
- Implented checking if site times out or crashes and added global variable for username and password.
- Next plan is to implement scraper for the offered courses
- Next Plan is to implement scraper for remaining balance for the semester.
- ismisCrawl version 2 is hardcoded in the same file.
- needs .txt file (credentials.txt) with format for version 3
- username=YOUR-ISMIS-USERNAME
- password=YOUR-ISMIS-PASSWORD
