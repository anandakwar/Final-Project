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


# from edge_detection import event_detector

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
    con = pyodbc.connect(
        r'Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=' + os.path.join(path, file_name) + ';')
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

def calc_phase_energy(df):
    # phase = phase - 1  # match an index
    # col_list_power = ["kW L1", "kW L2", "kW L3"]  # ["kW L2"]#["kW L1", "kW L2", "kW L3"]
    # df = pd.read_csv("data.csv", usecols=col_list_power) #TODO: change to relevane file name instead of data.csv
    E = []
    sum = 0
    for x in range(df.shape[0]):
        sum = sum + df['kw'][x] #the second col is of power
        E.append(sum)
    return (E)

def calc_energy(E,df):
    E.append(calc_phase_energy(df))
    return E

def energy_main_func():
    DATA_FILES_DIR = os.path.join(os.getcwd(), '2d_plot_files')
    files = os.listdir(DATA_FILES_DIR)
    for file in files:
        E = []
        for i in range(1, 4, 1):
            phase_number = i
            if phase_number == 1:
                parameters = 'kwL1'
            if phase_number == 2:
                parameters = 'kwL2'
            if phase_number == 3:
                parameters = 'kwL3'
            with open(os.path.join(DATA_FILES_DIR, '{}.csv'.format(file.split(".")[0])), newline='') as csvfile:
                data = list(csv.reader(csvfile))
            df=pd.DataFrame(data)
            df = df.rename(columns=df.iloc[0, :])
            time = df.iloc[1:, 0]
            time = [dateutil.parser.parse(s) for s in time]
            df = df.iloc[1:, 1:].apply(pd.to_numeric)  # the name row appears twice, so remove it
            dfs = df[parameters] # the i'th parameter
            energy_df=pd.DataFrame(columns=['timestamp','kw'])
            energy_df['timestamp']=time
            energy_df['kw']=dfs.values
            E=calc_energy(E, energy_df)
        print(str(time[0])+"-"+str(time[-1]))
        print('Energy in kWh:')
        print(np.transpose(E)[-1,:]/3600)
energy_main_func()
#def calc_phase_energy(phase):
  #  phase = phase - 1  # match an index
  #  col_list_power = ["kW L1", "kW L2", "kW L3"]  # ["kW L2"]#["kW L1", "kW L2", "kW L3"]
  #  df = pd.read_csv("data.csv", usecols=col_list_power)  # TODO: change to relevant file name instead of data.csv
  # Energ = []
  #  sum = 0
   # for x in range(df.shape[0]):
   #     sum = sum + df[col_list_power[phase]][x]
   #     Energ.append(sum)
    #return (Energ)


#def calc_energy():
 #   E = []
 #   for i in range(1, 4):
 #       E.append(calc_phase_energy(i))
 #   return (np.array(E))


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


def plot_param_2(CSV_FLAG, columns, Ts,num):
    # Customization per parameter

    # columns = ["timestamp", "kwL1", "kwL2", "kwL3"]
    for i in range(1, len(columns)):
        if columns[i] == 'kvar L1':
            print('frr')
        # dfs=df.iloc[:,i]
        # if '1' in df.keys()[i]:
        #     phase=1
        # elif '2' in df.keys()[i]:
        #     phase=2
        # elif '3' in df.keys()[i]:
        #     phase=3

        if Ts >= 30:
            if Ts % 60 == 0:
                s_Ts = '{}[min]'.format(int(Ts / 60))
            else:
                s_Ts = '{}[min]'.format(Ts / 60)
        else:
            s_Ts = '{}[sec]'.format(int(Ts))
        # colors = ["blue", "red", "green"]
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
                dfs = abs(dfs)
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
            # plt.gcf()
            myFmt = mdates.DateFormatter('%H:%M')
            plt.gca().xaxis.set_major_formatter(myFmt)
            # plt.title('{}, Ts= {}'.format(columns[i] + '(t)', s_Ts))
        # plt.tight_layout()
    plt.show()



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


def func(day_in,holiday_in):
    s3 = boto3.client('s3')
    objects = []
    valid = 0
    paginator =s3.get_paginator('list_objects_v2')
    pages =paginator.paginate(Bucket='satec-flamiingo')
    for page in pages :
        for obj in page['Contents']:
            if valid < 6 :
                objects.append(obj['Key'])
                valid = valid + 1
    for date in objects :
        year = date[0:4]
        month= date[4:6]
        day = date[6:8]
        new_format=  str(month + '-' + day + '-' +year)
        new_format_t = pd.Timestamp(new_format)
        if holiday_in == "holiday":
            if (new_format_t.day_name() == day_in) and (new_format_t in holidays.Israel()):
                return date
        else:
            if (new_format_t.day_name() == day_in) and (new_format_t not in holidays.Israel()) :
                return date


