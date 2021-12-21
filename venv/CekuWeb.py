import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
import regex as re
from Ceks import Ceks
from Simple_date import SimpleDate
import os
import os.path
import shutil
import sys

# Class for interracting with the check lottery web page
class CekuWeb:
    driver = webdriver
    driverOptions = None
    web_page = "https://cekuloterija.lv/"
    # Month names for date field
    _month_names = ['Janvāris',
                    'Februāris',
                    'Marts',
                    'Aprīlis',
                    'Maijs',
                    'Jūnijs',
                    'Jūlijs',
                    'Augusts',
                    'Septembris',
                    'Oktobris',
                    'Novembris',
                    'Decembris']

    def __init__(self):
        self.driver = webdriver.Chrome(executable_path='C:/Users/Boo Boo/Documents/PythonRelated/chromedriver.exe',
                                       chrome_options=self.driverOptions)

    def open(self):
        # Open page and enter credentials
        self.driver.get(self.web_page)
        self.driver.maximize_window()
        # Allow cookies
        cookies_btn = self.driver.find_element_by_xpath("//*[text()='Piekrītu']")
        cookies_btn.click()
        
    def get_web_status(self):
        return self.driver.session_id

    def open_first_time(self):
        self.open()
        self.click_open_check_form()

    def click_open_check_form(self):
        # Open Register check form
        check_btn = self.driver.find_element_by_xpath("//button[@aria-label='Saite čeku reģistrēšanai']")
        # Must be done like this, otherwise returns element not interractable exception
        self.driver.execute_script("arguments[0].click();", check_btn)

    def register_check(self, check, phone_number):
        """
        @type check: Ceks
        """
        # Check if chrome driver opened already,
        # By default the URL whn nothing opened is "data:,"
        if len(self.driver.current_url) < 10:
            print("Web driver opened for the first time, open the webpage and start from beginning")
            self.open_first_time()
        elif self.driver.current_url == 'https://cekuloterija.lv/':
            # Check if we finished registering the previous check in which case press the next check button
            #<button class="sc-bdVaJa dgQslF sc-gFaPwZ dCMARx">Iesniegt vēl vienu čeku</button>
            another_check_xpath = "//button[contains(text(), 'Iesniegt vēl vienu čeku')]"
            if self.check_exists_by_xpath(another_check_xpath):
                next_check_btn = self.driver.find_element_by_xpath(another_check_xpath)
                next_check_btn.click()
            else:
                # No next cheeck button to press, atempt to open the check form
                self.click_open_check_form()
        else:
            self.open_first_time()
        self.fill_in_data(check,phone_number)

    def check_exists_by_xpath(self, xpath):
        try:
            self.driver.find_element_by_xpath(xpath)
        except NoSuchElementException:
            return False
        return True


    def fill_in_data(self,check, phone_number):
        # Write check data
        PVN_input_el = self.driver.find_element_by_name("taxpayer_number")
        PVN_input_el.send_keys(check.pvn_nr)
        kases_nr_input_el = self.driver.find_element_by_name("cash_register_number")
        kases_nr_input_el.send_keys(check.sasijas_nr)
        check_number_input_el = self.driver.find_element_by_name("number")
        check_number_input_el.send_keys(check.ceka_nr)
        check_sum_input_el = self.driver.find_element_by_name("amount")
        check_sum_input_el.send_keys(check.summa)
        phone_input_el = self.driver.find_element_by_name("phone")
        phone_input_el.send_keys(phone_number)
        self.input_date(check.datums)
        
    def input_date(self, date_string):
        # Search for any char that is not a number
        match_obj = re.search(r'\D', date_string)
        # find char that splits the date ints
        date_obj = None
        if (match_obj != None):
            splitting_char = match_obj.group(0)
            # Split date string in year, month and day and create simple date object
            split_date_string = date_string.split(sep=splitting_char, maxsplit=3)
            date_obj = SimpleDate(split_date_string[0], split_date_string[1], split_date_string[2])
            date_with_dot = date_string.replace(splitting_char, '.')
            print(date_with_dot)
        else:
            print("Did not find splitting char")
        # MuiPickersSlideTransition-transitionContainer MuiPickersCalendarHeader-transitionContainer
        date_field = self.driver.find_element_by_xpath(
            "//div[@class='MuiInputBase-root MuiOutlinedInput-root jss36 jss40 MuiInputBase-fullWidth "
            "MuiInputBase-formControl MuiInputBase-adornedEnd MuiOutlinedInput-adornedEnd']")
        date_field.click()
        self.driver.implicitly_wait(1)
        # Get the name of the month. Written like this "Novembris 2021"
        month_year_parrent = self.driver.find_element_by_xpath(
            "//div[@class='MuiPickersSlideTransition-transitionContainer MuiPickersCalendarHeader-transitionContainer']")
        month_year_el = month_year_parrent.find_element_by_xpath(".//*")
        correct_month = self.check_if_correct_month(month_year_el.text, date_obj)
        if not correct_month:
            # The correct month was not opened in the calendar
            # Attemt to go back one month and check again
            prev_month_button = self.driver.find_element_by_xpath(
            "//button[@class='MuiButtonBase-root MuiIconButton-root MuiPickersCalendarHeader-iconButton']")
            prev_month_button.click()
            month_year_el = month_year_parrent.find_element_by_xpath(".//*")
            correct_month = self.check_if_correct_month(month_year_el.text, date_obj)
        if correct_month:
            curren_day_field = self.driver.find_element_by_xpath("//span[text()='" + str(date_obj.date) + "']")
            # curren_day_field = self.driver.find_element_by_xpath("//span[text()='" + '5' + "']")
            parrent_el = curren_day_field.find_element_by_xpath('..')
            self.driver.execute_script("arguments[0].click();", parrent_el)

    def check_if_correct_month(self, date_str_web, date_obj):
        """
        @type date_obj: SimpleDate
        """
        # Month in web written like: "Novembris 2021"
        print('Web month name: ' + date_str_web)
        month_name = self._month_names[date_obj.month - 1]
        date_str_current = month_name + ' ' + str(date_obj.year)
        if date_str_current == date_str_web:
            print("Correct month opened")
            return True
        else:
            print("Incorret month selected")
            return False






"""
Selenieum notes
*wait until element becomes clickable
element = WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH,
                        "//button[@aria-label='Saite čeku reģistrēšanai']")))
*check if element clickable
# print("Element is visible? " + str(elem.is_displayed()))    
*wait
self.driver.implicitly_wait(20)                    
"""