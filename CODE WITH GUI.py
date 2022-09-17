import csv
import pyodbc
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.dates as mdates
import dateutil
import os
from scipy import ndimage
import boto3
import botocore
import holidays
import datetime
import tkinter as tk
from tkinter import *
import customtkinter
root= tk.Tk()
DATA_FILES_DIR = r"C:\Users\Admin\Desktop\fin\csv"
s3 = boto3.client('s3')
customtkinter.set_appearance_mode("Dark")
customtkinter.set_default_color_theme("blue")

def event_detector(df):

    times = np.arange(0, len(df[0]), 1)
    df = np.array(df)[0]
    filtered = ndimage.median_filter(df, 3)
    plt.plot(times, filtered)
    t_positive = 0.3
    t_negative = -0.3
    delta_p = [np.round(filtered[i + 1] - filtered[i], 2) for i in range(0, len(filtered) - 1)]
    event_up = [i for i in range(0, len(delta_p)) if (delta_p[i] > t_positive)]
    event_down = [i for i in range(0, len(delta_p)) if (delta_p[i] < t_negative)]

    ev = np.zeros(len(df))
    event_2 = np.zeros(len(df))
    ev = [e + 1 if i in event_up else e for i, e in enumerate(ev)]
    ev = [e - 1 if i in event_down else e for i, e in enumerate(ev)]
    # plt.plot(times, ev)

    i = 0
    window_len = 7
    while i < len(ev):
        if ev[i] == 0:
            event_2[i] = 0
        if ev[i] == 1:
            idx = [i for i, e in enumerate(ev[i:i + window_len]) if e == 1]
            for j in range(0, window_len):
                if j == idx[-1]:
                    event_2[i + j] = 1
                else:
                    event_2[i + j] = 0
            i = i + (window_len - 1)
        if ev[i] == -1:
            idx = [i for i, e in enumerate(ev[i:i + window_len]) if e == -1]
            for j in range(0, window_len):
                if j == idx[0]:
                    event_2[i + j] = -1
                else:
                    event_2[i + j] = 0
            i = i + (window_len - 1)
        i = i + 1
    plt.plot(times, event_2)
    plt.show()
    return event_2


def gen_CSV(path, file_name):
    # connect to db
    con = pyodbc.connect(r'Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=' + os.path.join(path, file_name) + ';')
    cur = con.cursor()
    col_desc = list(cur.columns())
    table_names = []
    for b in col_desc:
        if b[2] not in table_names:
            table_names.append(b[2])
    c = [e for e in table_names if e[0:3] == 'RT ']
    # c= table_names[-1]
    # c = table_names[3:]
    rows = []
    for i, c in enumerate([e for e in table_names if e[0:3] == 'RT ']):
        sql = 'SELECT * FROM [{}]'.format(c)
        cur.execute(sql)
        if i == 0:
            rows.append([x[3] for x in col_desc if x[2] == c])  # headers
        for row in cur.fetchall():
            if row[0] != 0.0:
                rows.append(row)
        del rows[1]  # remove first row
    path_for_csv = os.path.join(os.getcwd())
    with open(os.path.join(DATA_FILES_DIR, '{}.csv'.format(file_name.split(".")[0])), 'w',
              newline='') as fou:  # file.split(".")[0]
        csv_writer = csv.writer(fou)  # default field-delimiter is ","
        csv_writer.writerows([e[1:] for e in rows])
    cur.close()
    con.close()



def get_data(path, file_name):  # also adds the Energy colums.
    gen_CSV(path, file_name)
    # with open(os.path.join(path,'{}.csv'.format(file_name.split(".")[0])), newline='') as csvfile:
    #   data = list(csv.reader(csvfile))
    # data = np.array(data)
    # add the energy columns
    # E=np.transpose(calc_energy())
    # E_titels= np.array(['E1','E2','E3'])
    # E_tot= np.vstack( (E_titels , E ))
    # data= np.hstack((data,E_tot))
    #return data

def calc_phase_energy(df):
    # phase = phase - 1  # match an index
    # col_list_power = ["kW L1", "kW L2", "kW L3"]  # ["kW L2"]#["kW L1", "kW L2", "kW L3"]
    # df = pd.read_csv("data.csv", usecols=col_list_power) #TODO: change to relevane file name instead of data.csv
    Energ = []
    sum = 0
    for x in range(df.shape[0]):
        sum = sum + df['kw'][x] #the second col is of power
        Energ.append(sum)
    return (Energ)

def calc_energy(E,df):
    E.append(calc_phase_energy(df))
    return E


