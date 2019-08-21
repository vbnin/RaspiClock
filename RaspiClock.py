#!/usr/bin/env python
# coding: utf-8

"""
Programmed by IP Echanges - VBNIN et CKAR
This is a simple NTP customizable clock displaying full screen for TV offices
Warning : The clock layout is made for 7" Raspberry Screens. It won't display correctly elsewhere
"""

version_text = 'Version 0.7 - 24/10/2018'

# Import libraries
import time
import os
import sys
import subprocess
import re
import socket
import logging
import multiprocessing
import filelock
from logging.handlers import RotatingFileHandler

# Changing library names if running different version of Python
if sys.version_info < (3,0):
    # Python v2.x
    import Tkinter as tk
else:
    # Python v3.x
    import tkinter as tk

# Logs files are stored there
log_file = os.path.join(sys.path[0],'RaspiClock_logs.log')

# Activating logging handler
handler = RotatingFileHandler(log_file, maxBytes=10000000, backupCount=5, encoding="utf-8")
handler.setFormatter(logging.Formatter('%(asctime)s : %(message)s'))
logging.basicConfig(level=logging.INFO, format='%(asctime)s : %(message)s')
logger = logging.getLogger(__name__)
logger.addHandler(handler)

# Define config file location and name
ConfigFile = os.path.join(sys.path[0], 'RaspiClock_config.ini')

# System NTP server file location
NTPFile = '/etc/systemd/timesyncd.conf'

# Temporary file storing NTP infos
NTPTempFile = '/home/pi/RaspiClock_NTP/TEMP_timesyncd.conf'

# Witness file path, this file prevents multiple instances of the app
witness_file = os.path.join(sys.path[0], 'running.lock')

