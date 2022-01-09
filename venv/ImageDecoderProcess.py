import cv2
import pytesseract
import os
from os.path import exists
import regex as re
from Ceks import Ceks
from Simple_date import SimpleDate
from multiprocessing import Process, Queue
import logging

# logging
log_formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:%(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(log_formatter)
stream_handler.setLevel(logging.INFO)
logger.addHandler(stream_handler)
file_handler = logging.FileHandler('image_decoder.log')
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.ERROR)
logger.addHandler(file_handler)

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

"""
Intended for getting data from check images
test
"""
class ImageDecoderProcess(Process):
    _resize_factor = 0.5
    _LENGTH_CHECK_DISABLED = -1
    text = ""
    # List of stores first being name second PVN code
    _store_list = [("MAXIMA", "LV40003520643"),
                   ("RIMI", "LV40003053029"),
                   ("TOPS", "789")]
    _MAXIMA_NR = 0
    _RIMI_NR = 1
    _TOPS_NR = 2
    _UNKNOWN_NR = 100
    # List of tupples for searching different data in different stores
    # 1 = String to search for
    # 2 = next is allowable faults
    # 3 = expected min length
    _SASIJAS_KEYWORDS = [('Šas. Nr.', 1, 4),
                         ('Šasijas numurs:', 7, 4),
                         ('Šasijas numurs:', 7, 4),
                         ('S/N:', 1, 4)]
    _CEKA_NR_KEYWORDS = [('Čeks', 1, 4),
                         ('Dok\. Nr', 2, 4),
                         ('Dok\. Nr', 2, 4),
                         ('KVĪTS Nr.', 2, 4),
                         ('Dokuments',2, 4)]
    _PVN_NR_KEYWORDS = [('PVN maksātāja kods', 8, 10),
                        ('PVN maksātāja kods', 8, 10),
                        ('PVN maksātāja kods', 8, 10),
                        ('PVN Nr.', 1, 10),
                        ('PVN ', 1, 10)]
    _SUM_KEYWORDS = [('KOPĀ:', 1, 3),
                     ('Samaksai EUR', 1, 3),
                     ('Summa:', 1, 3),
                     ('Kopā apmaksai', 5, 3),
                     ('KARTE', 1, 3),
                     ('KOPĀ EUR', 1, 3),
                     ('SAMAKSA', 1, 3),
                     ('KOPĀ', 1, 3)]

    def __init__(self, queue, image_location, image_name):
        Process.__init__(self)
        self.queue = queue
        self.config = "--psm 3"
        self.image_location = image_location
        self.image_name = image_name

    def run(self):
        ceks = self.get_check_data(self.image_location, self.image_name)
        self.queue.put(ceks)

    # Get data from check imaeg to create check object
    def get_check_data(self, image_location, image_name):
        full_name = image_location + "\\" + image_name
        self.img = cv2.imread(full_name)
        self.adjust_image()
        self.get_image_text(full_name)
        store_nr = self.determine_store()
        if store_nr < 100:
            # If store number smaller than 100, it is known, set PVN nr.
            veikals = self._store_list[store_nr][0]
            pvn_nr = self._store_list[store_nr][1]
        else:
            # PVN number needs to be found
            # pvn_nr = self.find_in_txt_after_space('PVN maksātāja kods', 8)
            pvn_nr = self.get_store_specific_data(store_nr, self._PVN_NR_KEYWORDS)
            veikals = "Nezināms"
        sasijas_nr = self.get_store_specific_data(store_nr, self._SASIJAS_KEYWORDS)
        # ceka_nr = self.find_in_txt_after_space('Dok\. Nr', 2)
        ceka_nr = self.get_store_specific_data(store_nr, self._CEKA_NR_KEYWORDS)
        # summa = self.find_in_txt_after_space('Samaksai EUR', 6)
        summa = self.get_store_specific_data(store_nr, self._SUM_KEYWORDS)
        # datums = self.search_for_pattern('(20)\d\d[- /.](0[1-9]|1[012])[- /.](0[1-9]|[12][0-9]|3[01])', 2)
        datums = self.get_date()
        ceks = Ceks(ceka_nr=ceka_nr,
                    sasijas_nr=sasijas_nr,
                    veikals=veikals,
                    pvn_nr=pvn_nr,
                    summa=summa,
                    datums=datums,
                    file_name=image_name)
        return ceks

    def get_date(self):
        date_string = self.search_for_pattern('(20)\d\d[- /.](0[1-9]|1[012])[- /.](0[1-9]|[12][0-9]|3[01])', 2)
        logger.info(f'Found date: {date_string}')
        # Remove all text before 2 so only useful date gets left
        better_string = re.sub(r'^.*?2', '2', date_string)
        return better_string

    def get_store_specific_data(self, veikals_nr, keyword_list):
        result = None
        nr_found = False
        if veikals_nr < 100:
            logger.info("Known store, searching for specific keyword:" +
                             keyword_list[veikals_nr][0])
            # Known store, search only specific string
            result = self.find_in_txt_after_space(keyword_list[veikals_nr][0],
                                                  keyword_list[veikals_nr][1],
                                                  keyword_list[veikals_nr][2])
            logger.info(f'Found: {result}')
        if result == None:
            logger.info("Did not find data by specific keyword, using all keywords")
            # Store not known or did not find with specifc search keyword
            # Loop through all of the search words
            for nr, search_word_tpl in enumerate(keyword_list):
                if nr != veikals_nr:
                    # Do not check the keyword already used with known store
                    logger.info("Searching for: " + search_word_tpl[0])
                    result = self.find_in_txt_after_space(search_word_tpl[0],
                                                          search_word_tpl[1],
                                                          search_word_tpl[2])
                    if result != None:
                        logger.info(f'Found {result}')
                        break
        if result != None:
            better_result = self.remove_new_line_chars(result)
            return better_result
        else:
            return "Nezināms"

    # search for text which is after search string seperated by spaces
    def find_in_txt_after_space(self, search_string, nr_of_faults_allowed, min_expected_length=_LENGTH_CHECK_DISABLED):
        length_check_enabled = True
        if min_expected_length < 0:
            length_check_enabled = False
        search_crit = re.compile('(%s){e<=%s}' % (search_string, str(nr_of_faults_allowed)))
        for match_obj in re.finditer(search_crit, self.text):
            logger.info(f"EXAMINING MATCH OBJECT: {search_string}")
            if match_obj != None:
                # get the string where the searched data starts
                data_plus_extra = self.text[match_obj.end():]
                if len(data_plus_extra) > 0:
                    if data_plus_extra[0] == ' ':
                        # There is a space after the search keyword
                        # Get string 2 full words with space between them, removing starting space
                        search_crit_2w = re.compile("^\S*\s+(\S+)")
                        match_obj = re.search(search_crit_2w, data_plus_extra)
                        found_data = match_obj.group(0)
                        # Split string with whitespaces
                        list_of_strings = re.split("\\s+", found_data)
                        result = list_of_strings[1]
                    else:
                        # There is no space after the search word, so no need to search for next word after space
                        # Get text until first space
                        data_list = re.split("\\s+", data_plus_extra, maxsplit=1)
                        result = data_list[0]
                    if length_check_enabled:
                        # Check if found result is at least the min length
                        if len(result) >= min_expected_length:
                            # Result length acceptable, return
                            return result
                    else:
                        # Length check not enabled return first found result
                        return result
        logger.info(f"Did not find search word: {search_string}")
        return None


    def search_for_pattern(self, pattern_string, nr_of_faults_allowed):
        search_crit = re.compile('(%s){e<=%s}' % (pattern_string, str(nr_of_faults_allowed)))
        match_obj = re.search(search_crit, self.text)
        if (match_obj != None):
            logger.info("Found pattern")
            found_pattern = match_obj.group(0)
            return found_pattern
        else:
            logger.warning("Did not find pattern")
            return None

    def remove_new_line_chars(self, string):
        better_string = string.split(sep='\\n', maxsplit=1)
        return better_string[0]

    def check_if_exists_in_text(self, search_str, allowable_faults):
        search_crit = re.compile('(%s){e<=%s}' % (search_str, str(allowable_faults)))
        match_obj = re.search(search_crit, self.text)
        if match_obj != None:
            return True
        else:
            return False

    """
    Returns store number if it isrecognised by the app, else returns unknown constant
    """
    def determine_store(self):
        logger.info("Determening store")
        for nr, item in enumerate(self._store_list):
            # Loop through stores that we know  and check if check from tht store
            logger.info("Checking if store is " + item[0])
            if self.check_if_exists_in_text(item[0], 1):
                # Found store name in check return it
                # Return store number
                logger.info("Store is " + item[0])
                return nr
        return self._UNKNOWN_NR

    def adjust_image(self):
        self.img = cv2.resize(self.img, None, fx=self._resize_factor, fy=self._resize_factor)
        self.img = cv2.cvtColor(self.img, cv2.COLOR_BGR2GRAY)
        self.img = cv2.adaptiveThreshold(self.img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 85, 11)

    def show_image(self):
        cv2.imshow('Image', self.img)

    def get_image_text(self, picture_name):
        # Create picture text file name
        base_pic_name = os.path.basename(picture_name)
        wo_extension = os.path.splitext(base_pic_name)[0]
        pic_text_f_name = wo_extension + ".txt"
        file_exists = exists(pic_text_f_name)
        if (file_exists):
            # text file already created for this picture
            logger.info("Text file exists reading that")
            with open(pic_text_f_name, encoding="utf8") as f:
                temp_text = f.readlines()
            self.text = str(temp_text)
        else:
            logger.info("Text file does not exists, creating")
            # crete text from image and save
            self.text = pytesseract.image_to_string(self.img, lang="lav")
            self.create_text_file(pic_text_f_name)
            pass

    def create_text_file(self, file_name):
        with open(file_name, "w") as text_file:
            text_file = open(file_name, "w", encoding="utf8")
            text_file.write(self.text)

    def print_text(self):
        print(self.text)