def plot_param_2(CSV_FLAG, columns, Ts,num):
    phase_counter =0
    for i in range(1, len(columns)):
        if Ts >= 30:
            if Ts % 60 == 0:
                s_Ts = '{}[min]'.format(int(Ts / 60))
            else:
                s_Ts = '{}[min]'.format(Ts / 60)
        else:
            s_Ts = '{}[sec]'.format(int(Ts))
        files = os.listdir(DATA_FILES_DIR)
        plt.figure()  # for each parameter there is a seperate file
        for file_n, file in enumerate(files):
            if file.split('.')[1] != 'csv':  # if the files were originally mdb, go only over their csv copies
                continue
            with open(os.path.join(DATA_FILES_DIR, '{}.csv'.format(file.split(".")[0])), newline='') as csvfile:
                data = list(csv.reader(csvfile))
                df = pd.DataFrame(data)
                df = df.rename(columns=df.iloc[0, :])
                time = df.iloc[1:, 0]
                # time = [time[i][10:18] for i in range(len(time))]  # keep the '%H:%M:%S' only.
                time = [dateutil.parser.parse(s) for s in time]
                df = df.iloc[1:, 1:].apply(pd.to_numeric)  # the name row appears twice, so remove it
            dfs = df[columns[i]]  # the i'th parameter
            if columns[i] == 'P1' or columns[i] == 'P2' or columns[i] == 'P3':
                if columns[i] == 'P1':
                    phase_counter = 1
                if columns[i] == 'P2':
                    phase_counter=2
                if columns[i] =='P3':
                    phase_counter = 3
                e_vals=[]
                dfs = abs(dfs)
                energy_df=pd.DataFrame(columns=['timestamp', 'kw'])
                energy_df['timestamp']=time
                energy_df['kw']=dfs.values
                e_vals=calc_energy(e_vals, energy_df)
                label=Label(root,bg='light blue',font=('century',12),text='Total Energy in kWh for phase #'+str(phase_counter)+' on date '+str(time[0].day) +"-"+str(time[0].month)+ "-" + str(time[0].year)+" is: "+str(np.transpose(e_vals)[-1, :] / 3600))
                label.pack()
                #print(phase_counter, end =" on date ")
                #print(str(time[0].day) +"-"+str(time[0].month)+ "-" + str(time[0].year), end=" is: ")
                #print(np.transpose(e_vals)[-1, :] / 3600)
            ax = plt.subplot(len(files), 1, file_n + 1)
            first =file[0:4]+'/' +file[4:6] + '/' + file[6:8] +' ' + file[8:10] + ':'+ file[10:12]
            second =file[13:17]+'/' +file[17:19] + '/' + file[19:21] +' ' + file[21:23] + ':'+ file[23:25]
            if(file !='merged.csv'):
                ax.title.set_text(columns[i] + ' of ' + first +' to '+ second)
            else:
                ax.title.set_text(columns[i] + ' of ' + file)
            plt.step(time, dfs)  # 'step' is the zero order interpolation plot function.
            # plt.plot(time, dfs, color=colors[i])
            plt.xlabel("t [h:m]")
            # plt.suptitle("{}".format(suptitle)) #("{}{}".format(suptitle,i))
            plt.xticks(time[0:len(time):int(num)*1440])  # how many x values to display 8->800
            myFmt = mdates.DateFormatter('%H:%M')
            plt.gca().xaxis.set_major_formatter(myFmt)
        # plt.tight_layout()[
    plt.show()



#def gen_plots(file,num, params, phase, CSV_FLAG, columns):
    # update_data(data, Ts)
    #Ts = 1
    #for x in params:
        # plt.figure()
        #if CSV_FLAG == 1:
            #plot_param_2(CSV_FLAG, columns, Ts,num)
        #else:
            #plot_param(file, x, phase, CSV_FLAG, Ts)


def calc_energy_diffs(data):
    E = data[1:, [-3, -2, -1]]
    E = E.astype(float)
    E = np.transpose(E)
    deltas = np.diff(E)
    E[:, 1:E.shape[1]] = deltas
    E[:, 0] = 0
    return (E)


def update_data(data, Ts):  # adds the Energy diff between the sampels & dilutes the sampales
    if (Ts != 1):
        data = dilute_sampales(data, Ts)
    data = np.array(data)
    # calc_energy_deltas
    dE = np.transpose(calc_energy_diffs(data))
    dE_title = np.array(['dE1', 'dE2', 'dE3'])
    dE_tot = np.vstack((dE_title, dE))
    new_data = np.hstack((data, dE_tot))
    with open('data.csv', 'w') as f:
        write = csv.writer(f)
        write.writerows(new_data)


def dilute_sampales(data, new_gap):
    Ts_orig = 1  # the original gap between samples [sec]
    k = int(new_gap / Ts_orig)
    n = int((len(data) - 1) / k)
    new_data = [data[k * i] for i in range(1, n + 1)]
    new_data.insert(0, data[0])
    return new_data

