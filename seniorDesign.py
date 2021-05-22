from tkinter import *
import tkinter as tk                # python 3
from tkinter import font as tkfont  # python 3
from playsound import playsound
#import playsound
import spectrogram as sp
import math
import matplotlib
# import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import headerfile
import random
import mand_deeplearning as mdl
import viet_deeplearning as vdl
import hmong_deeplearning as hdl
import matplotlib.patches as mpatches
matplotlib.use('TkAgg')


LANGUAGES = ["Mandarin"]
MAND_TONES = ["1", "2", "3", "4"]
MAND_WORDS = headerfile.mandWords
MAND_VOICES = ["Male #1", "Male #2", "Male #3", "Female #1", "Female #2", "Female #3"]

'''To be expanded with the following'''
#LANGUAGES = ["Mandarin", "Vietnamese", "Hmong"]
# VIET_TONES = ["Level", "Deep", "Sharp", "Heavy", "Asking", "Tumbling"]
# viet_tone = {
#     VIET_TONES[0]: 0,
#     VIET_TONES[1]: 1,
#     VIET_TONES[2]: 2,
#     VIET_TONES[3]: 3,
#     VIET_TONES[4]: 4,
#     VIET_TONES[5]: 5,
# }


# VIET_WORDS = [headerfile.vietWordsLevel, headerfile.vietWordsDeep,
#               headerfile.vietWordsSharp, headerfile.vietWordsHeavy,
#               headerfile.vietWordsAsking, headerfile.vietWordsTumbling]
# HMONG_TONES = ["B", "_", "S", "J", "V", "M", "G"]
# HMONG_WORDS = headerfile.hmongWords





color = "#e4f7f2" #light blue
skyblue = "#bff9ff"     # color of the text boxes
highlighter = "#f8ffb5"     # color of next option to select
hovering = "#f9ff52"    # when you hover an option menu


