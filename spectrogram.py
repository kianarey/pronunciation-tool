import parselmouth
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import sounddevice as sd
from scipy.io.wavfile import write
import mand_deeplearning as mdl
import viet_deeplearning as vdl
from pydub import AudioSegment
import librosa
import librosa.display
from dtw import dtw
from numpy.linalg import norm
import scipy.interpolate as interp


# this function extracts the pitch contour from a sound - UNUSED
def draw_pitch(pitch):
    # Extract selected pitch contour, and
    # replace unvoiced samples by NaN to not plot
    pitch_values = pitch.selected_array['frequency']
    pitch_values[pitch_values==0] = np.nan
    plt.plot(pitch.xs(), pitch_values, 'o', markersize=5, color='w')
    plt.plot(pitch.xs(), pitch_values, 'o', markersize=2)
    plt.grid(False)
    plt.ylim(0, pitch.ceiling)
    plt.ylabel("fundamental frequency [Hz]")


# normalize helper function
def normalize_freq(array):
    normalized = []
    try:
        ratio = 100/array[0]
        for i in array:
            normalized.append(i*ratio)
    except IndexError:
        normalized = [0]
    return normalized


# function that extracts frequencies from the pitch contour.
def get_frequencies(pitch):
    # calling to_array stores the pitch object into an array
    # however it has a lot of extra meta-data and we only want the frequencies
    pitch_array = pitch.to_array()
    frequencies = []
    # these for loops take only the valid frequencies from the array
    # TODO: is pitch_array[1] useful? is it metadata or stereo audio data?
    for x in pitch_array[0]:
        if x[0] > 0:
            frequencies.append(x[0])
    frequencies = np.asarray(normalize_freq(frequencies))
    return frequencies


# gets indexes of pitch contour
def get_indexes(array):
    return np.linspace(0, len(array)-1, len(array), True)


