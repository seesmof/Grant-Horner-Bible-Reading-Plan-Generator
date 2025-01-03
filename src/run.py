import os
import json
from todoist_api_python.api import TodoistAPI

from data import PLAN_LISTS_WITH_BOOK_NUMBERS as lists_data, TODOIST_API_KEY
from data import BIBLE_BOOK_NUMBER_TO_NUMBER_OF_CHAPTERS as chapter_counts
from data import BIBLE_BOOK_NUMBER_TO_UKRAINIAN_NAME as Ukrainian_Book_names
from data import BIBLE_BOOK_NUMBER_TO_SHORT_ABBREVIATION as English_Book_names
from data import BIBLE_BOOK_NUMBER_TO_TINY_ABBREVIATION as eBible_abbreviations

root=os.path.dirname(os.path.abspath(__file__))
results=os.path.join(root,"..","example")
data_file_path=os.path.join(root,"data.json")
cache_file_path=os.path.join(root,"cache.json")
try:
    with open(cache_file_path,'r') as f:
        cache=json.load(f)
except:
    cache={}

def get_next_reading_for_list(
    list_index:int,
    Book_index:int,
    chapter_number:int
):
    # Get a list of Book numbers for current list
    list_data=lists_data[list_index]

    # Get a Book number from the selected list
    Book_number = list_data[Book_index]

    # Get a number of available chapters for the current Book
    available_chapters = chapter_counts[Book_number]

    # Check if there are more chapters to read for this Book
    if chapter_number < available_chapters:
        # If so, move to the next chapter
        chapter_number += 1

    # If there are no more chapters for the current Book
    else:
        # Then set a chapter into 1 since wee will be moving to the next Book
        chapter_number = 1

        # Now check if there are move Books in a list
        if Book_index < len(list_data)-1:
            # If so then move to the next Book
            Book_index += 1
        
        # If there are no more Books to read from in a list
        else:
            # Then restart the list and read the first Book
            Book_index = 0

    return Book_index,chapter_number

def get_reading_for_day(
    day_number:int,
):
    if cache.get(str(day_number)) and day_number:
        return cache[str(day_number)]

    # Will be forming a list of tuples
    # Each tuple will contain: Bible Book Number, and a Chapter Number
    reading_data=[]
    previous_day_data=cache[str(day_number-1)]

    # Form readings for of the 10 lists
    for list_index in range(10):
        list_data=lists_data[list_index]
        Book_number,chapter_number=previous_day_data[list_index]
        Book_index=list_data.index(Book_number)
        Book_index,chapter_number=get_next_reading_for_list(list_index,Book_index,chapter_number)
        reading_data.append((list_data[Book_index],chapter_number))

    if day_number not in cache.keys() and day_number:
        cache[str(day_number)]=reading_data
    
    # And return the formed list
    return reading_data

def get_eBible_reading_link(
    Book_number:int,
    chapter_number:int,
):
    # This is how a typical eBible.org reading link looks like
    base_link = "https://ebible.org/study/?w1=bible&t1=local%3A"

    # Version can be later changed as a parameter
    translation_abbreviation = 'ukr1871'
    # Form a Bible Book Abbreviation specific to eBible.org, data taken from a constant variable
    Book_name_abbreviation = eBible_abbreviations[Book_number]
    # Form a link in a format that eBible.org uses
    ready_link = f'{base_link}{translation_abbreviation}&v1={Book_name_abbreviation}{chapter_number}'

    # And return it back to the user 
    return ready_link

def get_Bolls_reading_link(Book,chapter):
    base='https://bolls.life/HOM'
    ready=f'{base}/{Book}/{chapter}/'
    return ready

def get_formatted_link(
    Book_number:int,
    chapter_number:int,
    language:str='EN',
    link_type:str='MD'
):
    reading_link=get_eBible_reading_link(Book_number,chapter_number)
    Book_name=Ukrainian_Book_names[Book_number] if language=='UK' else English_Book_names[Book_number]
    return f'[{Book_name} {chapter_number}]({reading_link})' if link_type=='MD' else f'<a href="{reading_link}">{Book_name} {chapter_number}</a>'

def todoist_add_daily_reading(
    given_day:int=None
):
    todoist=TodoistAPI(TODOIST_API_KEY)
    tasks=todoist.get_tasks()

    def check_available_tasks(
        task_name:str,
        parent:int=None,
    ):
        return [
            t for t in tasks 
            if task_name in t.content 
            and (t.parent_id==parent if parent else True)
        ]
    
    def add_unique_task(
        task_name:str,
        parent:int=None,
        due:str=None,
    ):
        duplicates=check_available_tasks(task_name,parent)
        new_task=todoist.add_task(task_name,parent_id=parent,due_string=due) if not duplicates else duplicates[0]
        return new_task
    
    with open(data_file_path,'r') as f:
        data=json.load(f)
    day=data['day'] if not given_day else given_day

    main_task_name=f'Біблія {day}'
    parent_id=add_unique_task(main_task_name,due='today').id

    reading_list=get_reading_for_day(day)
    for Book_number,chapter_number in reading_list:
        add_unique_task(get_formatted_link(Book_number,chapter_number),parent_id)

    if not given_day:
        data['day']+=1
        with open(data_file_path,'w') as f:
            json.dump(data,f)

CURRENT_DAY=163
lines=[]
for day in range(CURRENT_DAY,CURRENT_DAY+366):
    plan_for_day=get_reading_for_day(day)
    for i,reading in enumerate(plan_for_day):
        Book,chapter=reading
        link=get_formatted_link(Book,chapter)
        lines.append(link+f" день {day}" if i==0 else link)
print(f'Formed links for 365 days from day {CURRENT_DAY}')

local_output_file_path=os.path.join(results,'output.txt')
vault_output_file_path=os.path.join(r'E:\Notatnyk\План.md')
with open(os.path.join(results,'output.txt'),encoding='utf-8',mode='w') as local_output_file, open(vault_output_file_path,encoding='utf-8',mode='w') as vault_output_file:
    output_lines=[l+'\n' for l in lines]
    local_output_file.writelines(output_lines)
    vault_output_file.writelines(output_lines)