class ToneLearner:
    def __init__(self, master):
        self.master = master

        self.master.title("Pronunciation Tool for Learning Tonal Languages")
        self.master.bind('<Configure>', self.resize)
        self.master.configure(bg="white")

        self.title_font = tkfont.Font(self.master, family="Helvetica", size=18, weight="bold")
        self.button_font = tkfont.Font(family="Arial")
        self.text_font = tkfont.Font(family="Arial")
        self.feedback_font = tkfont.Font(family="Arial", slant="italic")
        self.center_x_offset = tk.DoubleVar()   # these variables used for re-centering text when the window is resized
        self.center_y_offset = tk.DoubleVar()

        # self variable initialization
        self.last_language = "Select language"
        self.last_tone = ""
        self.current_word = ""
        self.last_voice = ""
        self.countdown_active = False
        self.feedback_lines = [""]*6
        self.current_fb_line = 0

        # Change these weights to make some rows/columns larger than others
        self.numRow = 8
        self.numCol = 8
        for i in range(self.numRow):
            self.master.rowconfigure(i, weight=1)
        for i in range(self.numCol):
            if i >= 2:  # These 6 will only take up the right half (must have same weight as left half below)
                self.master.columnconfigure(i, weight=1)    # 2 buttons -> 3 cols each, 3 buttons -> 2 cols each
            if i < 2:
                self.master.columnconfigure(i, weight=3)

        # Initialize the canvases that you can display text and add other widgets to
        # Plain text boxes
        self.language_text, self.language_text_label = self.create_canvas(f"Language", (0, 0))
        self.tone_text, self.tone_text_label = self.create_canvas(f"Tone", (1, 0))
        self.word_text, self.word_text_label = self.create_canvas(f"Word", (2, 0))
        self.voice_text, self.voice_text_label = self.create_canvas(f"Voice", (3, 0))
        self.predicted_text, self.predicted_text_label = self.create_canvas(f"Predicted Tone", (4, 0))
        self.score_text, self.score_text_label = self.create_canvas(f"Score", (5, 0))
        self.countdown_canvas, self.countdown_label = self.create_canvas(f"", (0, 5), span=(1, 3))
        self.feedback, self.feedback_label = self.create_canvas("", (6, 0), span=(2, 8),
                                                                font=self.feedback_font, size=(80, 500))
        # Colored text boxes
        self.score_output, self.score_output_label = self.create_canvas(f"", (5, 1), bg=color)
        self.predicted_output, self.predicted_output_label = self.create_canvas(f"", (4, 1), bg=color)
        # Dropdown buttons
        # Language needs to be selected first - highlight it!
        self.language_button, self.language = self.create_dropdown((0, 1), options=LANGUAGES,
                                                                   callback=self.language_changed, bg=highlighter,
                                                                   default="Select language")
        self.tone_button, self.tone = self.create_dropdown((1, 1), callback=self.tone_changed,
                                                           default="")
        self.voice_button, self.voice = self.create_dropdown((3, 1), callback=self.voice_changed,
                                                             default="")
        # Search bar initialization - need a background, frame, searchbar itself, and a word variable
        self.searchbar_bg, throwaway = self.create_canvas(f"", (2, 1))
        self.search_bar_frame = tk.Frame(self.master, relief=tk.GROOVE)
        self.search_bar_frame.grid(row=2, column=1)
        self.search_bar = self.SearchBar(self.search_bar_frame, [], self.button_font)
        self.word = self.search_bar.get_trace()
        self.word.trace("w", self.word_changed)

        self.current_word_canvas, self.current_word_label = self.create_canvas("", (0, 2), span=(1, 3))

        self.current_word_meaning_canvas, self.current_word_meaning_label = self.create_canvas("", (1, 2), span=(1, 6))

        # Push buttons
        self.play_button = self.create_button("Play", (2, 2), span=(1, 3), command=lambda: self.play())
        self.record_button = self.create_button("Record", (2, 5), span=(1, 3), command=lambda: self.record())
        self.next_button = None     # Only show this once Shuffle mode is entered
        # Plot
        self.plot_spectrograms([], [], [], [])

    # This is called whenever the main window is moved or resized - use for configuring text size/placement
    def resize(self, event):
        if event.type == '22':  # Configure (resize)
            # using the appropriate width:height ratio, constrain the text size to the smaller of the two
            textbox_constraint = int(min(self.language_text.winfo_width()/4, self.language_text.winfo_height()))
            button_constraint = int(min(self.language_button.winfo_width()/12, self.language_button.winfo_height()/1.5))
            feedback_constraint = int(min(self.feedback.winfo_width()/16, self.feedback.winfo_height()/2.4))

            self.text_font['size'] = int(textbox_constraint / 3)
            self.button_font['size'] = int(math.sqrt(button_constraint * 8))
            self.feedback_font['size'] = int(feedback_constraint/4)

            # set text coords to center
            canvasArray = [(self.countdown_canvas, self.countdown_label),
                           (self.current_word_canvas, self.current_word_label),
                           (self.language_text, self.language_text_label), (self.tone_text, self.tone_text_label),
                           (self.word_text, self.word_text_label), (self.voice_text, self.voice_text_label),
                           (self.predicted_text, self.predicted_text_label),
                           (self.predicted_output, self.predicted_output_label),
                           (self.score_text, self.score_text_label), (self.score_output, self.score_output_label),
                           (self.current_word_meaning_canvas, self.current_word_meaning_label)]
            for canvas_label in canvasArray:
                canvas_label[0].coords(canvas_label[1], (canvas_label[0].winfo_width()/2,
                                                         canvas_label[0].winfo_height()/2))

    # Called when a language is selected
    def language_changed(self, *args):
        language = self.language.get()
        if language == self.last_language:
            return
        self.last_language = language
        self.language_button.config(bg=color)
        self.searchbar_bg.config(bg=color)
        self.tone_button.destroy()
        self.voice_button.destroy()
        self.current_word_canvas.itemconfig(self.current_word_label, text="")
        self.current_word_meaning_canvas.itemconfig(self.current_word_meaning_label, text="")
        if self.language.get() == "Mandarin":
            # Remake the tone, voice, and word buttons with Mandarin tones/voices/words
            self.tone_button, self.tone = self.create_dropdown((1, 1), options=MAND_TONES, callback=self.tone_changed,
                                                               bg=highlighter, default="Select Tone")
            self.voice_button, self.voice = self.create_dropdown((3, 1), options=MAND_VOICES,
                                                                 callback=self.voice_changed)
            self.search_bar.des()
            self.search_bar_frame = tk.Frame(self.master, relief=tk.GROOVE)
            self.search_bar_frame.grid(row=2, column=1)
            self.search_bar = self.SearchBar(self.search_bar_frame, MAND_WORDS, self.button_font)
            self.word = self.search_bar.get_trace()
            self.word.trace("w", self.word_changed)


    # Called whenever tone is changed
    def tone_changed(self, *args):
        self.last_tone = self.tone.get()
        self.tone_button.config(bg=color)
        if self.language.get() == "Mandarin":
            if self.word.get() == "":
                self.searchbar_bg.config(bg=highlighter)
            else:
                self.current_word_canvas.itemconfig(self.current_word_label,
                                                    text=str(self.current_word) + " " + self.tone.get())
                self.current_word_meaning_canvas.itemconfig(self.current_word_meaning_label, text=self.pinyin_to_char())


    # Called whenever word is changed
    def word_changed(self, *args):
        self.current_word = self.word.get()
        self.searchbar_bg.config(bg=color)
        self.current_word_canvas.itemconfig(self.current_word_label, text=str(self.current_word) + " " + self.tone.get())
        
        if self.language.get() == "Mandarin":
            self.current_word_meaning_canvas.itemconfig(self.current_word_meaning_label, text=self.pinyin_to_char())
    
           
        if self.next_button is not None:
            self.next_button.destroy()
            self.next_button = None
            self.record_button.destroy()
            self.record_button = self.create_button("Record", (2, 5), span=(1, 3), command=lambda: self.record())
            self.play_button = self.create_button("Play", (2, 2), span=(1, 3), command=lambda: self.play())
            


    # Unused for now; we don't need to do anything for voice changes
    def voice_changed(self, *args):
        pass

    # Creates new TK canvas in the selected location and initializes with some text
    def create_canvas(self, text, coordinates, span=(1, 1), bg=color, relief=tk.RAISED, font=None, size=(40, 250)):
        anchor = "nw"   # for Feedback. Could add anchor to the parameters of this function
        if font is None:
            font = self.text_font
            anchor = "center"

        canvas = tk.Canvas(bg=bg, relief=relief, height=size[0], width=size[1], bd=1)
        label = canvas.create_text((10, 10), anchor=anchor, text=text, font=font)
        canvas.grid(row=coordinates[0], column=coordinates[1], rowspan=span[0], columnspan=span[1], padx=0, pady=0,
                    sticky="nsew")
        return canvas, label    # Returns pointers to the canvas itself as well as the text item

    # Creates the dropdown selection menu for language, tone, voice
    def create_dropdown(self, coordinates, options=("",), callback=None,  span=(1, 1), bg=color, relief=tk.RAISED,
                        textcolor=None, default=None):
        var = tk.StringVar()
        if default is None:
            default = options[0]
        var.set(default)
        var.trace("w", callback)
        button = tk.OptionMenu(self.master, var, *options)
        button.grid(row=coordinates[0], column=coordinates[1], rowspan=span[0], columnspan=span[1], padx=0, pady=0,
                    sticky="nsew")
        button.config(fg=textcolor, bg=bg, relief=relief, activebackground=hovering, font=self.button_font)
        return button, var
        # Returns the button background and the variable pointer
        # get the selected value with var.get(), set with var.set()

    # Creates pushbutton for play, record
    def create_button(self, text, coordinates, span=(1, 1), command=None, font=None, relief=tk.RAISED, bg=None):
        if font is None:
            font = self.button_font
        # if bg is None:
        #     bg = "gray"
        button = tk.Button(self.master, text=text, font=font, width=len(text), relief=relief, command=command, bg=bg)
        button.grid(row=coordinates[0], column=coordinates[1], padx=0, pady=0, sticky="nsew", rowspan=span[0],
                    columnspan=span[1])
        return button

    # Plots the two spectrograms in the same window as the main application
    def plot_spectrograms(self, xref, yref, xusr, yusr):
        fig = Figure(figsize=(1, 1), constrained_layout=True)
        a = fig.add_subplot(111, frameon=False)
        a.scatter(xref, yref, color='green')
        a.scatter(xusr, yusr, color='red')
        # a.set_title("Title", fontsize=12)
        # Remove X and Y ticks
        a.set_yticks([])
        a.set_xticks([])
        a.set_xlim([0, 60])
        a.set_ylim([50, 150])
        user_legend = mpatches.Patch(color='red', label='Your pronunciation')
        ref_legend = mpatches.Patch(color='green', label='Correct pronunciation')
        fig.legend(handles=[user_legend, ref_legend], loc='upper left', fontsize=10, borderaxespad=0, frameon=False)

        canvas = FigureCanvasTkAgg(fig, master=self.master)
        canvas.get_tk_widget().grid(row=3, column=2, padx=3, pady=3, sticky="nsew", rowspan=3, columnspan=6)
        canvas.draw()

    # Starts recording process after a [count] second delay
    def countdown(self, count):
        self.countdown_active = True
        if count > 0:
            self.countdown_canvas.itemconfig(self.countdown_label, text=str(count))
            self.master.after(1000, self.countdown, count-1)
        else:
            self.countdown_canvas.itemconfig(self.countdown_label, text="RECORDING")
            self.master.update()
            audio_file = self.get_audio_file()
            self.master.after(100, sp.record_user, self.countdown_canvas, self.countdown_label, audio_file, self)
            self.plot_spectrograms([], [], [], [])
            self.countdown_active = False
            return

    # Called when you press Record button
    def record(self):
        if "" in [self.language.get(), self.word.get(), self.tone.get()]:
            return
        if not self.countdown_active:
            self.countdown(3)

    # Returns the path for the current language, tone, voice, and word selection
    def get_audio_file(self):
        #sound = "Hmong_MP3/B Tone/aab.MP3"
        if self.language.get() == "Mandarin":
            sound = "MandarinMP3s/" + self.current_word + self.tone.get() + "_" + self.voice.get()[0] + "V" \
                    + self.voice.get()[-1] + "_MP3.mp3"
        else:
            self.countdown_canvas.itemconfig(self.countdown_label, text="")
            sound = ""
        return sound

    # Plays the currently selected audio file
    def play(self):
        if "" in [self.language.get(), self.word.get(), self.tone.get()]:
            return
        try:
            playsound(self.get_audio_file())
        except UnboundLocalError:
            self.countdown_canvas.itemconfig(self.countdown_label, text="")

    def update_score(self, score):
        self.countdown_active = False
        # TODO: maybe edit these color scales to get a better red -> green transition
        R = int((1 - score/100) * 255)
        G = int(score/100 * 255)
        B = 64
        RGB = hex((R << 16) | (G << 8) | B)
        # in case RGB is too short (not 6 characters):
        RGB = "#" + "0"*(8 - len(RGB)) + RGB[2:]
        self.score_output.itemconfig(self.score_output_label, text="Score: "+str(int(score)))
        self.score_output.config(bg=RGB)
        if self.language.get() == "Mandarin":
            predicted_tone = mdl.mand_deepL("user.mp3")
            self.predicted_output.itemconfig(self.predicted_output_label, text="Tone #" + str(predicted_tone[0]))
            if predicted_tone[0] == int(self.tone.get()):
                bg = "green"
            else:
                bg = "red"
            self.predicted_output.config(bg=bg)
        

    def pinyin_to_char(self):
        pinyin_word = self.current_word + self.tone.get()
        try:
            x = headerfile.mandarinDictionary[pinyin_word]
        except KeyError:
            x = ""
        return x


    def add_feedback(self, line):
        self.feedback_lines[self.current_fb_line] = line
        text = self.feedback_lines[self.current_fb_line] + "\n"\
            + self.feedback_lines[(self.current_fb_line - 1) % 6] + "\n"\
            + self.feedback_lines[(self.current_fb_line - 2) % 6] + "\n"\
            + self.feedback_lines[(self.current_fb_line - 3) % 6] + "\n"\
            + self.feedback_lines[(self.current_fb_line - 4) % 6] + "\n"\
            + self.feedback_lines[(self.current_fb_line - 5) % 6] + "\n"
        self.feedback.itemconfig(self.feedback_label, text=text)
        self.current_fb_line = (self.current_fb_line + 1) % 6

    # Searchable selection box for lists with many choices, i.e. Word selection
    class SearchBar:
        @staticmethod
        def create_new_list(string_given, string_list):
            new_list = []
            for string in string_list:
                if len(string_given) <= len(string):
                    if string.find(string_given) != -1:
                        new_list.append(string)
            return new_list

        def update_display_list(self):
            if self.listboxExist:
                self.m_LISTBOX.delete(0, tk.END)
                for string in self.m_list_to_display:
                    self.m_LISTBOX.insert('end', string)

        def maybe_update_display_LISTBOX(self):
            possible_new_list_to_display = self.create_new_list(self.m_text_entry_object.get(), self.m_list)

            if len(possible_new_list_to_display) == 0:
                if self.listboxExist:
                    self.delete_LISTBOX()
                return

            if possible_new_list_to_display == self.m_list_to_display:
                if self.listboxExist:
                    pass
                else:
                    self.create_LISTBOX()
                return

            if len(possible_new_list_to_display) == len(self.m_list_to_display):
                self.m_list_to_display = possible_new_list_to_display
                if self.listboxExist:
                    self.update_display_list()
                else:
                    self.create_LISTBOX()
                return

            if len(possible_new_list_to_display) >= self.m_max_element_to_display and \
               len(self.m_list_to_display) >= self.m_max_element_to_display:
                self.m_list_to_display = possible_new_list_to_display
                if self.listboxExist:
                    self.update_display_list()
                else:
                    if not self.itemInListboxSelected:
                        self.create_LISTBOX()
                return

            self.m_list_to_display = possible_new_list_to_display
            if self.listboxExist:
                self.delete_LISTBOX()
            self.create_LISTBOX()

        def func_called_when_text_change(self, event):
            self.maybe_update_display_LISTBOX()

        def focus_in_ENTRY(self, event):
            self.focusIn_ENTRY = True
            self.maybe_create_LISTBOX()

        def focus_out_ENTRY(self, event):
            self.focusIn_ENTRY = False
            self.maybe_delete_LISTBOX()

        def cursor_in_ENTRY(self, event):
            self.cursorIn_ENTRY = True

        def cursor_out_ENTRY(self, event):
            self.cursorIn_ENTRY = False

        def focus_in_LISTBOX(self, event):
            self.focusIn_LISTBOX = True

        def focus_out_LISTBOX(self, event):
            self.focusIn_LISTBOX = False
            self.maybe_delete_LISTBOX()

        def cursor_in_LISTBOX(self, event):
            self.cursorIn_LISTBOX = True

        def cursor_out_LISTBOX(self, event):
            self.cursorIn_LISTBOX = False

        def maybe_create_LISTBOX(self):
            if self.focusIn_ENTRY is True and self.listboxExist is False:
                self.create_LISTBOX()

        def maybe_delete_LISTBOX(self):
            if self.listboxExist is True and \
               self.cursorIn_LISTBOX is False and \
               self.cursorIn_ENTRY is False:
                # and self.focusIn_ENTRY == False
                self.delete_LISTBOX()

        def item_selected(self, event):
            self.itemInListboxSelected = True
            selected_item_tuple_id = self.m_LISTBOX.curselection()
            if selected_item_tuple_id != ():
                string = str(self.m_LISTBOX.get(self.m_LISTBOX.curselection()))
                self.m_text_entry_object.set(string)
            self.m_list_to_display = []
            self.delete_LISTBOX()
            self.itemInListboxSelected = False
            self.word_selected.set(string)
            # global Word
            # Word = string

        def des(self):
            self.m_FRAME.destroy()

        def create_LISTBOX(self):
            if self.listboxExist:
                return
            if self.m_LISTBOX is not None:
                return

            if len(self.m_list_to_display) == 0:
                return
            if self.m_max_element_to_display > len(self.m_list_to_display):
                nbr_of_row_to_display = len(self.m_list_to_display)
            else:
                nbr_of_row_to_display = self.m_max_element_to_display

            self.m_LISTBOX = tk.Listbox(self.m_FRAME, height=nbr_of_row_to_display)
            self.m_LISTBOX.pack()
            self.m_LISTBOX.bind("<FocusIn>", self.focus_in_LISTBOX)
            self.m_LISTBOX.bind("<FocusOut>", self.focus_out_LISTBOX)
            self.m_LISTBOX.bind("<Enter>", self.cursor_in_LISTBOX)
            self.m_LISTBOX.bind("<Leave>", self.cursor_out_LISTBOX)
            self.m_LISTBOX.bind('<<ListboxSelect>>', self.item_selected)
            self.listboxExist = True
            self.update_display_list()

        def delete_LISTBOX(self):
            if not self.listboxExist:
                return
            if self.m_LISTBOX is None:
                return
            self.m_LISTBOX.destroy()
            del self.m_LISTBOX
            self.m_LISTBOX = None
            self.list_to_display = []
            self.listboxExist = False

        def get_trace(self):
            return self.word_selected

        def __init__(self, actual_FRAME, _list, font, max_element_to_display=5):
            self.word_selected = tk.StringVar()
            self.itemInListboxSelected = False
            self.focusIn_ENTRY = False
            self.cursorIn_ENTRY = False
            self.cursorIn_LISTBOX = False
            self.listboxExist = False
            self.m_LISTBOX = None
            self.focusIn_LISTBOX = False
            self.list_to_display = None
            self.m_list = _list
            if max_element_to_display > len(_list):
                self.m_max_len_to_display = len(_list)
            self.m_max_element_to_display = max_element_to_display
            self.m_list_to_display = self.m_list
            self.m_FRAME = actual_FRAME
            self.m_text_entry_object = tk.StringVar()
            self.m_text_entry_object.trace("w", lambda name, index, mode,
                                           x=self.m_text_entry_object: self.func_called_when_text_change(x))
            self.m_ENTRY = tk.Entry(self.m_FRAME, textvariable=self.m_text_entry_object,
                                    font=font)
            self.m_ENTRY.pack(side=tk.TOP)

            self.m_ENTRY.bind("<FocusIn>", self.focus_in_ENTRY)
            self.m_ENTRY.bind("<FocusOut>", self.focus_out_ENTRY)
            self.m_ENTRY.bind("<Enter>", self.cursor_in_ENTRY)
            self.m_ENTRY.bind("<Leave>", self.cursor_out_ENTRY)

            self.m_LISTBOX = None


root = tk.Tk()

app = ToneLearner(root)

root.mainloop()