def diff_day():
    def days():
        def holid_fst():
            def holiday_checker(day_in,holiday_in):
                valid=0
                for page in content :
                    for obj in page['Contents']:
                        if valid < 11 :
                            cp_list.append(obj['Key'])
                            valid = valid + 1
                counter =0
                for date in cp_list :
                    year = date[0:4]
                    month= date[4:6]
                    day = date[6:8]
                    new_format=  str(month + '-' + day + '-' +year)
                    new_format_t = pd.Timestamp(new_format)
                    if holiday_in == "holiday":
                        if (new_format_t.day_name() == day_in) and (new_format_t in holidays.Israel()) and (counter < num):
                            s_days.append(date)
                            counter =counter+1
                    else:
                        if (new_format_t.day_name() == day_in) and (new_format_t not in holidays.Israel()) and (counter < num) :
                            s_days.append(date)
                            counter=counter+1
                for target in cp_list:
                    to_download=target
                    to_download_path = str(DATA_FILES_DIR + '\\' + to_download)
                    try:
                        s3.download_file("satec-flamiingo", to_download, to_download_path)
                    except botocore.exceptions.ClientError as e:
                        if e.response['Error']['Code'] == "404":
                            label = Label(root, text="The requested file does not exist.")
                            label.pack()
                            exit(1)
                join = os.path.join(DATA_FILES_DIR, "*.csv")
                button = Button(root, text="Give Me Graphs!", command=lambda: main(num))
                button.pack(padx=5,pady=5)
                return num


            d=str(dif_day.get())
            label=Label(root,text="Please choose an option :")
            label.pack()
            hol=Button(root, text= "Holiday",command=lambda: holiday_checker(d,"holiday"))
            hol.pack(padx=4,pady=4)
            wor=Button(root,text="Workday",command=lambda: holiday_checker(d,"workday"))
            wor.pack(padx=4,pady=4)


        num=int(num_val.get())
        for i in range(num):
            label=Label(root,text ="Enter day number " +str(i+1) +" in the week :")
            label.pack()
            dif_day=Entry(root,width=35)
            dif_day.pack(padx=5,pady=5)
            button1 = Button(root, text="Next", command=holid_fst)
            button1.pack()


    s3 = boto3.client('s3')
    s_days = []
    cp_list = []
    paginator = s3.get_paginator('list_objects_v2')
    content = paginator.paginate(Bucket='satec-flamiingo')
    label = Label(root, text="Please enter number of days :", font=('century', 12))
    label.pack()
    num_val = Entry(root, width=35)
    num_val.pack(padx=5, pady=5)
    button1 = Button(root, text="Next", command=days)
    button1.pack()


def same_day():
    def sec_func():
        def checker():
            x=0
            for page in content:
                valid_names =0
                for obj in page['Contents']:
                    if valid_names < 11:
                        if obj['Key'][0:8] == obj['Key'][13:21]:
                            s_days.append(obj['Key'])
                        valid_names = valid_names + 1
                num=int(num_val.get())
                w_day=str(day_ent.get())
            for val in s_days:
                prep_date = str(val[4:6] + '-' + val[6:8] + '-' + val[0:4])
                prep_date_format = pd.Timestamp(prep_date)
                if (prep_date_format.day_name() == w_day) and (x < num):
                    cp_list.append(val)
                    x = x + 1
                    val = 0
            if len(cp_list) == 0:
                label=Label(root,text="No occurences were found, exiting...")
                label.pack()
                exit(1)
            elif len(cp_list) < num:
                label=Label(root,text="Not enough occurences were found, plotting" +str(x) + "occurences\n")
            for obj in cp_list:
                to_download = obj
                to_download_path = str(DATA_FILES_DIR + '\\' + to_download)
                try:
                    s3.download_file("satec-flamiingo", to_download, to_download_path)
                except botocore.exceptions.ClientError as e:
                    if e.response['Error']['Code'] == "404":
                        label = Label(root, text="The requested file does not exist.")
                        label.pack()
                        exit(1)
            join = os.path.join(DATA_FILES_DIR, "*.csv")
            button = Button(root, text="Give Me Graphs!", command=lambda: main(num))
            button.pack(padx=5,pady=5)
            return num

        label = Label(root, text="Please enter number of occurences :",font=('century',12))
        label.pack()
        num_val = Entry(root, width=35)
        num_val.pack(padx=5, pady=5)
        button1 = Button(root, text="Next", command=checker)
        button1.pack()

    s3 = boto3.client('s3')
    s_days = []
    cp_list=[]
    x=0
    valid_names = 0
    paginator =s3.get_paginator('list_objects_v2')
    content =paginator.paginate(Bucket='satec-flamiingo')
    label = Label(root, text="Please enter day in the week :",font=('century',12))
    label.pack()
    day_ent = Entry(root, width=35)
    day_ent.pack(padx=5, pady=5)
    button1 = Button(root, text="Next", command=sec_func)
    button1.pack()

