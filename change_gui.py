import numpy as np
import argparse
import imutils
import time
import cv2
import face_recognition
import pickle
from tkinter import *
from tkinter import ttk
import PIL
from PIL import ImageTk, Image

root = Tk()
root.resizable(False, False)
root.title('Change faces')

container = Frame(root)

#creation canvas
main_canvas = Canvas(container, width = 350, height=255, bg = 'grey')
change_canvas = Canvas(container, width = 200, height=255, bg = 'white')

#scrollbar
scroll = ttk.Scrollbar(container, command = main_canvas.yview)

scroll_main_canvas_frame = Frame(main_canvas)
main_canvas.create_window((0, 0), window=scroll_main_canvas_frame, anchor="nw")

change_canvas_frame = Frame(change_canvas)
change_canvas.create_window((0, 0), window=change_canvas_frame, anchor="nw")

#mouse wheel but it's ne robit on scroll_main_canvas_frame
def rollWheel(event):
    print(event.__class__)
    direction = 0

    if event.delta == -120:
        direction = 1
    if event.delta == 120:
        direction = -1

    event.widget.yview_scroll(direction, UNITS)

main_canvas.bind(
    '<MouseWheel>', 
    lambda event: 
        rollWheel(event)
)

scroll_main_canvas_frame.bind(
    "<Configure>",
    lambda event: 
        main_canvas.configure(
            scrollregion=main_canvas.bbox("all"),
            yscrollcommand = scroll.set
        )
)

#why it's global
global known_face_encodings, known_face_metadata

try:
    with open("known_faces.dat", "rb") as face_data_file:
        known_face_encodings, known_face_metadata = pickle.load(face_data_file)
        face_data_file.close()
        print("Known faces loaded from disk.")
except FileNotFoundError:
    print("Not found a dataset")
    pass


#CONTENT

metadata_id = 0

for metadata in known_face_metadata:
    
    #преобразование массива NumPy в PIL image
    get_image = ImageTk.PhotoImage(PIL.Image.fromarray(metadata['face_image']))
    image_label = Label(scroll_main_canvas_frame, image=get_image, text='    ID: ' + str(metadata_id) + ' NAME: ' + metadata['face_name'], font=("Arial", 10), compound=LEFT)
    image_label.image = get_image
    #ipadx - in pading x
    image_label.pack(ipadx=10, ipady=10)
    metadata_id += 1

#===WINDOW OF CHANGE CANVAS===#

update_lable = Label(change_canvas_frame, text='Update image', font='bold')
update_lable.pack(padx=50)

img = Image.open("eldorado_smal.jpg")
get_image_ch = ImageTk.PhotoImage(img)
image_label_img = Label(change_canvas_frame, image = get_image_ch, text='ID: X' + ' NAME: XXX', font=("Arial", 10), compound=TOP)
#ipadx - in pading x
image_label_img.pack(ipadx=10, ipady=10)

#CANGE ID

change_id_lable = Label(change_canvas_frame, text='ID')
change_id_lable.pack(ipady=3)

change_canvas_id_entry = ttk.Entry(change_canvas_frame, width=20)
change_canvas_id_entry.pack(padx=10)
change_canvas_id_entry.focus_set()

#CANGE NAME

change_name_lable = Label(change_canvas_frame, text='На что менять будем')
change_name_lable.pack(ipady=3)

change_canvas_name_entry = ttk.Entry(change_canvas_frame, width=20)
change_canvas_name_entry.pack(padx=10)

change_btn = Button(change_canvas_frame,
                    text="Change",
                    width=15,
            )

change_btn.pack(pady=10)


def change(event):

    print(change_canvas_id_entry.get(), change_canvas_name_entry.get(), PIL.Image.fromarray(known_face_metadata[int(change_canvas_id_entry.get())]['face_image']))

    known_face_metadata[int(change_canvas_id_entry.get())]["face_name"] = change_canvas_name_entry.get()

    #!!!!!!!!!какой мусор собирает переменная с PhotoImage и почему я не могу кинуть изображение через локальную
    image_label_img.image = ImageTk.PhotoImage(
                        PIL.Image.fromarray(known_face_metadata[int(change_canvas_id_entry.get())]['face_image'])
                    )

    image_label_img.configure(
            image = image_label_img.image,
            text = 'ID: ' + change_canvas_id_entry.get() + ' NAME: ' + change_canvas_name_entry.get()
        )

    with open("known_faces.dat", "wb") as face_data_file:
        face_data = [known_face_encodings, known_face_metadata]
        pickle.dump(face_data, face_data_file)
        face_data_file.close()
        print("Change saved")

change_btn.bind("<Button-1>", change)

#РАЗМЕТКА

container.pack()

#fill - заполнение
scroll.pack(side = LEFT, fill = Y)
main_canvas.pack(side=LEFT, fill=Y)
change_canvas.pack(side=LEFT, fill=Y)


root.mainloop()