def findfile(DATA_FILES_DIR):
    filenames = []
    s3 = boto3.client('s3')
    choice = int(input("choose an option : 1.date                   2.day in the week\n"))
    num = int(input("Please enter number of days :"))
    if choice==2 :
        for i in range(num):
            print("Please enter day #" , end ="")
            print(i+1 ,end="")
            day_in = input(str(" in the week\n"))
            holiday_in = input(str("Choose: holiday/workday\n"))
            file_name = func(day_in,holiday_in)
            filenames.append(file_name)
    else:
        file_name = 'yeardate0000_yeardate2359.csv'
        print ("Now enter the dates in order in %m-%d-%y format")
        for i in range(num):
            print("Date of day #" , end="")
            print(i+1 ,end=": ")
            scanner = str(input())
            to_timestamp = pd.Timestamp(scanner)
            to_format = datetime.datetime.strptime(scanner, '%m-%d-%Y').strftime('%Y%m%d')
            print("The day you requested is a", to_timestamp.day_name(), end=", ")
            if to_timestamp in holidays.Israel() or to_timestamp.day_name() == "Friday" or to_timestamp.day_name() =="Saturday" :
                print("this day is a holiday")
            else :
                print("this day is a workday")
            file_name = file_name.replace(file_name[0:8],   to_format)
            file_name = file_name.replace(file_name[13:21],  to_format)
            filenames.append(file_name)
    for obj in filenames :
        to_download = obj
        to_download_path =str(DATA_FILES_DIR +'\\' + to_download)
        try:
            s3.download_file("satec-flamiingo", to_download, to_download_path)
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "404":
                print("The requested file does not exist.")
                exit(1)
    join = os.path.join(DATA_FILES_DIR, "*.csv")
    return num


def merge_csv_files(DATA_FILES_DIR,DATA_FILES_DIR2):  #no need for this function anymore
    file_list = [DATA_FILES_DIR + "\\" + f for f in os.listdir(DATA_FILES_DIR)]
    csv_list = []
    csv_list=[pd.read_csv(file) for file in file_list]
    csv_merged = pd.concat(csv_list, ignore_index=True)
    csv_merged.to_csv(DATA_FILES_DIR2 + "\\" + 'merged.csv', index=False)

# --------MAIN----------#
if __name__ == '__main__':
    DATA_FILES_DIR = r"C:\Users\Public\Project\Compare"
    # on your computer open an empty folder called downloads and put here the path
    num = findfile(DATA_FILES_DIR)
    dont_change =DATA_FILES_DIR
    # on your computer open an empty folder called downloads and put here 2
    # the path
    DATA_FILES_DIR2 = r"C:\Users\Public\Project\merged"
    # on your computer open an empty folder called merged and put here the path
    if (input("do you want to compare days?: yes/no:")=="yes"):
        DATA_FILES_DIR = dont_change
    else:
        merge_csv_files(DATA_FILES_DIR, DATA_FILES_DIR2)
        DATA_FILES_DIR = DATA_FILES_DIR2
    files = os.listdir(DATA_FILES_DIR)
    file = files[0]
    if not file.endswith("csv"):
        for file in files:
            get_data(DATA_FILES_DIR, file)
        print('Plotting requested files ...')
        columns = list(['timestamp', 'I3'])
    else:
        print('Plotting requested files ...')
        columns = list(['timestamp', 'I1', 'V1', 'P1', 'PF1'])
    #gen_plots(file,num, ['mock_param'], -1, CSV_FLAG=1, columns=columns)  # built for csv from dekel
    Ts = 1
    CSV_FLAG=1
    for x in ['mock_param']:
        plot_param_2(CSV_FLAG , columns, Ts,num)
    os.chdir(dont_change)
    all_files = os.listdir()
    for f in all_files:
        os.remove(f)
    # else: #print a parameter of each file seperatly
    #     for file in files:
    #         # mdb from yuval
    #         if file.endswith("mdb"):# TODO: make sure file.startswith(phase):
    #             print(file)
    #             phase = str(input("Please enter Phase: the options are 1, 2, 3"))
    #             if phase not in ["1", "2", "3"]:
    #                 raise IOError("please choose phase 1, 2, 3 ")
    #             # params = str(input("Please choose parameters: the options are I, P, Q, V, ANG, THD"))
    #             # if params not in ['I', 'P', 'Q', 'V', 'ANG', 'THD']:
    #             #     raise IOError("please choose params from the list")
    #             params=['I']
    #             get_data(DATA_FILES_DIR, file)
    #             gen_plots(file,params, int(phase),CSV_FLAG=0,columns=[])#columns is un-used
    #             # plt.show()