# Main class
class Clock(object):
    def __init__(self, root):
        try:
            self.clock_type = '%H:%M:%S'
            self.CurrentTime = time.strftime(self.clock_type)

            with open(NTPFile, 'r') as f:
                self.timesyncd_lines = f.read().splitlines()
                for l in self.timesyncd_lines:
                    if re.match(r'NTP=', l):
                        ls = l.split('=')
                        self.NTPServer = ls[1]
                        logger.info('Currently used NTP server : {}'.format(self.NTPServer))
                        break
            if not self.NTPServer:
                raise Exception('NO current NTP server found')
                
        except Exception as e:
            logger.info("Unable to verify the current NTP server : {}".format(e))
            self.NTPServer = ''


        # Try to read the config file or use default settings
        try:
            with open(ConfigFile, 'r') as f:
                lines = f.read().splitlines()
                self.Color = lines[0]
                self.SecondsChoice = lines[1]
                if self.NTPServer != lines[2]:
                    logger.info('Warning - Conflict between stored NTP server and config file !')
                self.net_address = lines[3]
            logger.info('Config file present in : {}'.format(ConfigFile))
        except Exception as e:
            logger.info("Cannot read config file : {}".format(e))
            logger.info("Creating new config file with default values")
            try:
                self.Color = 'red'
                self.SecondsChoice = 'Oui'
                self.net_address = "itransfert.francetv.fr"
                with open(ConfigFile, 'w') as f:
                    f.writelines(self.Color + '\n')
                    f.writelines(self.SecondsChoice + '\n')
                    f.writelines(self.NTPServer + '\n')
                    f.writelines(self.net_address)
            except Exception as e:
                logger.info("Unable to create Config file : {}".format(e))
            

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

        self.net_status = tk.Label(button_frame, text='Statut Réseau : Inconnu', font='Helvetica 11 bold', fg='gray', bg='black')
        self.net_status.pack(padx=(30,0), side='left')

        self.ntp_status = tk.Label(button_frame, text='Sync NTP : Inconnu', font='Helvetica 11 bold', fg='gray', bg='black')
        self.ntp_status.pack(padx=(30,0), side='left')

        # Creating the clock layout
        self.clock_enable = False
        self.clock = tk.Label(master=root, text='''Vérification\nréseau et NTP\nen cours...''', font='System 60 bold', fg=self.Color, bg='black')
        self.clock.pack(padx=10, pady=80)
  
        # Launching a subprocess checking every 20 secondes for network and ntp status
        self.queue = multiprocessing.Queue()
        p = multiprocessing.Process(target=self.net_check, args=(self.queue,))
        p.start()

        # Starting the ntp and network feedback loop
        self.net_stat_feeback_loop() 

        # Starting the tick loop
        self.Tick()

           
    def config(self, event=None):
        # This function allows you to configure the clock
        # Opening popup window
        logger.info("User opened config panel")
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

        tk.Label(config_frame, text='Serveur NTP :').grid(row=2, column=0, sticky='w', pady=(15,0))
        self.NTPField = tk.StringVar()
        self.NTPField.set(self.NTPServer)
        self.NTPChoice = tk.Entry(config_frame, textvariable=self.NTPField)
        self.NTPChoice.grid(row=2, column=1, sticky='ew', pady=(15,0))

        tk.Label(config_frame, text='Adresse de test réseau :').grid(row=3, column=0, sticky='w', pady=(15,0))
        self.net_field = tk.StringVar()
        self.net_field.set(self.net_address)
        self.net_choice = tk.Entry(config_frame, textvariable=self.net_field)
        self.net_choice.grid(row=3, column=1, sticky='ew', pady=(15,0))

        self.quit = tk.Button(config_frame, text='Quitter le programme', height=1, width=15, command=self.Quit)
        self.quit.grid(row=4, column=0, sticky='w', padx=10, pady=(20,0))

        self.about_button = tk.Button(config_frame, text='A propos', height=1, width=8, command=self.about)
        self.about_button.grid(row=4, column=1, sticky='w', padx=10, pady=(20,0))

        button_frame = tk.Frame(self.config_window)
        button_frame.pack()
        tk.Button(button_frame, text='Valider', height=1, width=6, default='active', command=self.click_valider).pack(side='right')
        tk.Button(button_frame, text='Retour', height=1, width=6, command=self.click_retour).pack(side='right', padx=10)

    def click_valider(self):
        # This function sets the defined settings anc closes the config window
        logger.info("User closed config panel with 'Valider' button")
        if self.ColorChoice.get() != '':
            self.Color = self.ColorChoice.get()
            self.clock.configure(fg=self.Color)
        if self.SecondsToggle.get() != '':
            self.SecondsChoice = self.SecondsToggle.get()
        try:
            with open(ConfigFile, 'w') as f:
                f.writelines(self.Color + '\n')
                f.writelines(self.SecondsChoice + '\n')
                f.writelines(self.NTPChoice.get() + '\n')
                f.writelines(self.net_choice.get())
        except Exception as e:
            logger.info("Unable to create Config file : {}".format(e))
        if self.NTPChoice.get() != self.NTPServer or self.net_address != self.net_choice.get():
            self.tempNTP = self.NTPChoice.get()
            self.RebootWindow()
        else:
            root.configure(cursor='none')
            self.config_window.destroy()
        return

    def click_retour(self):
        # This function closes the config window
        logger.info("User closed config panel")
        try:
            with open(ConfigFile, 'r') as f:
                    lines = f.read().splitlines()
                    self.Color = lines[0]
        except Exception as e:
            logger.info("Unable to read Config file while closing config panel : {}".format(e))
            self.Color = 'red'
        self.ColorChoice = self.Color
        root.configure(cursor='none')
        self.config_window.destroy()
        return

    def Quit(self):
        logger.info("Application exited by user")
        lock.release()
        root.destroy()
        sys.exit(0)
        return

    def about(self):
        # This function opens a window with 'about' informations
        self.click_retour()

        # Opening popup window
        logger.info("User opened 'about' window")
        self.about_window = tk.Toplevel()
        self.about_window.resizable(False, False)
        self.about_window.attributes("-topmost", True)
        root.configure(cursor='arrow')
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

        tk.Button(about_frame, text='Fermer', height=1, width=6, default='active', command=self.click_fermer_about).pack(side='right')

    def click_fermer_about(self):
        # This function closes the about window
        logger.info("User closed 'about' window")
        root.configure(cursor='none')
        self.about_window.destroy()
        return

    def RebootWindow(self):
        # This function opens a window proposing to reboot the computer
        self.click_retour()

        # Opening popup window
        logger.info("User opened 'do you want to reboot' window")
        self.reboot_window = tk.Toplevel()
        self.reboot_window.resizable(False, False)
        self.reboot_window.attributes("-topmost", True)
        root.configure(cursor='arrow')
        self.reboot_window.title("Redémarrage nécessaire")

        x = (self.reboot_window.winfo_screenwidth() - self.reboot_window.winfo_reqwidth()) / 3
        y = (self.reboot_window.winfo_screenheight() - self.reboot_window.winfo_reqheight()) / 3
        self.reboot_window.geometry("+{}+{}".format(x, y))

        reboot_frame = tk.Frame(self.reboot_window)
        reboot_frame.pack(padx=30, pady=20, anchor='center')

        tk.Label(reboot_frame, text="Le changement de NTP nécessite un redémarrage de l'ordinateur.").pack()

        tk.Button(reboot_frame, text='Redémarrer', height=1, width=8, default='active', command=self.ChangeNTP).pack(side='right')
        tk.Button(reboot_frame, text='Annuler', height=1, width=6, default='active', command=self.click_fermer_reboot).pack(side='right')

    def click_fermer_reboot(self):
        # This function closes the about window
        logger.info("User closed 'RebootWindow' window")
        root.configure(cursor='none')
        self.reboot_window.destroy()
        return

    def ChangeNTP(self):
        # This function changes the NTP server if needed
        for n, l in enumerate(self.timesyncd_lines):
            if re.match(r'NTP=', l) or re.match(r'#NTP=', l):
                r = 'NTP=' + self.tempNTP
                self.timesyncd_lines[n] = r
        with open(NTPTempFile, 'w') as f:
            for l in self.timesyncd_lines:
                f.writelines(l + '\n')
        try:
            os.system("sudo cp {} /etc/systemd/timesyncd.conf".format(NTPTempFile))
            logger.info("File copied to /etc/systemd")
            os.system("sudo chown root:root /etc/systemd/timesyncd.conf")
            logger.info("Changed file owner to root:root")
            os.system("rm {}".format(NTPTempFile))
            logger.info("NTP successfully changed to {}".format(self.tempNTP))
            with open(ConfigFile, 'w') as f:
                f.writelines(self.Color + '\n')
                f.writelines(self.SecondsChoice + '\n')
                f.writelines(self.tempNTP)
            os.system('sudo reboot')
            self.reboot_window.destroy()            
        except Exception as e:
            logger.info("Error during NTP change : {}".format(e))
            self.reboot_window.destroy()
        
    def Tick(self):
        # This function checks for time and launch ntp function every 200ms
        if self.clock_enable == True:
            if self.SecondsChoice == 'Non' and self.clock['font'] != '"LCD AT&T Phone Time/Date" 260':
                    self.clock_type = '%H:%M'
                    self.clock.configure(font= '"LCD AT&T Phone Time/Date" 260')
                    self.clock.pack(padx=15, pady=70, side='left')
            elif self.SecondsChoice == 'Oui' and self.clock['font'] != '"LCD AT&T Phone Time/Date" 162':
                    self.clock_type = '%H:%M:%S'
                    self.clock.configure(font= '"LCD AT&T Phone Time/Date" 162')
                    self.clock.pack(padx=(15, 0), pady=120, side='left')
            self.clock.configure(text=time.strftime(self.clock_type))
        self.clock.after(200, self.Tick)

    def net_check(self, q):
        net_stats = {}
        while True:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(20)
                sock.connect((self.net_address, 80))
                net_stats['net_stat_text'] = 'Statut Réseau : OK'
                net_stats['net_stat_fg'] = 'green'
            except Exception as e:
                logger.info("Warning - NO network connectivity : {}".format(e))
                net_stats['net_stat_text'] = 'Statut Réseau : Hors ligne'
                net_stats['net_stat_fg'] = 'red'

            try:
                cmd = "systemctl status systemd-timesyncd.service"
                action = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                (out, err) = action.communicate()
                if action.returncode != 0:
                    raise Exception(err)
                else:
                    for line in out.splitlines():
                        if re.search(r'Status: (.*)', line, re.I):
                            result = re.search(r'Status: (.*)', line, re.I)
                            result = result.group(1).lower()
                            if result == '"idle."':
                                raise Exception(out)
                            else:
                                r = result.split(" ")
                                try:
                                    output = "Sync NTP OK : {} {}".format(r[4], r[5][:-2])
                                except:
                                    output = r.group(1)
                                net_stats['ntp_stat_text'] = output
                                net_stats['ntp_stat_fg'] = 'green'
            except Exception as e:
                logger.info("Warning - NO NTP synchronization : {}".format(e))
                net_stats['ntp_stat_text'] = 'Sync NTP : Free Run'
                net_stats['ntp_stat_fg'] = 'red'

            q.put(net_stats)
            time.sleep(15)

    def net_stat_feeback_loop(self):
        # This function calls other function on a given interval
        if not self.queue.empty():
            self.network_stats = self.queue.get()
            self.ntp_status.configure(text=self.network_stats['ntp_stat_text'], fg=self.network_stats['ntp_stat_fg'])
            self.net_status.configure(text=self.network_stats['net_stat_text'], fg=self.network_stats['net_stat_fg'])
            if self.network_stats['net_stat_fg'] == 'green' and self.network_stats['ntp_stat_fg'] == 'green':
                self.clock_enable = True
        self.net_status.after(15000, self.net_stat_feeback_loop)

# Start the main app
if __name__ == '__main__':
    logger.info('This is RaspiClock - {}'.format(version_text))

    try:
        lock = filelock.FileLock(witness_file)
        lock.acquire(timeout=1)
        logger.info('Creating a witness file in {}'.format(witness_file))
    except:
        logger.info('*** Error *** : Another instance of the script seems to run because "running.lock" has been found')
        logger.info('Exiting app now')
        sys.exit(1)

    logger.info('Starting app now')
    logger.info('Logs are stored in : {}'.format(log_file))
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