# plots the reference contour on the left, user on the right
def plot_contours(sound, frame_pointer):
    # if language == "Mandarin":
    #     mdl.mand_deepL("user.mp3")
    # elif language == "Vietnamese":
    #     vdl.viet_deepL("user.mp3")
    ref = parselmouth.Sound(sound)
    user = parselmouth.Sound("user.mp3")
    ref = ref.to_pitch().kill_octave_jumps().smooth()
    user = user.to_pitch().kill_octave_jumps().smooth()
    ref_frequencies = get_frequencies(ref)
    user_frequencies = get_frequencies(user)
    ref_indexes = get_indexes(ref_frequencies)
    user_indexes = get_indexes(user_frequencies)

    try:
        user_interp = interp.interp1d(np.arange(user_frequencies.size), user_frequencies)
    except ValueError:
        return -1
    user_stretch = user_interp(np.linspace(0, user_frequencies.size - 1, ref_frequencies.size))
    stretch_indexes = get_indexes(user_stretch)
    num_indexes = ref_frequencies.size

    MSE = 0
    for i in range(num_indexes):
        # MSE = MSE + (user_frequencies[i] - ref_frequencies[i])*(user_frequencies[i] - ref_frequencies[i])
        MSE = MSE + (user_stretch[i] - ref_frequencies[i])*(user_stretch[i] - ref_frequencies[i])
    MSE = MSE/num_indexes
    print("MSE: ", MSE)
    # convert MSE to a score between 0 and 100
    # TODO: this might just be me, but some tones are a lot easier than others. Could we change this algorithm, e.g. grade tone 1 more harshly?
    # pronunciation_score = min(max(int(-(.00002*MSE*MSE) - .09*MSE + 100), 0), 100)
    tone = frame_pointer.tone.get()
    
    if tone == "1" or tone == "Level":
        pronunciation_score = min(max(int(-(.0003*MSE*MSE) - .28*MSE + 100), 0), 100)
    if tone == "2" or tone == "Sharp":
        pronunciation_score = min(max(int(-.042*MSE + 96), 0), 100)
    if tone == "3" or tone == "Asking" or tone == "Tumbling":
        pronunciation_score = min(max(int(-.037*MSE + 100), 0), 100)
    if tone == "4" or tone == "Heavy" or tone == "Deep":
        pronunciation_score = min(max(int(-(.00007*MSE*MSE) - .041*MSE + 97), 0), 100)
    
    if pronunciation_score < 50:
        pronunciation_score = 50
    print("Score using MSE: ", pronunciation_score)
    frame_pointer.update_score(pronunciation_score)
    frame_pointer.plot_spectrograms(ref_indexes, ref_frequencies, ref_indexes, user_stretch)
    # TODO: possibly check to see how accurate and useful this is
    if pronunciation_score < 95:
        tone = frame_pointer.tone.get()
        # Find difference in pitches for beginning and end of tone to provide user feedback
        beginning_dif = computeDifference(0, int(num_indexes / 2), user_stretch, ref_frequencies)
        end_dif = computeDifference(int(num_indexes / 2), num_indexes, user_stretch, ref_frequencies)
        if tone == "1" or tone == "Level":
            frame_pointer.add_feedback("Try to keep your tone more level")

        if tone == "2" or tone == "Sharp":
            # If the beginning of the tone needs correction:
            if abs(beginning_dif) > abs(end_dif):
                if beginning_dif > 0:
                    frame_pointer.add_feedback("The beginning of your tone is too high. This tone should sound like you are asking a question")
                else:
                    frame_pointer.add_feedback("The beginning of your tone is too low. This tone should sound like you are asking a question")
            # If the end of the tone needs correction:
            else:
                if end_dif > 0:
                    frame_pointer.add_feedback("The end of your tone is too high. Try to make the change from low to high less dramatic")
                else:
                    frame_pointer.add_feedback("The end of your tone is too low. Try to make the change from low to high more dramatic as if you are asking a question")

        if tone == "3" or tone == "Asking":
            # If the beginning of the tone needs correction
            if abs(beginning_dif) > abs(end_dif):
                if beginning_dif > 0:
                    frame_pointer.add_feedback("The beginning of your tone is too high. The tone should start high, drop, and end high like a confused 'huh?'")
                else:
                    frame_pointer.add_feedback("The beginning of your tone is too low. The tone should start high, drop, and end high like a confused 'huh?'")
            # If the end of the tone needs correction
            else:
                if end_dif > 0:
                    frame_pointer.add_feedback("The end of your tone is too high. The tone should start high, drop, and end high like a confused 'huh?'")
                else:
                    frame_pointer.add_feedback("The end of your tone is too low. The tone should start high, drop, and end high like a confused 'huh?'")

        if tone == "Tumbling":
            # If the beginning of the tone needs correction
            if abs(beginning_dif) > abs(end_dif):
                if beginning_dif > 0:
                    frame_pointer.add_feedback("The beginning of your tone is too high. This tone is similar to the Asking tone as it should start high and drop, but there should be a break at the bottom of the tone before rising again")
                else:
                    frame_pointer.add_feedback("The beginning of your tone is too low. This tone is similar to the Asking tone as it should start high and drop, but there should be a break at the bottom of the tone before rising again")
            # If the end of the tone needs correction
            else:
                if end_dif > 0:
                    frame_pointer.add_feedback("The end of your tone is too high. Try to make the change from high to low less dramatic")
                else:
                    frame_pointer.add_feedback("The end of your tone is too low. The tone should start high and drop and there should be a break at the bottom of the tone before rising again")

        if tone == "4" or tone == "Heavy":
            # If the beginning of the tone needs correction
            if abs(beginning_dif) > abs(end_dif):
                if beginning_dif > 0:
                    frame_pointer.add_feedback("The beginning of your tone is too high. This tone should sound stern or angry and drop quickly")
                else:
                    frame_pointer.add_feedback("The beginning of your tone is too low. This tone should sound stern or angry and drop quickly")
            # If the end of the tone needs correction:
            else:
                if end_dif > 0:
                    frame_pointer.add_feedback("The end of your tone is too high. Try to make the change from high to low more dramatic. This tone should sound stern or angry and drop quickly")
                else:
                    frame_pointer.add_feedback("The end of your tone is too low. Try to make the change from high to low less dramatic")

        if tone == "Deep":
            # If the beginning of the tone needs correction
            if abs(beginning_dif) > abs(end_dif):
                if beginning_dif > 0:
                    frame_pointer.add_feedback("The beginning of your tone is too high. This tone should start high and end low, but the change in pitch is more gradual than the Heavy tone")
                else:
                    frame_pointer.add_feedback("The beginning of your tone is too low. This tone should start high and end low, but the change in pitch is more gradual than the Heavy tone")
            # If the end of the tone needs correction:
            else:
                if end_dif > 0:
                    frame_pointer.add_feedback("The end of your tone is too high. Try to make the change from high to low more dramatic. This tone should start high and end low, but the change in pitch is more gradual than the Heavy tone")
                else:
                    frame_pointer.add_feedback("The end of your tone is too low. Try to make the change from high to low less dramatic. This tone should start high and end low, but the change in pitch is more gradual than the Heavy tone")
    else:
        frame_pointer.add_feedback("Good pronunciation!")
    return pronunciation_score


# this function records user input
def record_user(countdown_canvas, countdown_label, sound, frame_pointer):
    fs = 44100
    seconds = 1.1
    recording = sd.rec(int(seconds * fs), samplerate=fs, channels=2)
    sd.wait()   # blocks until 3 seconds
    write('user.wav', fs, recording)
    file = AudioSegment.from_wav('user.wav')
    file.export('user.mp3', format='mp3')
    countdown_canvas.itemconfig(countdown_label, text="")
    return plot_contours(sound, frame_pointer)


# Compute the total difference between contour points between start_index and num_indexes
def computeDifference(start_index, num_indexes, user_frequencies, ref_frequencies):
    i = start_index
    dif = 0
    # find difference in pitch contour points
    while num_indexes > start_index:
        dif = dif + (user_frequencies[i] - ref_frequencies[i])
        i = i + 1
        num_indexes = num_indexes - 1
    return dif

