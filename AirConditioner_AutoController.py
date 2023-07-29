import numpy as np
from tkinter import *
import threading
import time
import csv


# TODO: research for corelation between temperature of outside and inside 
class Temperature(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.temperature = 20
        self.temperature_change_value = 0.5
        self.delay_time = 3
        self.flag = False

    def run(self):
        while True:
            self.change_temperature(self.flag)
            time.sleep(self.delay_time)

    def change_temperature(self, flag):
        self.flag = flag
        if self.flag:
            self.temperature = self.temperature - self.temperature_change_value
            return

        self.temperature = self.temperature + self.temperature_change_value

class AutoControl(threading.Thread):
    def __init__(self, app, temper, auto_on_point, auto_off_point):
        super().__init__(daemon=True)
        self.app = app
        self.temper = temper
        self.delay_time = 0.5
        self.auto_function = self.auto_off_function
        self.auto_on_point = auto_on_point
        self.auto_off_point = auto_off_point
        self.flag = False

    def run(self):
        while True:
            self.change_auto_function(self.flag)

    def change_auto_function(self, flag):
        self.flag = flag
        if self.flag:
            self.auto_on_function()
            return

        self.auto_off_function()

    def auto_off_function(self):
        time.sleep(self.delay_time)

    def auto_on_function(self):
        if self.temper.temperature < self.auto_off_point:
            self.app.activation_btn_update('ON', 'green')
            self.temper.change_temperature(False)
            return

        if self.temper.temperature > self.auto_on_point:
            self.app.activation_btn_update('OFF', 'red')
            self.temper.change_temperature(True)


class Application:
    def __init__(self, temper, DB):
        self.app_func = AppFunction(self, temper, DB)

        self.window = Tk()
        self.window.title("Air Conditioner Controller")
        self.window.geometry("200x120")
        self.window.resizable(True, True)

        self.temperature_lbl = Label(self.window, text='Current Temperature : ' + str(temper.temperature) + 'ºC')
        self.temperature_lbl.pack()
        self.air_conditioner_on_point_lbl = Label(self.window, text='Auto ON Point : ' + str(self.app_func.air_conditioner_on_point()) + 'ºC')
        self.air_conditioner_on_point_lbl.pack()
        self.air_conditioner_off_point_lbl = Label(self.window, text='Auto OFF Point : ' + str(self.app_func.air_conditioner_off_point()) + 'ºC')
        self.air_conditioner_off_point_lbl.pack()
        self.activation_btn = Button(self.window, text='ON', width='5', bg='green', fg='white', command=self.app_func.activation_function)
        self.activation_btn.pack()
        self.auto_activation_btn = Button(self.window, text='AUTO ON', width='9', command=self.app_func.auto_activation_function)
        self.auto_activation_btn.pack()

        self.app_func.ui_update()

        self.window.mainloop()


    def activation_btn_update(self, text, bg):
        self.activation_btn['text'] = text
        self.activation_btn['bg'] = bg


    def auto_activation_btn_update(self, text):
        self.auto_activation_btn['text'] = text


    def on_off_point_lbl_update(self, on_point, off_point):
        self.air_conditioner_on_point_lbl['text'] = 'ON Point : ' + str(on_point) + 'ºC'
        self.air_conditioner_off_point_lbl['text'] = 'OFF Point : ' + str(off_point) + 'ºC'


    def temperature_lbl_update(self, temperature):
        self.temperature_lbl['text'] = 'Current Temperature : ' + str(temperature) + 'ºC'


class AppFunction:
    def __init__(self, app, temper, DB):
        self.app = app
        self.temper = temper
        self.DB = DB

        self.init_air_conditioner_on_point = 30
        self.init_air_conditioner_off_point = 20
        self.auto_on_point = self.init_air_conditioner_on_point
        self.auto_off_point = self.init_air_conditioner_off_point
        self.auto_control = AutoControl(self.app, self.temper, self.auto_on_point, self.auto_off_point)
        self.auto_control.start()

        self.num_of_data_for_avg = 6
        self.temperature_update_delay = 1000
        self.on_off_point_update_delay = 10000
        self.show_decimal_point = 1


    def activation_function(self):
        if self.app.activation_btn['text'] == 'ON':
            self.app.activation_btn_update('OFF', 'red')
            self.temper.change_temperature(True)
            self.DB.insert_data(self.DB.on_point_lst, self.temper.temperature)
            return

        self.app.activation_btn_update('ON', 'green')
        self.temper.change_temperature(False)
        self.DB.insert_data(self.DB.off_point_lst, self.temper.temperature)


    def auto_activation_function(self):
        if self.app.auto_activation_btn['text'] == 'AUTO ON':
            self.app.auto_activation_btn_update('AUTO OFF')
            self.auto_control.change_auto_function(True)
            return

        self.app.auto_activation_btn_update('AUTO ON')
        self.app.activation_btn_update('ON', 'green')
        self.auto_control.change_auto_function(False)


    # 수정
    def air_conditioner_on_point(self):
        if len(self.DB.on_point_lst) < self.num_of_data_for_avg:
            self.auto_on_point = self.init_air_conditioner_on_point
            return

        self.auto_on_point = round(np.average(self.DB.on_point_lst[-self.num_of_data_for_avg:]), self.show_decimal_point)


    # 수정
    def air_conditioner_off_point(self):
        if len(self.DB.off_point_lst) < self.num_of_data_for_avg:
            self.auto_off_point = self.init_air_conditioner_off_point
            return

        self.auto_off_point = round(np.average(self.DB.off_point_lst[-self.num_of_data_for_avg:]), self.show_decimal_point)


    def ui_on_off_point_update(self):
        self.air_conditioner_on_point()
        self.air_conditioner_off_point()
        self.app.on_off_point_lbl_update(self.auto_on_point, self.auto_off_point)
        self.app.air_conditioner_on_point_lbl.after(self.on_off_point_update_delay, self.ui_on_off_point_update)


    def ui_temperature_update(self):
        temperature = round(self.temper.temperature, self.show_decimal_point)
        self.app.temperature_lbl_update(temperature)
        self.app.temperature_lbl.after(self.temperature_update_delay, self.ui_temperature_update)


    def ui_update(self):
        self.ui_temperature_update()
        self.ui_on_off_point_update()


class Database:
    def __init__(self):
        self.on_point_lst = []
        self.off_point_lst = []
        self.data_save_limit = 60
        self.delete_data_index = 0


    def csv_to_data(self, read_path, file_name):
        try:
            f = open(read_path + file_name + '.csv', 'r', encoding='utf-8')
            rd = csv.reader(f)
            for on, off in rd:
                self.on_point_lst.append(float(on))
                self.off_point_lst.append(float(off))
            f.close()
        except FileNotFoundError as e:
            print(e)


    def insert_data(self, lst, value):
        if len(lst) == self.data_save_limit:
            lst.pop(self.delete_data_index)
            lst.append(value)
            return

        lst.append(value)


    def data_to_csv(self, save_path, file_name):
        f = open(save_path + file_name + '.csv', 'w', encoding='utf-8', newline='')
        wd = csv.writer(f)
        for d in zip(self.on_point_lst, self.off_point_lst):
            wd.writerow(d)
        f.close()


if __name__ == '__main__':

    read_data_path = './'
    read_data_name = 'temperature_data'
    save_data_path = './'
    save_data_name = 'temperature_data'

    temper = Temperature()
    temper.start()

    DB = Database()
    DB.csv_to_data(read_data_path, read_data_name)
    application = Application(temper, DB)
    DB.data_to_csv(save_data_path, save_data_name)
