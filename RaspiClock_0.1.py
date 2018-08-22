#!/usr/bin/env python
# coding: utf-8

"""
Développé par IP Echanges - VBNIN et CKAR
Version : 0.1 
Release date : 21/08/2018
"""

# Import libraries
import Tkinter as tk
import time
import os
import sys
import subprocess
import re

# Define config file location and name
ConfigFile = os.path.join(sys.path[0], 'RaspiClock_config.ini')

# Main class
class Clock(object):
    def __init__(self, root):
        # Try to read the config file or use default settings
        try:
            with open(ConfigFile, 'r') as f:
                lines = f.read().splitlines()
                self.Color = lines[0]
                self.SecondsChoice = lines[1]
        except Exception as e:
            print("Cannot read config file : ", e)
            self.Color = 'red'
            self.SecondsChoice = 'Oui'

        # Frame containing main buttons
        button_frame = tk.Frame(master=root, bg='black')
        button_frame.pack(padx=10, pady=10, anchor='n')
        tk.Button(button_frame,
         text='Configurer',
          font='Helvetica 12 bold',
           height=1, width=11,
            command=self.config,
             bg='black',
              fg='gray',
               bd=1,
                highlightbackground='black',
                 activebackground='gray').pack(side='left')
        self.ntp_color='gray'
        self.ntp_text='Statut NTP : non vérifié'
        self.ntp_status = tk.Label(button_frame, text=self.ntp_text, font='Helvetica 12 bold', fg=self.ntp_color, bg='black')
        self.ntp_status.pack(padx=(80,0), side='right')

        # Creating the clock layout
        self.clock = tk.Label(master=root, font = '"LCD AT&T Phone Time/Date" 140', fg=self.Color, bg='black')
        self.clock.pack(padx=(20,20), pady=(120,100))

        # Starting the tick loop
        self.Tick()    

    def config(self):
        # This function allows you to configure the clock
        # Opening popup window
        self.config_window = tk.Toplevel()
        self.config_window.resizable(False, False)
        self.config_window.attributes("-topmost", True)
        self.config_window.title("Configuration de RaspiClock")

        x = (self.config_window.winfo_screenwidth() - self.config_window.winfo_reqwidth()) / 2
        y = (self.config_window.winfo_screenheight() - self.config_window.winfo_reqheight()) / 2
        self.config_window.geometry("+{}+{}".format(x, y))

        config_frame = tk.Frame(self.config_window)
        config_frame.pack(padx=20, pady=30, anchor='w')

        tk.Label(config_frame, text='Couleur de texte : ').grid(row=0, column=0, sticky='w')
        colors = ['red', 'green', 'blue', 'white']
        self.ColorChoice = tk.StringVar()
        self.ColorChoice.set(self.Color)
        self.Color = tk.OptionMenu(config_frame, self.ColorChoice, *colors)
        self.Color.configure(width=10)
        self.Color.grid(row=0, column=1, sticky='ew')

        tk.Label(config_frame, text='Affichage des secondes :').grid(row=1, column=0, sticky='w', pady=(15,0))
        choix = ['Oui', 'Non']
        self.SecondsToggle = tk.StringVar()
        self.SecondsToggle.set(self.SecondsChoice)
        self.toggle = tk.OptionMenu(config_frame, self.SecondsToggle, *choix)
        self.toggle.grid(row=1, column=1, sticky='ew', pady=(15,0))

        self.quit = tk.Button(config_frame, text='Quitter le programme', height=1, width=15, command=root.destroy)
        self.quit.grid(row=2, column=0, sticky='w', padx=10, pady=(20,0))

        self.about_button = tk.Button(config_frame, text='A propos', height=1, width=8, command=self.about)
        self.about_button.grid(row=2, column=1, sticky='w', padx=10, pady=(20,0))

        button_frame = tk.Frame(self.config_window)
        button_frame.pack()
        tk.Button(button_frame, text='Valider', height=1, width=6, default='active', command=self.click_valider).pack(side='right')
        tk.Button(button_frame, text='Retour', height=1, width=6, command=self.click_retour).pack(side='right', padx=10)

    def about(self):
        # This function opens an about window with informations
        # Closing Config Window
        self.click_retour()

        # Opening popup window
        self.about_window = tk.Toplevel()
        self.about_window.resizable(False, False)
        self.about_window.attributes("-topmost", True)
        self.about_window.title("A propos de RaspiClock")

        x = (self.about_window.winfo_screenwidth() - self.about_window.winfo_reqwidth()) / 2
        y = (self.about_window.winfo_screenheight() - self.about_window.winfo_reqheight()) / 2
        self.about_window.geometry("+{}+{}".format(x, y))

        about_frame = tk.Frame(self.about_window)
        about_frame.pack(padx=30, pady=20, anchor='center')

        tk.Label(about_frame, text='Horloge synchronisée par NTP').pack()
        tk.Label(about_frame, text='Language : Python 2.7').pack()
        tk.Label(about_frame, text='Une application IP-Echanges pour France Télévisions').pack()
        tk.Label(about_frame, text='Version 0.1 - 22/08/2018').pack()

        tk.Button(about_frame, text='Fermer', height=1, width=6, default='active', command=self.click_fermer).pack(side='right')

    def click_fermer(self):
        # This function closes the about window
        self.about_window.destroy()

    def click_valider(self):
        # This function sets the defined settings anc closes the config window
        if self.ColorChoice.get() != '':
            self.Color = self.ColorChoice.get()
            self.clock.configure(fg=self.Color)
        if self.SecondsToggle.get() != '':
            self.SecondsChoice = self.SecondsToggle.get()
        with open(ConfigFile, 'w') as f:
            f.writelines(self.Color + '\n')
            f.writelines(self.SecondsChoice)
        self.config_window.destroy()

    def click_retour(self):
        # This function closes the config window
        with open(ConfigFile, 'r') as f:
                lines = f.read().splitlines()
                self.Color = lines[0]
        self.ColorChoice = self.Color
        self.config_window.destroy()

    def Tick(self):
        # This function checks for time and launch ntp function every 300ms
        if self.SecondsChoice == 'Non':
            self.CurrentTime = time.strftime('%H:%M')
        else:
            self.CurrentTime = time.strftime('%H:%M:%S')
        self.clock['text'] = self.CurrentTime
        self.NTP_check()
        self.clock.after(300, self.Tick)
    
    def NTP_check(self):
        # This function checks for NTP sync (works only with a raspberry for now)
        try:
            if sys.platform.lower() == 'linux' or sys.platform.lower() == 'linux2':
                cmd = ["timedatectl", "status"]
                action = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                (out, err) = action.communicate()
                if action.returncode == 0:
                    for line in out.splitlines():
                        if re.search(r'Network time on: (.*)', line, re.I):
                            self.ntp_time = re.search(r'Network time on: (.*)', line, re.I)
                        elif re.search(r'NTP synchronized: (.*)', line, re.I):
                            self.ntp_sync = re.search(r'NTP synchronized: (.*)', line, re.I)
                    if self.ntp_time.group(1).lower() == 'yes' and self.ntp_sync.group(1).lower() == 'yes':
                        self.ntp_status.configure(text='Statut NTP : OK', fg='green')
                    else:
                        self.ntp_status.configure(text='Statut NTP : Free Run', fg='red')
                else:
                    # print("Unable to check NTP status.")
                    return
            else:
                # print("Unable to check NTP because not on linux system.")
                return
        except Exception as e:
            # print("Error during NTP check action : {}").format(e)
            return

# Start the main app
if __name__ == '__main__':
    root = tk.Tk()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    app = Clock(root)
    root.title('FranceTV PyClock v0.1')
    root.resizable(False, False)
    root.geometry('{}x{}'.format(screen_width, screen_height))
    root.wm_attributes('-fullscreen', 1)
    root.attributes("-topmost", True)
    root.focus_force()
    root.configure(bg='black', cursor='none')
    root.mainloop()
