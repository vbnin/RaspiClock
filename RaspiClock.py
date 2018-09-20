#!/usr/bin/env python
# coding: utf-8

"""
Programmed by IP Echanges - VBNIN et CKAR
This is a simple NTP customizable clock displaying full screen for TV offices
Warning : The clock layout is made for 7" Raspberry Screens. It won't display correctly elsewhere
"""

version_text = 'Version 0.3 - 20/09/2018'

# Import libraries
import Tkinter as tk
import time
import os
import sys
import subprocess
import re
import socket

# Logs files are stored there
logs_file = os.path.join(sys.path[0],'RaspiClock_logs.log')
i = 1
try:
    while os.path.getsize(logs_file) > 5000000:
        logs_file = os.path.join(sys.path[0],'RaspiClock_logs_{}.log'.format(str(i)))
        i += 1
except:
    pass

def Log(log):
    # This function records a message in computer syslogs
    logline = time.strftime("%d/%m/%Y - %H:%M:%S") + ' : ' + log + '\n'
    print(logline)
    try:
        with open(logs_file, 'a') as l:
            try:
                l.writelines(logline.encode("utf-8"))
            except:
                l.writelines(logline)
    except Exception as e:
        print('Error !! Could not store logs in file.. : {}').format(e)

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
            Log('Config file present in : {}'.format(ConfigFile))
        except Exception as e:
            Log("Cannot read config file : {}".format(e))
            Log("Using default values for color and seconds")
            self.Color = 'red'
            self.SecondsChoice = 'Oui'

        # Frame containing main buttons
        button_frame = tk.Frame(master=root, bg='black')
        button_frame.pack(padx=10, pady=10, fill='both', anchor='n')
        self.conf = tk.Button(button_frame,
            text='Config (F1)',
            font='Helvetica 10 bold',
            height=1, width=8,
            command=lambda: self.config(),
            bg='black',
            fg='#202020',
            bd=1,
            highlightbackground='black',
            highlightcolor='#202020',
            activebackground='#202020')
        self.conf.pack(side='left')

        self.net_color='gray'
        self.net_text='Statut Réseau : Inconnu'
        self.net_status = tk.Label(button_frame, text=self.net_text, font='Helvetica 12 bold', fg=self.net_color, bg='black')
        self.net_status.pack(padx=(160,0), side='left')

        self.ntp_color='gray'
        self.ntp_text='Sync NTP : Inconnu'
        self.ntp_status = tk.Label(button_frame, text=self.ntp_text, font='Helvetica 12 bold', fg=self.ntp_color, bg='black')
        self.ntp_status.pack(padx=(30,0), side='left')

        # Creating the clock layout
        self.clock_enable = False
        self.clock = tk.Label(master=root, font = '"LCD AT&T Phone Time/Date" 165', fg=self.Color, bg='black')
        self.clock.pack(padx=10, pady=120)

        # Starting the ntp and network check loop
        self.Loop() 

        # Starting the tick loop
        self.Tick()

           
    def config(self, event=None):
        # This function allows you to configure the clock
        # Opening popup window
        Log("User opened config panel")
        root.configure(cursor='arrow')
        self.config_window = tk.Toplevel()
        self.config_window.resizable(False, False)
        self.config_window.attributes("-topmost", True)
        self.config_window.overrideredirect(1)
        self.config_window.focus_set()
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

        self.quit = tk.Button(config_frame, text='Quitter le programme', height=1, width=15, command=self.Quit)
        self.quit.grid(row=2, column=0, sticky='w', padx=10, pady=(20,0))

        self.about_button = tk.Button(config_frame, text='A propos', height=1, width=8, command=self.about)
        self.about_button.grid(row=2, column=1, sticky='w', padx=10, pady=(20,0))

        button_frame = tk.Frame(self.config_window)
        button_frame.pack()
        tk.Button(button_frame, text='Valider', height=1, width=6, default='active', command=self.click_valider).pack(side='right')
        tk.Button(button_frame, text='Retour', height=1, width=6, command=self.click_retour).pack(side='right', padx=10)

    def about(self):
        # This function opens a window with 'about' informations
        # Closing Config Window
        self.click_retour()

        # Opening popup window
        Log("User opened 'about' window")
        self.about_window = tk.Toplevel()
        self.about_window.resizable(False, False)
        self.about_window.attributes("-topmost", True)
        self.config_window.overrideredirect(1)
        self.about_window.title("A propos de RaspiClock")

        x = (self.about_window.winfo_screenwidth() - self.about_window.winfo_reqwidth()) / 2
        y = (self.about_window.winfo_screenheight() - self.about_window.winfo_reqheight()) / 2
        self.about_window.geometry("+{}+{}".format(x, y))

        about_frame = tk.Frame(self.about_window)
        about_frame.pack(padx=30, pady=20, anchor='center')

        tk.Label(about_frame, text='Horloge synchronisée par NTP').pack()
        tk.Label(about_frame, text='Language : Python 2.7').pack()
        tk.Label(about_frame, text='Une application IP-Echanges pour France Télévisions').pack()
        tk.Label(about_frame, text=version_text).pack()

        tk.Button(about_frame, text='Fermer', height=1, width=6, default='active', command=self.click_fermer).pack(side='right')

    def click_fermer(self):
        # This function closes the about window
        Log("User closed 'about' window")
        root.configure(cursor='none')
        self.about_window.destroy()

    def click_valider(self):
        # This function sets the defined settings anc closes the config window
        Log("User closed config panel with 'Valider' button")
        if self.ColorChoice.get() != '':
            self.Color = self.ColorChoice.get()
            self.clock.configure(fg=self.Color)
        if self.SecondsToggle.get() != '':
            self.SecondsChoice = self.SecondsToggle.get()
        try:
            with open(ConfigFile, 'w') as f:
                f.writelines(self.Color + '\n')
                f.writelines(self.SecondsChoice)
        except Exception as e:
            Log("Unable to create Config file : {}".format(e))
        root.configure(cursor='none')
        self.config_window.destroy()

    def click_retour(self):
        # This function closes the config window
        Log("User closed config panel with 'Retour' button")
        try:
            with open(ConfigFile, 'r') as f:
                    lines = f.read().splitlines()
                    self.Color = lines[0]
        except Exception as e:
            Log("Unable to read Config file while closing config panel : {}".format(e))
            self.Color = 'red'
        self.ColorChoice = self.Color
        root.configure(cursor='none')
        self.config_window.destroy()

    def Quit(self):
        Log("Application exited by user")
        root.destroy()

    def Tick(self):
        # This function checks for time and launch ntp function every 300ms
        if self.clock_enable == True:
            if self.SecondsChoice == 'Non':
                self.CurrentTime = time.strftime('%H:%M')
                if self.clock['font'] != '"LCD AT&T Phone Time/Date" 260':
                    self.clock.configure(font= '"LCD AT&T Phone Time/Date" 260')
                    self.clock.pack(padx=10, pady=70, side='left')
            else:
                self.CurrentTime = time.strftime('%H:%M:%S')
                if self.clock['font'] != '"LCD AT&T Phone Time/Date" 162':
                    self.clock.configure(font= '"LCD AT&T Phone Time/Date" 162')
                    self.clock.pack(padx=(10, 0), pady=120, side='left')
            self.clock['text'] = self.CurrentTime
        else:
            self.clock.configure(font= 'System 60 bold')
            self.clock.pack(padx=10, pady=80)
            self.clock['text'] = '''Vérification
réseau et NTP
en cours...'''
        self.clock.after(100, self.Tick)

    def net_check(self):
        # This function checks for network status
        try:
            # connect to the host -- tells us if the host is actually reachable
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(20)
            try:
                sock.connect(("itransfert.francetv.fr", 80))
            except Exception as e:
                Log("Unable to check Network with itransfert.francetv.fr, trying with Google...  - {}".format(e))
                sock.connect(("google.fr", 80))
            self.net_status.configure(text='Statut Réseau : OK', fg='green')
            return True
        except Exception as e:
            Log("Warning - NO network connectivity : {}".format(e))
            self.net_status.configure(text='Statut Réseau : Hors ligne', fg='red')
            return False
        
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
                            n_t = self.ntp_time.group(1).lower()
                        elif re.search(r'NTP synchronized: (.*)', line, re.I):
                            self.ntp_sync = re.search(r'NTP synchronized: (.*)', line, re.I)
                            n_s = self.ntp_sync.group(1).lower()
                    if n_t == 'yes' and n_s == 'yes':
                        self.ntp_status.configure(text='Sync NTP : OK', fg='green')
                        return True
                    else:
                        Log("Warning - NO NTP sync")
                        Log("Command ouput : {}".format(out))
                        self.ntp_status.configure(text='Sync NTP : Free Run', fg='red')
                        return False
                else:
                    Log("Warning - Unable to check NTP status : {}".format(err))
                    return False
            else:
                Log("Warning - Unable to check NTP because not on linux system.")
                self.ntp_status.configure(text='Sync NTP : Non vérifiable', fg='gray')
                return True
        except Exception as e:
            Log("Error while checking for NTP sync : {}".format(e))
            return False

    def Loop(self):
        # This function calls other function on a given interval
        if self.net_check() is True and self.NTP_check() is True:
            self.clock_enable = True
        elif self.net_check() is False and self.NTP_check() is False:
            Log("Critical - NO NTP sync and NO network connectivity !")
        self.net_status.after(10000, self.Loop)

# Start the main app
if __name__ == '__main__':
    Log('This is RaspiClock - {}'.format(version_text))
    Log('Starting app now')
    Log('Logs are stored in : {}'.format(logs_file))
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
    root.bind('<F1>', lambda e: app.config()) 
    root.mainloop()
