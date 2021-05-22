from os import listdir
from os.path import isfile, join
import os
import numpy as np
import unicodedata
from ast import literal_eval
import unidecode


# This function lists out all the Mandarin words in the path to copy and past into class ListPage self.mandWords

def hmong_list_names():
    path = "HmongMP3s/_ Tone"
    files = [f for f in listdir(path) if isfile(join(path, f))]
    for filename in files:
        print('"', end='')
        print(filename[:-4], end='')
        print('",', end='')

def mand_list_names():
    path = "MandarinMP3s"
    files = [f for f in listdir(path) if isfile(join(path, f))]
    for filename in files:
        if filename[-13:] == "1_MV1_MP3.mp3":
            print('"', end='')
            print(filename[:-13], end='')
            print('",', end='')


# This function renames all the Vietnamese words of one tone to a standard format
def viet_rename_files():
    path = "VietnameseMP3s/tumbling - ngã"
    files = [f for f in listdir(path) if isfile(join(path, f))]
    for filename in files:
        word_index = filename.rfind(" ") + 1
        end_index = filename.rfind(".")
        file = path + "/" + filename
        if filename[word_index:end_index] == "":
            continue
        new_file = "VietnameseMP3s/tumbling_" + (filename[word_index:end_index].encode('ascii', 'xmlcharrefreplace')).decode() + ".MP3"
        # print(file, new_file)
        os.rename(file, new_file)



# Lists out Vietnamese words
# path: input, string of folder, e.g. "VietnameseMP3s"
# tone: input, string of tone, e.g. "asking"
def viet_list_names(path, tone):
    # path = "VietnameseMP3s"
    tone_length = len(tone)
    files = [f for f in listdir(path) if isfile(join(path, f))]
    for filename in files:
        if filename[:tone_length] == tone:
            print('"', end='')
            print(filename[tone_length+1:-4], end='')
            print('", ', end='')


def test_mse_method(ref_indexes, user_indexes):
    # init mean squared error
    MSE = 0
    if len(ref_indexes) > len(user_indexes):                 # take the array with more points and shrink it
        larger_array = ref_indexes
        smaller_array = user_indexes
    else:
        larger_array = user_indexes
        smaller_array = ref_indexes
    fraction_to_keep = len(larger_array)/len(smaller_array)             # have to keep this many elements
    mask = (fraction_to_keep * np.arange(len(smaller_array))).astype(int)
    larger_array = larger_array[mask]                                   # don't delete the indexes of [mask]
    for i in range(len(larger_array)):                                  # lengths should be Exactly the same here
        MSE += (larger_array[i] - smaller_array[i]) ** 2                # Both frequency arrays are already normalized
    MSE /= len(larger_array)                                            # get the mean of the square errors
    pronunciation_score = -(MSE/4) + 100                                # convert to scale out of 100 (MSE > 0)
    print(MSE)
    print(max(pronunciation_score, 0))                                  # shouldn't be negative

# asdf = "Băn"
# print(asdf.encode())
# # viet_rename_files()
# # viet_list_names("VietnameseMP3s", "tumbling")
# keyword = "fēng".encode()
# pinyin = "chèng"


def str_to_char(str):
    return literal_eval("'%s'" % str)


def replace_u_v():  # ü -> v - standard for the Mandarin audio database, but unidecode.unidecode replaces ü -> u
    with open('Unihan_Readings.txt', 'r', encoding='utf8') as inputFile:
        with open('Unihan_Readings_Replaced.txt', 'w', encoding='utf8') as outputFile:
            for line in inputFile:
                for character in line:
                    if character == "ǖ":
                        outputFile.write("v1")
                    elif character == "ǘ":
                        outputFile.write("v2")
                    elif character == "ǚ":
                        outputFile.write("v3")
                    elif character == "ǜ":
                        outputFile.write("v4")
                    elif character == "ü":
                        outputFile.write("v")
                    else:
                        outputFile.write(character)
    pass


def make_pinyin_database():
    pinyinAlreadySeen = []
    lastDefinition = ""
    lastUnicode = ""
    with open('pinyin_to_char.txt', 'w', encoding='utf8') as outputFile:
        with open('Unihan_Readings_Replaced.txt', 'r', encoding='utf8') as inputFile:
            for line in inputFile.readlines():
                try:
                    currentUnicode = line.split()[0]
                    if currentUnicode != lastUnicode:
                        lastDefinition = ""
                        lastUnicode = currentUnicode
                    if line.split()[1] == "kDefinition":
                        lastDefinition = line.split()[2:]
                    if line.split()[1] == "kMandarin":
                        pinyin = line.split()[2]
                        if pinyin in pinyinAlreadySeen:
                            continue
                        else:
                            pinyinAlreadySeen += [pinyin]
                        if len(line.split()[0][2:]) > 4:
                            character = "U+" + line.split()[0][2:]
                        else:
                            character = str_to_char("\\u" + line.split()[0][2:])
                        # print(pinyin + " " + character + " " + line.split()[0][2:] + " " + lastDefinition)
                        outputFile.write(pinyin + " " + character + " " + (' '.join(lastDefinition)) + "\n")
                except IndexError:
                    pass
    with open('pinyin_to_char.txt', encoding='utf8') as file:
        with open('pinyin_translator.txt', 'w', encoding='utf8') as file2:
            for line in file.readlines():
                tone = check_tone(line.split()[0])
                ascii_word = unidecode.unidecode(line.split()[0])
                ascii_word += str(tone)
                file2.write(ascii_word + " " + (" ".join(line.split()[1:]) + "\n"))


def check_tone(word):
    if "ā" in word or "ē" in word or "ī" in word or "ō" in word or "ū" in word:
        return 1
    if "á" in word or "é" in word or "í" in word or "ó" in word or "ú" in word:
        return 2
    if "ǎ" in word or "ě" in word or "ǐ" in word or "ǒ" in word or "ǔ" in word:
        return 3
    if "à" in word or "è" in word or "ì" in word or "ò" in word or "ù" in word:
        return 4
    else:
        return ""


def pinyin_to_char(pinyin_word=None, pinyin_tone=None):
    # if pinyin_word is None:
    #     pinyin_word = self.current_word
    #     if pinyin_tone is None:
    #         pinyin_tone = self.tone.get()
    # if pinyin_tone is None:
    #     print("asdf")
    #     pinyin_word = unidecode.unidecode(pinyin_word) + str(self.check_tone(pinyin_word))
    # else:
    pinyin_word = pinyin_word + pinyin_tone
    print(pinyin_word)
    with open('pinyin_translator.txt', 'r', encoding='utf8') as file:
        for line in file.readlines():
            if pinyin_word in line:
                return line.split()[1]
    return ""

def make_pinyin_dictionary():
    dict = {}
    with open('pinyin_to_char.txt', 'r', encoding='utf8') as file:
        for line in file.readlines():
            key = line.split()[0]
            value = " ".join(line.split()[1:])
            dict[key] = value
    print(dict)

if __name__ == "__main__":
    make_pinyin_dictionary()