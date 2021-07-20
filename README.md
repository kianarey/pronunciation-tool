# Pronunciation Tool for Learning Tonal Languages
#### Senior Design Project, Fall 2020

###### Members: Kiana Vang, Brendan Bagley, Kirsten Olson, Derrick Loke, Jake Wang
###### Predecessors: Abdirahman Abdirahman, Ali Adam, Hassan Ali, Elijah Nguyen, Chee Tey (Spring 2020)
###### Mentor: Professor Gerald Sobelman, University of Minnesota - Twin Cites, MN


## Project Description
The ability to speak more than one language possesses many benefits. It especially opens a gateway for one to engage in different perspectives, exchange cultural awareness, and increase their understanding of the world. However, not all languages are created equal. Some languages have multiple writing systems, while others only have one. Some languages are only written, while others are a mix of written and oral. 

The languages that we are particularly interested in for this project are tonal languages, such as Chinese Mandarin, Vietnamese, Hmong and Thai. While a given word can be spelled the same, the tone tied to that specific word can give it an entirely new and different meaning. This presents many challenges to the person learning and teaching said language. This project expands on our predecessor’s work and aims to complete a pronunciation tool for learning tonal languages. Different techniques were used to achieve the final development of the tool, such as digital signal processing, statistical analysis, machine learning, and software engineering.

__Note:__ *The project materials have been revised on May 21, 2021 by Kiana Vang. Currently, I am working on improving the overall graphical user interface, expanding the language datasets to better train the models used for predicting a user's tone, and ensuring scalability and functionality for future languages. In doing so, I have scaled back the number of languages we originally had and focusing one language, Chinese Mandarin.*

#### About the Code
`seniorDesign.py` is the main program that runs the GUI via Tkinter. It allows a user to select a language, tone and word. It plays back the reference audio for the word the user is attempting to pronounce and also allows the user to record.

`mand_deeplearning.py` predicts the user's tone.

`spectrogram.py` displays the pitch contour of the user's pronunciation and the reference pronunciation. 

Note: All files are provided except `Mandarin_model.h5` file which is **required** to successully run the GUI. See [here](https://github.com/kianavang/kianavang) for how to contact me for this file.

#### How to Run Code
Make sure all files are within the same directory. Build the program using shell command:

    $ python seniordesign.py
