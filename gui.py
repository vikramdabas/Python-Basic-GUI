import tkinter as tk
import os
import time
import sys
import glob
import serial
import serial.tools.list_ports as sport
import re
from tkinter import ttk
import io
from tkinter import messagebox
import csv
import paho.mqtt.client as mqtt
import json
import threading

Default_Font = "Segoe 10 bold"
Default_Font1 = "Segoe 10"
Default_LFont = "Segoe 12 bold"
Default_LFont1 = "Segoe 12"


def escape_ansi(line):
    ansi_escape = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]')
    # ansi_escape = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]')
    return ansi_escape.sub('', line)


class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)
        self.initialize_user_interface()
        self.create_widgets()
        self.bms_widgets()
        self.ser = serial.Serial()

    def serial_ports(self):
        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            # this excludes your current terminal "/dev/tty"
            ports = glob.glob('/dev/tty[A-Za-z]*')
        elif sys.platform.startswith('darwin'):
            ports = glob.glob('/dev/tty.*')
        else:
            raise EnvironmentError('Unsupported platform')
        result = []
        for port in ports:
            try:
                s = serial.Serial(port)
                s.close()
                result.append(port)
            except OSError:
                pass
        return result

    def initialize_user_interface(self):
        self.master.title("Test Application")

    def portrefresh(self):
        if self.ser.is_open:
            print(self.ser.name)
            pass
            self.connectb['state'] = 'disabled'
            self.connectb['bg'] = '#f0f0f0'
            self.tkvar.set(self.ser.name)
        else:
            self.tkvar.set('')
            self.popupMenu['menu'].delete(0, 'end')
            serialports = self.serial_ports()
            if len(serialports) == 0:
                serialports = {'COM0'}
                for choice in serialports:
                    self.popupMenu['menu'].add_command(label=choice, command=tk._setit(self.tkvar, choice))
            else:
                for choice in serialports:
                    self.popupMenu['menu'].add_command(label=choice, command=tk._setit(self.tkvar, choice))
            self.connectb['state'] = 'disabled'
            self.connectb['bg'] = '#f0f0f0'

    def create_widgets(self):
        # ********************** ROW 0 *********************************#
        self.quit = tk.Button(self.master, text="Quit App", fg="White", bg="#c0392b", font=Default_Font, command=self.master.destroy)
        self.quit.grid(sticky='n e w', row=0, column=0, padx=10, pady=2, ipadx=10, ipady=2)
        self.portrefreshb = tk.Button(self.master, text="Port Refresh", bg="#2980b9", fg="White", font=Default_Font, command=self.portrefresh)
        self.portrefreshb.grid(sticky='n e w', row=0, column=1, padx=10, pady=2, ipadx=10, ipady=2)
        self.label1 = tk.Label(self.master, text="", state='disabled')
        self.label1.grid(sticky='n e w', row=0, column=2, columnspan=1, padx=10, pady=2, ipadx=10, ipady=2)
        self.realtime = tk.Button(self.master, text="", state='disabled', font=Default_Font)
        self.realtime.grid(sticky='n e w', row=0, column=3, padx=10, pady=2, ipadx=10, ipady=2)
        self.update_clock()

    def update_clock(self):
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        self.realtime.configure(text="Current Time: " + now)
        self.after(1000, self.update_clock)

    def connect(self):
        try:
            self.ser = serial.Serial(self.tkvar.get(), 115200, timeout=0, parity=serial.PARITY_NONE, rtscts=0)
        except:
            print("Connection Error")
            return
        finally:
            pass
        print("********************* " + self.ser.name + " Connected" + " *********************")
        # self.ser.write(b'hello')
        # print("message send")
        self.connectb['state'] = 'disabled'
        self.connectb['bg'] = '#f0f0f0'
        self.msgsendb['state'] = 'normal'
        self.msgsendb['bg'] = '#e74c3c'
        self.disconnectb['state'] = 'normal'
        self.disconnectb['bg'] = '#c0392b'
        self.comportincrement = 0
        self.msgreadprint()

    def disconnect(self):
        if self.ser.is_open:
            print("******************** " + self.ser.name + " Connected" + " ********************")
            print("******************* " + self.ser.name + " Disconnected" + " *******************")
            self.ser.close()
        else:
            print("******************* " + "Serial Port Disconnected" + " *******************")
            self.ser.close()
        # self.connectb['state'] = 'normal'
        # self.connectb['bg'] = '#2980b9'
        self.msgsendb['state'] = 'disabled'
        self.msgsendb['bg'] = '#f0f0f0'
        self.disconnectb['state'] = 'disabled'
        self.disconnectb['bg'] = '#f0f0f0'

    def comport_select(self, *args):
        if len(self.tkvar.get()) > 0:
            print("********************* " + self.tkvar.get() + " Selected" + " **********************")
        if self.ser.is_open:
            pass
        else:
            self.connectb['state'] = 'normal'
            self.connectb['bg'] = '#2980b9'

    def bms_widgets(self):
        # ********************** bmsmainframe *********************************#
        # ********************** ROW 1 *********************************#
        self.bmsmainframe = tk.Frame(self.master, borderwidth=2, relief=tk.GROOVE)
        self.bmsmainframe.grid(row=1, column=0, columnspan=4, sticky="n e w s", padx=5, pady=5)
        tk.Label(self.bmsmainframe, text='BMS Box', pady=0).place(relx=.01, rely=0.1, anchor='sw')

        self.tkvar = tk.StringVar(self.bmsmainframe)
        serialports = self.serial_ports()
        if len(serialports) == 0:
            self.tkvar.set('COM0')
            serialports = {'COM0'}
            self.popupMenu = tk.OptionMenu(self.bmsmainframe, self.tkvar, serialports)
        else:
            self.popupMenu = tk.OptionMenu(self.bmsmainframe, self.tkvar, *serialports)
        self.popupMenu.config(bg="#1abc9c")
        self.comlabel = tk.Label(self.bmsmainframe, text="BMS Port", font=Default_Font)
        self.comlabel.grid(sticky='n e w s', row=1, column=0, padx=10, pady=8, ipadx=10, ipady=3)
        self.popupMenu.grid(sticky='n e w s', row=1, column=1, padx=10, pady=4, ipadx=10, ipady=3)

        self.connectb = tk.Button(self.bmsmainframe, text="Connect COM", fg="White", command=self.connect, state='disabled', font=Default_Font)
        self.connectb.grid(row=1, column=2, padx=10, pady=4, ipadx=10, ipady=3, sticky='n e w s')

        self.disconnectb = tk.Button(self.bmsmainframe, text="Disconnect", fg="White", command=self.disconnect, state='disabled', font=Default_Font)
        self.disconnectb.grid(row=1, column=3, padx=10, pady=4, ipadx=10, ipady=3, sticky='n e w s')

        self.msgsendata = tk.Entry(self.bmsmainframe, font=Default_Font1)
        self.msgsendata.grid(row=2, column=0, padx=10, pady=4, ipadx=10, ipady=3, sticky='n e w s')

        self.msgsendb = tk.Button(self.bmsmainframe, text="Send Message", fg="White", command=self.msgsend, state='disabled', font=Default_Font)
        self.msgsendb.grid(row=2, column=1, padx=10, pady=4, ipadx=10, ipady=3, sticky='n e w s')

        self.serialout = tk.Label(self.bmsmainframe, text=" ", font=Default_Font)
        self.serialout.grid(sticky='n e w s', row=3, column=0, columnspan=3, padx=10, pady=8, ipadx=10, ipady=3)

        self.tkvar.trace('w', self.comport_select)

    def msgsend(self):
        if self.ser.is_open:
            writeval = str(self.msgsendata.get()) + '\r'
            self.ser.write(writeval.encode())
            #self.ser.write(b'hello')
            print("********************** " + "Message Send From " + self.ser.name + " **********************")
            print(writeval)
        else:
            self.disconnect()

    def msgreadprint(self):
        if self.ser.is_open:
            pass
        else:
            return
        out = str(self.ser.readline().decode())
        nout = (escape_ansi(line=out)[1:][:-1].split(" "))
        while "" in nout:
            nout.remove("")
        # print(nout)
        self.serialout["text"] = out
        self.after(100, self.msgreadprint)


if __name__ == '__main__':
    root = tk.Tk()
    app = Application(master=root)
    app.master.minsize(625, 200)
    app.master.maxsize(625, 200)
    root.mainloop()
