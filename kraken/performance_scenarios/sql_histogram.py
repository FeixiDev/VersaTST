import sqlite3
import numpy as np
import matplotlib as mpl
from prettytable.prettytable import from_db_cursor
import yaml
mpl.use ('Agg')
# mpl.use ('TKAgg')
import matplotlib.pyplot as plt
import kraken.performance_scenarios.utils as utils
import kraken.performance_scenarios.log as log
import kraken.performance_scenarios.sql_chart as gcdb


class graph_histogram_manual (object):
    def __init__(self):
        a_yaml_file = open('./scenarios/P_sql_config.yml')
        self.a = yaml.load(a_yaml_file, Loader = yaml.FullLoader)

    def graph_histogram_output(self):

        con = sqlite3.connect ('sqldatabase_test.db') # create connection object and database file
        cur = con.cursor() # create a cursor for connection object

        text_table = []
        drbd = []
        values = []
        

        for i in range(len(self.a['Table_hist'])):
            sql_sentence = 'SELECT Text_Table_Name, DRBD_Type,' + ' ' + self.a['Select_Data_hist'] + ' ' + 'FROM Index_table,' +  self.a['Table_hist'][i] \
                    + ' ' + 'WHERE Readwrite_type = ' + self.a['Readwrite_hist']\
                    + ' ' + 'AND Number_of_Job = ' + self.a['Number_of_Job_hist']\
                    + ' ' + 'AND IOdepth = ' + self.a['IOdepth_hist']\
                    + ' ' + 'AND blocksize = ' + self.a['Blocksize_hist']\
                    + ' ' + 'AND Index_table.Key_ID =' + ' ' + self.a['Table_hist'][i] + '.Key_ID' \

            sql_result = cur.execute(sql_sentence)
        
            for row in sql_result:
                text_table.append(row[0])
                drbd.append(row[1])
                values.append(row[2])
                # print(row)
      
        plt.figure(figsize=(20,20), dpi = 100)
        bar_width = 0.3

        for i in range(len(drbd)):
            x_data = drbd[i]
            y_data = values[i]
            plt.bar(x_data, y_data, label = text_table[i], width = bar_width)
        plt.xlabel ('DRBD Type')
        plt.ylabel (self.a['Select_Data_hist'])
        plt.xticks (rotation = 30)
        
        for x,y in zip(drbd,values):
            plt.text(x, y+0.05, '%.2f' % y, ha = 'center', va = 'bottom', fontsize = 11)

        plt.title(self.a['Select_Data_hist'] + ' ' + 'under Different DRBD Type (Readwrite type = ' + self.a['Readwrite_hist'] + ', Blockszie =' + self.a['Blocksize_hist'] + ')')
        plt.legend()
        plt.grid()
        save_file_name = str(self.a['Table_hist'][0]) + '-' + 'histogram'  + '-' + str(self.a['Select_Data_hist'])  + '-' + self.a['Readwrite_hist'] + '-' + str(self.a['Blocksize_hist']) + '.png'
        plt.legend()
        plt.grid()
        plt.savefig(save_file_name)
        plt.draw()
        plt.close(1)
        # plt.show()

        cur.close()
        con.commit()
        con.close()





class sql_graph_histogram (object):
    def __init__(self,Table_Names):
        self.table_n = Table_Names
        get_info = gcdb.Get_info_db(self.table_n)
        self.rwType_info = get_info.get_rwType_db()
        self.nj_info = get_info.get_nj_db()
        self.IOPS_4K_list = ['IOPS','4k']
        self.MBPS_1M_list = ['MBPS','1M']


    def get_data_histogram(self,IO_MB_list):
        con = sqlite3.connect ('sqldatabase_test.db')
        cur = con.cursor()
        self.IO_MB_list = IO_MB_list
        file_name_list = []
        self.drbd = []
        values = []
        
        for i in range(len(self.rwType_info)):
            nj_info ='"{}"'.format(self.nj_info[0])
            bs = '"{}"'.format(self.IO_MB_list[1])
            rw = '"{}"'.format(self.rwType_info[i])
            sql_sentence = 'SELECT DRBD_Type,' + ' ' + self.IO_MB_list[0] + ' ' + 'FROM Index_table,' +  self.table_n \
                + ' ' + 'WHERE Readwrite_type = ' + rw\
                + ' ' + 'AND Number_of_Job = ' + nj_info \
                + ' ' + 'AND IOdepth = "8"'\
                + ' ' + 'AND blocksize =' + bs \
                + ' ' + 'AND Index_table.Key_ID =' + ' ' + self.table_n + '.Key_ID' \
            
            sql_result = cur.execute(sql_sentence)
            file_name =  'histogram' + '-' + self.IO_MB_list[0] + '-' + self.rwType_info[i] + '-' + self.IO_MB_list[1] 
            file_name_list.append(file_name)
            for row in sql_result:
                self.drbd.append(row[0])
                values.append(row[1])
        cur.close()
        con.commit()
        con.close()
        return file_name_list,values



    def draw_graph_histogram(self,fn_list,values):
        drbd_t = list(set(self.drbd))
        if len(drbd_t) == 0:
            utils.prt_log('', f"Table has not bs=4k or bs=1M data", 1)
        drbd_t.sort(key=self.drbd.index)
        utils.prt_log('', drbd_t, 0)
        num_of_device = len(drbd_t)
        plt.figure(figsize=(20,20), dpi = 100)
        bar_width = 0.3 

        flag = 0
        for b in [values[i:i + num_of_device] for i in range(0, len(values), num_of_device)]:
            # print('bbbbb',b)
            for i in range(len(drbd_t)):
                x_data = self.drbd[i]
                y_data = b[i]
                plt.bar(x_data, y_data, label=drbd_t[i],width = bar_width)
                plt.title(fn_list[flag])
            plt.xlabel ('DRBD Type')
            if 'IOPS' in str(fn_list[0].split('-')):
                plt.ylabel (self.IOPS_4K_list[0])
            else:
                plt.ylabel (self.MBPS_1M_list[0])

            plt.xticks (rotation = 30)
            plt.legend()
            plt.grid()
            png_name = self.table_n +'-' + fn_list[flag]
            plt.savefig(f"./kraken/performance_scenarios/performance_data/{png_name}")
            str1 = 'Save ' + png_name + '.png to performance_data directory , Done'
            utils.write_log('', str1, 0)
            flag +=1
            if flag == len(self.rwType_info):
                flag = 0 
            plt.draw()
            plt.close()
            # plt.show()



if __name__ == '__main__':
    pass
    # sql_graph_output()




