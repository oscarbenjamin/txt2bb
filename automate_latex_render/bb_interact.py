#!/usr/bin/env python3

"""
bb_interact.py
1 May 2020
Liam Wheen

Website interaction for Blackboard tests to atomate the rendering of Latex
equations without needing to manually edit/save each question.

Usage
========
This is designed for a Blackboard test once it has been uploaded but Latex
equations have not yet rendered.
Once the test is created, click its drop down menu and select 'edit test' which
will take you to the editing page in which the questions can be edited
indivually. Copy the current url of this page to your clipboard.

The file can then be run with

    python3 bb_interact.py 'Blackboard url' [--hide]

Where the blackboard url should be placed between quotations.

The optional --hide flag will run this script without opening an actual
Chrome browser but will require you to enter your login details into the
terminal rather than the secure login page directly.
"""

import time
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import sys

def login(driver):
    user = input('Please type your username: ')
    user_in = driver.find_element(By.ID, 'username').send_keys(user)

    password = input('Please type your password: ')
    pass_in = driver.find_element(By.ID, 'password').send_keys(password)

    driver.find_element(By.ID, 'submit').click()

def main(url, hide):
    options = webdriver.ChromeOptions()
    if hide:
        options.add_argument('headless');
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    
    print(driver.title)
    try:
        login_button = driver.find_element(By.ID, 'topframe.login.label').click()
        print('login found')
        if hide:
            login(driver)
            assert 'Welcome' in driver.title, '\n\n     Login failed - check login details'
        else:
            print('Please enter your login details on the page')
            print(driver.title)
            WebDriverWait(driver, 300).until(EC.title_contains('Welcome'))
        print(driver.title)
        driver.get(url)
    except NoSuchElementException as elem_error:
        print('no login')
        print('-----------------')
        raise(elem_error)

    try:
        arrow_buttons = driver.find_elements(By.XPATH, "//*[@class='contextMenuContainer']")

        # First 6 matches are not arrow buttons so start from index 6
        for i in range(6,len(arrow_buttons)):
            print('clicking on arrow')
            arrow_buttons[i].click()
            edit_buttons = driver.find_elements(By.XPATH, "//*[starts-with(@id,'modify_test')]")
            temp_adds = driver.find_elements(By.XPATH, "//*[@class='addBeforeLink']")

            assert len(edit_buttons) == 2, '\n\n    Edit button not found, run without --hide flag'
            print('clicking on edit')
            edit_buttons[0].click()
            print('----PAUSE----')
            time.sleep(1)
            try:
                submit_button = driver.find_element(By.NAME, "bottom_Submit")
            except:
                print('failed to find submit, looking for next button')
                next_button = driver.find_element(By.NAME, "bottom_Next")
                print('found next button')
                print('----PAUSE----')
                time.sleep(1)
                next_button.click()
                print('clicked next button')
                print('----PAUSE----')
                time.sleep(1)
                submit_button = driver.find_element(By.NAME, "bottom_Submit")
               
            submit_button.click()
            print('Submitted question {}/{}'.format(i-5, len(arrow_buttons)-6))
            arrow_buttons = driver.find_elements(By.XPATH, "//*[@class='contextMenuContainer']")

    except:
        print("Unknown error has occured")

    driver.close()
    return 0
    

if __name__ == '__main__':
    
    if '--hide' in sys.argv[1:]:
        hide = True
    else:
        hide = False
    sys.exit(main(sys.argv[1], hide))
