from ImageDecoderProcess import ImageDecoderProcess
from multiprocessing import Queue
from CekuWeb import CekuWeb
import tkinter
from tkinter import *
from PIL import ImageTk, Image
from tkinter import messagebox, filedialog
from Ceks import Ceks
import glob, os
from Settings import Settings
from datetime import date
from os.path import exists
import shutil

_entry_size = 30
_target_picture_size = 1000
ui_root = None
# test
# TODO: Test functionality when registering multiple check in a row, CekuWeb.register _check function
# Date field always has different name  - use regex when searching
# Phone number is left in cells
# TODO: Add zoom, and pan for picture https://www.youtube.com/watch?v=1v9az4LMDLU
# TODO: ? Add rotate buttons  -so far everything opened fine
# TODO: ? Radio buttons for store names
# TODO: ? Create logic that checks if found store data resembles expected

def main_fc():
    main = MainClass()


class MainClass:
    # Size of UI elements
    _entry_size = 30
    _directory_entry_size = 100
    _target_picture_size = 1000
    _image_row = 2
    _image_clmn = 3
    _imaga_span = 100
    # How often does the UI process check if new check has been processed in another process
    _check_processing_dreq_ms = 500

    def __init__(self):
        """
        @type self.check: Ceks
        @type self.web: CekuWeb
        """
        # Queue to get data from image process
        self.queue = Queue()
        # Number of checks processed in the background
        self.checks_processed = 0
        self.setting = Settings()
        # List of image names without location
        self.check_image_list = []
        # Indicates whihc picture in the check_image_list is displayed in the ui
        self.current_check_displayed = -999
        self.check = None
        # If true dos not allow switching between checks
        self.processing_check_data = False
        # List of actual check objects
        self.check_list = []
        self.image = None
        # CekuWeb object for interracting with web page
        self.web = None
        self.init_empty_UI()
        # determined by radiobutton pressed
        self.phone_number_selected = 1

    # Create UI
    def init_empty_UI(self):
        self.ui_root = Tk()
        self.ui_root.title('Čeku nolasīšana')
        self.prepare_ui_elements()
        self.place_ui_elements()
        self.ui_root.mainloop()

    # Set picture of check on UI
    def set_picture(self, image_name):
        image_location = self.entry_directory_var.get() + "\\" + image_name
        image = Image.open(image_location)
        old_width, old_height = image.size
        biggest_size = old_width if old_width >= old_height else old_height
        size_coeficient = self._target_picture_size / biggest_size
        new_size = (int(old_width * size_coeficient), int(old_height * size_coeficient))
        # new_size = (int(old_height * size_coeficient), int(old_width * size_coeficient))
        image = image.resize(new_size)
        if old_width > old_height:
            image = image.rotate(270, resample=Image.BICUBIC, expand=True)
        self.image = ImageTk.PhotoImage(image)
        self.img_lbl = Label(image=self.image)
        self.img_lbl.grid(row=self._image_row, column=self._image_clmn, columnspan=self._imaga_span,
                          rowspan=self._imaga_span)

    def prepare_ui_elements(self):
        # Labels
        self.lbl_title_ceks = Label(self.ui_root, text="Čeka dati")
        self.lbl_veikals = Label(self.ui_root, text="Veikals:")
        self.lbl_veikals_no_ceka = Label(self.ui_root, text="")
        self.lbl_ceka_nr = Label(self.ui_root, text="Čeka numurs:")
        self.lbl_sasijas_nr = Label(self.ui_root, text="Šasijas numurs:")
        self.lbl_pvn_nr = Label(self.ui_root, text="PVN numurs:")
        self.lbl_summa = Label(self.ui_root, text="Summa:")
        self.lbl_datums = Label(self.ui_root, text="Datums:")
        self.lbl_directory = Label(self.ui_root, text="Čeku mape:")
        self.img_lbl = Label(self.ui_root, text="Čeka bilde")
        self.picture_opened_statuss = Label(self.ui_root, text="Spied LASĪT ČEKUS, lai sāktu")
        self.phone_nr_label = Label(self.ui_root, text="Telefona numurs reģistrācijai:")
        self.entry_ceka_nr_var = tkinter.StringVar()
        self.entry_sasijas_nr_var = tkinter.StringVar()
        self.entry_pvn_nr_var = tkinter.StringVar()
        self.entry_summa_var = tkinter.StringVar()
        self.entry_date_var = tkinter.StringVar()
        self.entry_directory_var = tkinter.StringVar()
        self.r_btn_phone_var = tkinter.IntVar()
        self.entry_directory_var.set(self.setting.check_location)
        self.status_lbl = Label(self.ui_root, text="STATUSS", bg="green")
        # phone numbers for radio buttons
        self.entry_phone_1_var = tkinter.StringVar()
        self.entry_phone_2_var = tkinter.StringVar()
        self.entry_phone_3_var = tkinter.StringVar()
        self.entry_ceka_nr = Entry(self.ui_root, width=self._entry_size, textvariable=self.entry_ceka_nr_var)
        self.entry_sasijas_nr = Entry(self.ui_root, width=self._entry_size, textvariable=self.entry_sasijas_nr_var)
        self.entry_pvn_nr = Entry(self.ui_root, width=self._entry_size, textvariable=self.entry_pvn_nr_var)
        self.entry_summa = Entry(self.ui_root, width=self._entry_size, textvariable=self.entry_summa_var)
        self.entry_date = Entry(self.ui_root, width=self._entry_size, textvariable=self.entry_date_var)
        self.entry_directory = Entry(self.ui_root, width=self._directory_entry_size,
                                     textvariable=self.entry_directory_var)
        # phone number entrys for radio buttons
        self.entry_phone_1 = Entry(self.ui_root, width=self._entry_size, textvariable=self.entry_phone_1_var)
        self.entry_phone_2 = Entry(self.ui_root, width=self._entry_size, textvariable=self.entry_phone_2_var)
        self.entry_phone_3 = Entry(self.ui_root, width=self._entry_size, textvariable=self.entry_phone_3_var)

        self.dir_btn = Button(self.ui_root, text='MAPE', command=self.dir_btn_pressed)
        self.btn_analyse_checks = Button(self.ui_root, text='LASĪT ČEKUS', command=self.btn_start_pressed,
                                         padx=20, pady=10)
        self.btn_frame = Frame(self.ui_root)
        self.btn_prev = Button(self.btn_frame, text='IEPRIEKŠĒJAIS', command=self.btn_prev_pressed,
                               padx=5, pady=5, width=15)
        self.btn_next = Button(self.btn_frame, text='NĀKOŠAIS', command=self.btn_next_pressed,
                               padx=5, pady=5, width=15)
        self.btn_register = Button(self.ui_root, text='REĢISTRĒT', command=self.btn_register_pressed,
                                   padx=10, pady=8, width=15)
        self.btn_settings = Button(self.ui_root, text='IESTATĪJUMI', command=self.btn_settings_pressed)
        self.btn_save_and_finish = Button(self.ui_root, text='BEIGT', command=self.save_and_finish,
                                          padx=10, pady=8, width=15)
        # phone selection radio buttons
        self.r_btn_phone_1 = Radiobutton(ui_root, text="", variable=self.r_btn_phone_var, value=1,
                                         command=lambda: self.r_btn_clicked(self.r_btn_phone_var.get()))
        self.r_btn_phone_2 = Radiobutton(ui_root, text="", variable=self.r_btn_phone_var, value=2,
                                         command=lambda: self.r_btn_clicked(self.r_btn_phone_var.get()))
        self.r_btn_phone_3 = Radiobutton(ui_root, text="", variable=self.r_btn_phone_var, value=3,
                                         command=lambda: self.r_btn_clicked(self.r_btn_phone_var.get()))

    def place_ui_elements(self):
        ceka_dati_start_row = 3
        phone_r_btn_start_row = ceka_dati_start_row + 7
        self.btn_analyse_checks.grid(row=0, column=0, columnspan=2)
        self.picture_opened_statuss.grid(row=1, column=0, columnspan=2)
        self.btn_frame.grid(row=2, column=0, columnspan=2)
        # Next 2 are placed in the btn_frame
        self.btn_prev.grid(row=0, column=0)
        self.btn_next.grid(row=0, column=1)
        self.lbl_title_ceks.grid(row=ceka_dati_start_row, column=0, columnspan=2)
        self.lbl_veikals.grid(row=ceka_dati_start_row + 1, column=0)
        self.lbl_veikals_no_ceka.grid(row=ceka_dati_start_row + 1, column=1)
        self.lbl_ceka_nr.grid(row=ceka_dati_start_row + 2, column=0)
        self.entry_ceka_nr.grid(row=ceka_dati_start_row + 2, column=1)
        self.lbl_sasijas_nr.grid(row=ceka_dati_start_row + 3, column=0)
        self.entry_sasijas_nr.grid(row=ceka_dati_start_row + 3, column=1)
        self.lbl_pvn_nr.grid(row=ceka_dati_start_row + 4, column=0)
        self.entry_pvn_nr.grid(row=ceka_dati_start_row + 4, column=1)
        self.lbl_summa.grid(row=ceka_dati_start_row + 5, column=0)
        self.entry_summa.grid(row=ceka_dati_start_row + 5, column=1)
        self.lbl_datums.grid(row=ceka_dati_start_row + 6, column=0)
        self.entry_date.grid(row=ceka_dati_start_row + 6, column=1)
        # Phone number radio buttons
        self.phone_nr_label.grid(row=phone_r_btn_start_row, column=0, columnspan=2)
        self.r_btn_phone_1.grid(row=phone_r_btn_start_row + 1, column=0)
        self.r_btn_phone_2.grid(row=phone_r_btn_start_row + 2, column=0)
        self.r_btn_phone_3.grid(row=phone_r_btn_start_row + 3, column=0)
        self.entry_phone_1.grid(row=phone_r_btn_start_row + 1, column=1)
        self.entry_phone_2.grid(row=phone_r_btn_start_row + 2, column=1)
        self.entry_phone_3.grid(row=phone_r_btn_start_row + 3, column=1)
        self.btn_register.grid(row=phone_r_btn_start_row + 4, column=0, columnspan=2)
        self.btn_save_and_finish.grid(row=phone_r_btn_start_row + 5, column=0, columnspan=2)
        # right side of app, folder selection and picture of check
        self.lbl_directory.grid(row=0, column=3)
        self.entry_directory.grid(row=0, column=4)
        self.dir_btn.grid(row=0, column=5)
        self.btn_settings.grid(row=0, column=6)
        self.status_lbl.grid(row=1, column=3, columnspan=3)
        self.img_lbl.grid(row=self._image_row, column=self._image_clmn, columnspan=self._imaga_span,
                          rowspan=self._imaga_span)
        self.entry_phone_1_var.set(self.setting.N1)
        self.entry_phone_2_var.set(self.setting.N2)
        self.entry_phone_3_var.set(self.setting.N3)
        self.r_btn_phone_var.set(1)

    # Phone number chosen by press of radio button
    def r_btn_clicked(self, integer):
        self.phone_number_selected = integer

    # Place check data in UI
    def place_check_data(self, ceks):
        """
        @type ceks: Ceks
        """
        self.lbl_veikals_no_ceka.config(text=ceks.veikals)
        self.entry_ceka_nr_var.set(ceks.ceka_nr)
        self.entry_sasijas_nr_var.set(ceks.sasijas_nr)
        self.entry_pvn_nr_var.set(ceks.pvn_nr)
        self.entry_summa_var.set(ceks.summa)
        self.entry_date_var.set(ceks.datums)

    # Dirrectory selection button pressed
    def dir_btn_pressed(self):
        directory = filedialog.askdirectory(initialdir="", title="Izvelies mapi ar ceku bildem")
        if (directory is not None) and (len(directory) > 0):
            self.entry_directory_var.set(directory)

    # Register check shown in UI
    def btn_register_pressed(self):
        self.get_data_from_in_fields()
        phone_nr = self.get_phone_nr_from_radio_btns()
        # delete list contents
        print("Registret pressed")
        # self.web = CekuWeb('https://cekuloterija.lv/')
        if self.web == None:
            print("self.web object does not exist, creating")
            self.web = CekuWeb()
        self.web.register_check(self.check, phone_nr)

    """
    Before opening web, read input fields with any changes that the user might have done
    @type self.check: Ceks
    """

    def get_data_from_in_fields(self):
        try:
            self.check.ceka_nr = self.entry_ceka_nr_var.get()
            self.check.sasijas_nr = self.entry_sasijas_nr_var.get()
            self.check.pvn_nr = self.entry_pvn_nr_var.get()
            self.check.summa = self.entry_summa_var.get()
            self.check.datums = self.entry_date_var.get()
        except Exception as e:
            self.show_message('Nav aizpildīti visi lauki')

    def get_phone_nr_from_radio_btns(self):
        phone_nr = 0
        radio_btn_nr = self.r_btn_phone_var.get()
        if radio_btn_nr == 1:
            phone_nr = self.entry_phone_1_var.get()
        elif radio_btn_nr == 2:
            phone_nr = self.entry_phone_2_var.get()
        elif radio_btn_nr == 3:
            phone_nr = self.entry_phone_3_var.get()
        return phone_nr

    # Start by checking image files in the selected folder
    def btn_start_pressed(self):
        if not self.processing_check_data:
            self.set_statuss('Meklē čekus mapē', "Green")
            self.processing_check_data = True
            # delete list contents
            self.check_image_list.clear()
            self.check_list.clear()
            self.checks_processed = 0
            os.chdir(self.entry_directory_var.get())
            allowed_types = ('*.jpg', '*.jpeg', "*.jfif")
            for file in allowed_types:
                self.check_image_list.extend(glob.glob(file))
            for image in self.check_image_list:
                print(image)
            self.current_check_displayed = 0
            self.process_check_new()
        else:
            self.show_message("Apstrādā iepriekšējos čekus")

    # Start bachround processed for check reading
    def process_check_new(self):
        # Regullary look if new checks are ariving from the background process
        self.ui_root.after(self._check_processing_dreq_ms, self.check_results_from_image_process)
        if self.check_image_list:
            # List not empty, star processing checks
            for file_name in self.check_image_list:
                process = ImageDecoderProcess(self.queue, self.setting.check_location, file_name)
                process.start()
        else:
            self.processing_check_data = False
            self.set_statuss("Mapē nav čeku", "Red")

    """
    # Checks are being processed in the background. Check periodically if new data returned from
    # background process
    """
    def check_results_from_image_process(self):
        print("Checking results")
        try:
            while not self.queue.empty():
                processed_check = self.queue.get(timeout=0.05)
                self.check_list.append(processed_check)
                self.checks_processed += 1
                print(f'Got check {self.checks_processed} of {len(self.check_image_list)} '
                      f'\nFile name:' + processed_check.file_name)
                self.set_statuss(f'Nolasīti {self.checks_processed} no {len(self.check_image_list)} čekiem', 'Green')
                if self.checks_processed == 1:
                    # if first check set it on UI
                    self.place_check_data(processed_check)
                    self.set_picture(processed_check.file_name)
                    status_text = "Rāda " + str(self.current_check_displayed + 1) + " no " + str(
                        len(self.check_image_list))
                    self.picture_opened_statuss.config(text=status_text)
        except Exception as e:
            print("No results yet, waiting again")
        if self.checks_processed < len(self.check_image_list):
            self.ui_root.after(self._check_processing_dreq_ms, self.check_results_from_image_process)
        else:
            self.processing_check_data = False
            self.set_statuss(f'Visi čeki apstrādāti', 'Green')

    # Open next check in UI
    def btn_next_pressed(self):
        if not self.processing_check_data:
            self.current_check_displayed += 1
            if self.current_check_displayed >= len(self.check_image_list):
                self.current_check_displayed = 0
            self.set_ui_with_current_check()
        else:
            self.show_message("Apstrādā čekus, nevar pārslēgties")

    # Open previous check in UI
    def btn_prev_pressed(self):
        if not self.processing_check_data:
            self.current_check_displayed -= 1
            if self.current_check_displayed < 0:
                self.current_check_displayed = len(self.check_image_list) - 1
            self.set_ui_with_current_check()
        else:
            self.show_message("Apstrādā čekus, nevar pārslēgties")

    def set_ui_with_current_check(self):
        status_text = "Rāda " + str(self.current_check_displayed + 1) + " no " + str(len(self.check_image_list))
        self.picture_opened_statuss.config(text=status_text)
        self.place_check_data(self.check_list[self.current_check_displayed])
        self.set_picture(self.check_list[self.current_check_displayed].file_name)

    # Open settings window
    def btn_settings_pressed(self):
        self.settings_window = Toplevel()
        self.settings_window.title('Iestatījumi')
        lbl_set_1 = Label(self.settings_window, text="Noklusējuma mape")
        lbl_set_2 = Label(self.settings_window, text="Nr. 1")
        lbl_set_3 = Label(self.settings_window, text="Nr. 2")
        lbl_set_4 = Label(self.settings_window, text="Nr. 3")
        self.entry_set_1_str = tkinter.StringVar()
        self.entry_set_2_str = tkinter.StringVar()
        self.entry_set_3_str = tkinter.StringVar()
        self.entry_set_4_str = tkinter.StringVar()
        self.entry_set_1_str.set(self.setting.check_location)
        self.entry_set_2_str.set(self.setting.N1)
        self.entry_set_3_str.set(self.setting.N2)
        self.entry_set_4_str.set(self.setting.N3)
        entry_set_1 = Entry(self.settings_window, width=50, textvariable=self.entry_set_1_str)
        entry_set_2 = Entry(self.settings_window, width=50, textvariable=self.entry_set_2_str)
        entry_set_3 = Entry(self.settings_window, width=50, textvariable=self.entry_set_3_str)
        entry_set_4 = Entry(self.settings_window, width=50, textvariable=self.entry_set_4_str)
        save_btn = Button(self.settings_window, text='SAGLABĀT UN AIZVĒRT', command=self.btn_settings_close_and_save,
                          padx=5, pady=5, width=30)
        folder_btn = Button(self.settings_window, text='...', command=self.btn_settings_folder_sel,
                            padx=5)
        lbl_set_1.grid(row=0, column=0)
        lbl_set_2.grid(row=1, column=0)
        lbl_set_3.grid(row=2, column=0)
        lbl_set_4.grid(row=3, column=0)
        entry_set_1.grid(row=0, column=1)
        entry_set_2.grid(row=1, column=1, columnspan=2)
        entry_set_3.grid(row=2, column=1, columnspan=2)
        entry_set_4.grid(row=3, column=1, columnspan=2)
        folder_btn.grid(row=0, column=3)
        save_btn.grid(row=4, column=0, columnspan=4)

    # Ask for folder selection
    def btn_settings_folder_sel(self):
        directory = filedialog.askdirectory(initialdir="", title="Noklusējuma mape")
        if (directory is not None) and (len(directory) > 0):
            self.entry_set_1_str.set(directory)
        self.settings_window.lift()

    # On close of settings save them in a file
    def btn_settings_close_and_save(self):
        self.setting.check_location = self.entry_set_1_str.get()
        self.setting.N1 = self.entry_set_2_str.get()
        self.setting.N2 = self.entry_set_3_str.get()
        self.setting.N3 = self.entry_set_4_str.get()
        self.setting.save_current_settings()
        self.settings_window.destroy()

    # Status field of app
    def set_statuss(self, text, color):
        self.status_lbl.config(text=text, bg=color)

    """
    When user closes the app by pressing the end button:
    Move all checks and text files to new folder
    """
    def save_and_finish(self):
        if (len(self.check_image_list) > 0):
            # Create folder with todays date
            today = date.today()
            date_str = today.strftime("%Y_%m_%d")
            final_folder_loc = self.create_folder(self.setting.check_location + "\\" + date_str)
            self.move_all_check_files_to_archive(final_folder_loc)
        else:
            print("No files to move exiting app")
        self.ui_root.destroy()

    # Done on end of work with app
    def move_all_check_files_to_archive(self, new_path):
        for pic_name in self.check_image_list:
            # Move image file and created text file to new folder
            pic_location = self.setting.check_location + "\\" + pic_name
            wo_extension = pic_location.split('.')[0]
            txt_location = wo_extension + ".txt"
            self.move_file_to_new_path(pic_location, new_path)
            self.move_file_to_new_path(txt_location, new_path)

    def move_file_to_new_path(self, current_path, new_path):
        file_exists = exists(current_path)
        if file_exists:
            shutil.move(current_path, new_path)
        else:
            print("File " + current_path + " does not exist")

    def create_folder(self, path):
        if os.path.exists(path):
            print("Folder exists:\r")
            number = 1
            while os.path.exists(path + "_" + str(number)):
                number += 1
            final_folder_name = path + "_" + str(number)
            os.mkdir(final_folder_name)
            return final_folder_name
        else:
            print("Folder does not exist, creating")
            os.mkdir(path)
            return path

    def show_message(self, text):
        messagebox.showwarning(title='Čeku nolasīšana', message=text)

if __name__ == "__main__":
    main_fc()
