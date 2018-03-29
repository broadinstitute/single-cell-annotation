import numpy as np
import pandas as pd
import time
import os

from bokeh.plotting import figure
from bokeh.layouts import row
from bokeh.plotting import curdoc
from bokeh.layouts import layout
from bokeh.models.widgets import Button, RadioButtonGroup, Div
from bokeh.models import ColumnDataSource
from bokeh.palettes import Spectral8

import traceback

INPUT_FILE = "data/inputs/{}.npy"
OUTPUT_FILE = "data/outputs/{}.csv"
BACKUP_EVERY = 2
label_options = [
    "Smooth Disc", 
    "Crenated Disc", 
    "Crenated Discoid", 
    "Crenated Spheroid", 
    "Crenated Sphere", 
    "Smooth sphere", 
    "Side view", 
    "Undecidable",
    "SKIP"
]

## EVENT HANDLER

class Handler():

    def __init__(self, controls, user):
        # Main variables
        self.controls = controls
        self.cell = 0
        self.label = None
        self.user = user

        # Load user input data
        self.data = np.load(INPUT_FILE.format(user))

        # Prepare output data
        self.out_file = OUTPUT_FILE.format(user)
        if os.path.isfile(self.out_file):
            self.annotations = pd.read_csv(self.out_file)
            self.cell = self.annotations.shape[0]
            if self.data.shape[0] == self.annotations.shape[0]:
                self.cell -= 1
            self.controls["back_btn"].disabled = False
        else:
            self.annotations = pd.DataFrame(columns={"CellID", "ClassID"})

        # Update layout controls
        self.display_cell()
        self.update_counts()


    def display_cell(self):
        new_data = dict()
        new_data["image"] =  [self.data[self.cell,:,:,0]]
        self.controls["cell_screen"].data_source.data = new_data
        self.controls["title"].text = "<center><h2>Cell #" + str(self.cell + 1 ) + "</h2></center>"


    def update_counts(self):
        counts = self.annotations.groupby("ClassID").count()
        for i in range(len(label_options)-1):
            try: self.controls["counts"].patch({"counts": [(int(i), counts.loc[i,"CellID"])]})
            except: self.controls["counts"].patch({"counts": [(int(i), 0)]})


    def forward(self):
        self.controls["back_btn"].disabled = True
        self.controls["next_btn"].disabled = True
        # Save label
        if self.label is not None:
            self.annotations.loc[self.cell] = {"CellID":self.cell, "ClassID":self.label}
            if self.cell % BACKUP_EVERY:
                self.annotations.to_csv(self.out_file, index=False)

            if self.cell < self.data.shape[0]-1:
                # Display next image
                self.cell += 1
                self.display_cell()
            else:
                self.cell = self.data.shape[0]
                self.controls["cell_screen"].data_source.data = {"image":[]}
                self.annotations.to_csv(self.out_file, index=False)

            self.controls["label_buttons"].active = None
            self.label = None
        self.controls["back_btn"].disabled = False
        self.update_counts()


    def back(self):
        if self.cell > 0:
            # Display previous cell
            if self.cell <= self.data.shape[0]:
                self.cell -= 1
            self.display_cell()
            idx = self.annotations.index[-1]
            self.annotations = self.annotations.drop(idx)
        else:
            self.controls["back_btn"].disabled = True
        self.update_counts()


    def set_label(self, new):
        self.label = new
        if self.label is not None:
            if self.cell < self.data.shape[0]:
                self.controls["next_btn"].disabled = False


## VISUALIZATION AREAS

# Image viewer
image = figure(x_range=(0, 10), y_range=(0, 10),plot_width=450, plot_height=450)
content = image.image(image=[], x=0, y=0, dw=10, dh=10, palette="Greys256")

# Counts viewer
source = ColumnDataSource(data=dict(label_options=label_options[0:-1], counts=[0 for i in range(8)], color=Spectral8))

bars = figure(x_range=label_options, plot_height=350, title="Cell Counts",
           toolbar_location=None, tools="")

bars.vbar(x='label_options', top='counts', width=0.9, color='color', source=source)

bars.xaxis.major_label_orientation = 3.14159/6.

## CONTROLS

title = Div(width=500)
button_group = RadioButtonGroup(labels=label_options, width=500, active=None)
button_group.on_change("active", lambda attr, old, new: data_handler.set_label(new))
back_btn = Button(label="Previous", disabled=True)
next_btn = Button(label="Save and Next", disabled=True)

controls = {
    "title": title,
    "label_buttons": button_group,
    "cell_screen": content,
    "back_btn": back_btn,
    "next_btn": next_btn,
    "counts": source
}


## HANDLER, LAYOUT AND WEB APP
try:
    # Read request arguments
    args = curdoc().session_context.request.arguments
    user = args["user"][0].decode("utf-8")

    # Create interaction handler
    data_handler = Handler(controls, user)
    back_btn.on_click(data_handler.back)
    next_btn.on_click(data_handler.forward)

    # Organize layout
    full_layout = layout([
        [title], 
        [image],
        [button_group],
        [row([back_btn, next_btn])],
        [bars]
    ])

    # Launch web application
    curdoc().add_root(row( full_layout ))
except:
    print("Invalid request (incorrect or no username provided).")

