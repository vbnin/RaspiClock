#!/usr/bin/env python
# coding: utf-8

"""
Développé par IP Echanges - VBNIN et CKAR

"""

version_text = 'Version 0.2 - 28/08/2018'
print('This is RaspiClock - {}').format(version_text)

# Import libraries
import Tkinter as tk
import time
import os
import sys
import subprocess
import re
import socket

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

        self.net_color='gray'
        self.net_text='Statut Réseau : Inconnu'
        self.net_status = tk.Label(button_frame, text=self.net_text, font='Helvetica 12 bold', fg=self.net_color, bg='black')
        self.net_status.pack(padx=(30,0), side='right')

        self.ntp_color='gray'
        self.ntp_text='Sync NTP : Inconnu'
        self.ntp_status = tk.Label(button_frame, text=self.ntp_text, font='Helvetica 12 bold', fg=self.ntp_color, bg='black')
        self.ntp_status.pack(padx=(130,0), side='right')

        # Creating the clock layout
        self.clock_enable = False
        self.clock = tk.Label(master=root, font = '"LCD AT&T Phone Time/Date" 165', fg=self.Color, bg='black')
        self.clock.pack(padx=(8,8), pady=(120))

        # Starting the ntp and network check loop
        self.Loop() 

        # Starting the tick loop
        self.Tick()

           

    def config(self):
        # This function allows you to configure the clock
        # Opening popup window
        self.config_window = tk.Toplevel()
        self.config_window.resizable(False, False)
        self.config_window.attributes("-topmost", True)
        self.config_window.overrideredirect(1)
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
        tk.Label(about_frame, text=version_text).pack()

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
        if self.clock_enable == True:
            if self.SecondsChoice == 'Non':
                self.CurrentTime = time.strftime('%H:%M')
                if self.clock['font'] != '"LCD AT&T Phone Time/Date" 260':
                    self.clock.configure(font= '"LCD AT&T Phone Time/Date" 260')
                    self.clock.pack(padx=(10,10), pady=(70))
            else:
                self.CurrentTime = time.strftime('%H:%M:%S')
                if self.clock['font'] != '"LCD AT&T Phone Time/Date" 165':
                    self.clock.configure(font= '"LCD AT&T Phone Time/Date" 165')
                    self.clock.pack(padx=(8,8), pady=(120))
            self.clock['text'] = self.CurrentTime
        else:
            self.clock.configure(font= 'System 60 bold')
            self.clock.pack(padx=(8,8), pady=(80))
            self.clock['text'] = '''Vérification
réseau et NTP
en cours...'''
        self.clock.after(100, self.Tick)

    def net_check(self):
        # This function checks for network status
        try:
            # connect to the host -- tells us if the host is actually reachable
            socket.create_connection(("www.google.com", 80), timeout=20)
            self.net_status.configure(text='Statut Réseau : OK', fg='green')
            self.net = 'OK'
            return True
        except:
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
                    if n_t == 'yes' and n_s == 'yes' and self.net == 'OK':
                        self.ntp_status.configure(text='Sync NTP : OK', fg='green')
                        return True
                    else:
                        self.ntp_status.configure(text='Sync NTP : Free Run', fg='red')
                        return False
                else:
                    print("Unable to check NTP status.")
                    return False
            else:
                print("Unable to check NTP because not on linux system.")
                self.ntp_status.configure(text='Sync NTP : Non vérifiable', fg='gray')
                return False
        except Exception as e:
            print("Error during NTP check action : {}").format(e)
            return False

    def Loop(self):
        # This function calls other function on a given interval
        if self.net_check() is True and self.NTP_check() is True:
            self.clock_enable = True
        self.net_status.after(10000, self.Loop)

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