def main(num):
    dont_change = DATA_FILES_DIR  # on your computer open an empty folder called downloads and put here the path
    DATA_FILES_DIR2 = r"C:\Users\Public\Project\merged"
    # if (input("do you want to compare days?: yes/no:")=="yes"):
    # DATA_FILES_DIR = dont_change
    # else:
    # merge_csv_files(DATA_FILES_DIR, DATA_FILES_DIR2)
    # DATA_FILES_DIR = DATA_FILES_DIR2
    files = os.listdir(DATA_FILES_DIR)
    if len(files) == 0:
        quit(0)
    file = files[0]
    if not file.endswith("csv"):
        for file in files:
            get_data(DATA_FILES_DIR, file)
        columns = list(['timestamp', 'P1', 'P2', 'P3'])
    else:
        columns = list(['timestamp', 'P1', 'P2', 'P3'])
    # gen_plots(file,num, ['mock_param'], -1, CSV_FLAG=1, columns=columns)  # built for csv from dekel
    Ts = 1
    CSV_FLAG = 1
    for x in ['mock_param']:
        plot_param_2(CSV_FLAG, columns, Ts, num)
    os.chdir(dont_change)
    all_files = os.listdir()
    for f in all_files:
        os.remove(f)


def Dates():
    def Dates_after_inputs():
        def myscanner():
            def start_drawing():
                for obj in filenames:
                    to_download = obj
                    to_download_path = str(DATA_FILES_DIR + '\\' + to_download)
                    try:
                        s3.download_file("satec-flamiingo", to_download, to_download_path)
                    except botocore.exceptions.ClientError as e:
                        if e.response['Error']['Code'] == "404":
                            label = Label(root,text="The requested file does not exist.")
                            label.pack()
                            print("The requested file does not exist.")
                            exit(1)
                join = os.path.join(DATA_FILES_DIR, "*.csv")
                button = Button(root, text="Give Me Graphs", command=main(num1))
                button.pack(padx=5,pady=5)
                return num1
            filenames = []
            s3 = boto3.client('s3')
            file_name = 'yeardate0000_yeardate2359.csv'
            scanner = str(c.get())
            button1.destroy()
            to_timestamp = pd.Timestamp(scanner)
            to_format = datetime.datetime.strptime(scanner, '%m-%d-%Y').strftime('%Y%m%d')
            if to_timestamp in holidays.Israel() or to_timestamp.day_name() == "Friday" or to_timestamp.day_name() == "Saturday":
                label = Label(root,text="The day you requested is a" + to_timestamp.day_name() + ", this day is a holiday")
                label.pack()
            else:
                label = Label(root, text="The day you requested is a " + to_timestamp.day_name() + ", this day is a workday")
                label.pack()
            file_name = file_name.replace(file_name[0:8], to_format)
            file_name = file_name.replace(file_name[13:21], to_format)
            filenames.append(file_name)
            button = Button(root, text="Give Me Graphs", command=start_drawing)
            button.pack(padx=5,pady=5)
        label = Label(root,text="Now enter the dates in order in %m-%d-%y format")
        label.pack()
        num1 = int(a.get())
        if num1 == 0:
            quit(0)
        button.destroy()
        for i in range(num1):
            label = Label(root,text="Date of day "+str(i+1)+": ")
            label.pack()
            c = Entry(root, width=35)
            c.pack(padx=5, pady=5)
            button1 = Button(root, text="Next", command=myscanner)
            button1.pack()
    Label(root, text='Please enter number of days:').pack()
    a = Entry(root, width=35)
    a.pack(padx = 5, pady = 5)
    button = Button(root,text="Next",command =Dates_after_inputs)
    button.pack()


##########################  code starts here ####################################################################
root.geometry("600x600")
root.title("Project Gui")
root['bg']="light blue"
label = tk.Label(root,text = "Choose an option:",bg="light blue", font=('century', 14))
label.pack(padx = 20, pady = 20)
Dates_button = tk.Button(root, text="Dates", font=('century',13),bg="light blue",fg="black", command=Dates)
Dates_button.pack(padx = 5, pady = 5)
diff_Weekday_button = tk.Button(root, text="different days in the week",bg="light blue",fg="black", font=('century',13),command=diff_day)
diff_Weekday_button.pack(padx = 5, pady = 5)
same_weekday_button = tk.Button(root, text="same day in the week",bg="light blue",fg="black", font=('century',13), command=same_day)
same_weekday_button.pack(padx = 5, pady = 5)
root.mainloop()
