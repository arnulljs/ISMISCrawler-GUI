# ISMIS Crawler by Zach Riane Machacon
# IMPROVED BY CHRYS SEAN SEVILLA
# GUI BY ARNOLD JOSEPH NAJERA

## Context
Built upon Kuya Zach and Sean's builds of this program, I'm thinking it would be more accessible and arguably easier to use with a GUI. Personal project really.

## Current ideas
I'm planning to use Kivy to build the GUI for the program and make the program open the users default browser instead of Chrome, as long as its Chromium. So theoretically it should be able to open your default Chromium browser (Edge, Opera/GX, Brave, etc.)

# How to install Selenium
- Install python at https://www.python.org/downloads/windows/
- run (python --version) at command prompt
- run (python -m pip install selenium)

## Zach Riane Machacon Progress report
January 19, 2021
- Managed to impelement authentication and scraping capability.
- Need to implement a catch function in case of site crash or incorrect credentials.

January 20, 2021
- Implemented checking for login status and site crash.
- Next plan would be to implement a checker for remaining balance for the semester.

## Chrys Sean Sevilla (Noxctis) Changes
January 3, 2025
- Implented checking if site times out or crashes and added global variable for username and password.
- Next plan is to implement scraper for the offered courses
- Next Plan is to implement scraper for remaining balance for the semester.
- ismisCrawl version 2 is hardcoded in the same file.
- needs .txt file (credentials.txt) with format for version 3 (automatically makes one if doesn't exist)
- YOUR-ISMIS-USERNAME
- YOUR-ISMIS-PASSWORD

January 8, 2025
- Implemented the Advise Course button logic
- Improved the undefined, loading, and please wait to retry logic.

January 10, 2025
- Implemented to advise the GE-FREE Electives after pressing the advise course and the retry logic.
- Implemented to display the possible schedules and their corresponding links after advising.
- Implemented function that makes it possible to also do it for separate courses as long as you know their course code. Will maybe make it user inputtable so that they can put the course code of the course they want? (line 662)
- Need to expand the list of free electives soon. (lines 425 and 523)

June 6, 2025
- Major improvements to course advising and scheduling automation:
  - Robustly handle modal dialogs for all course advising and scheduling actions, including timeouts, 'undefined', 'loading', and 'still processing' states.
  - Advise and schedule functions now check for course presence in the advised list before proceeding, and skip or retry as appropriate.
  - GE-FEL advising now properly exits after a successful advise or if the course is already advised, and will re-prompt the user only if the course cannot be advised due to schedule unavailability.
  - All schedule viewing functions print schedule details only if present, and skip rows with missing information.
  - Ensured all modals are closed after actions, preventing stuck states and repeated prompts.
- Noted code redundancy in course handling; refactoring to generalize course code logic is under consideration.
