import sqlite3
import numpy as np
import matplotlib
# matplotlib.use ('TKAgg')
matplotlib.use ('Agg')
import matplotlib.pyplot as plt
import yaml
from prettytable.prettytable import from_db_cursor
import kraken.performance_scenarios.utils as utils
import kraken.performance_scenarios.log as log




class graph_chart_manual (object):
    def __init__(self):
        a_yaml_file = open('./scenarios/P_sql_config.yml')
        self.a = yaml.load(a_yaml_file, Loader = yaml.FullLoader)


    def sql_graph_output(self):

        con = sqlite3.connect ('sqldatabase_test.db') # create connection object and database file
        cur = con.cursor() # create a cursor for connection object

        sql_sentence = 'SELECT'+ ' ' +'DRBD_Type, blocksize, '+ self.a['Select_Data']+' '+'FROM'+' '+self.a['Table_Names'] +' '+'WHERE'+' '+ 'Readwrite_type =' + self.a['ReadWrite_Type'] + ' ' + 'AND' + ' ' + 'Number_of_Job =' + self.a['Number_of_Job'] + 'AND' + ' '+ 'IOdepth =' + self.a['IOdepth']
        sql_result = cur.execute(sql_sentence)
        
        values = []
        drbd = []
        all_blocksize = []
        
        for row in sql_result:
            values.append(row[2])
            all_blocksize.append(row[1])
            drbd.append(row[0])
        # print (values)
        blocksize_range = list(set(all_blocksize))
        blocksize_range.sort(key=all_blocksize.index)

        number_of_drbd = len(values) // len(blocksize_range)

        values2 = []
        drbd_type = []
        for i in range(number_of_drbd):
            values2.append(values[:len(blocksize_range)])
            values = values[len(blocksize_range):]
            drbd_type.append(drbd[len(blocksize_range)*i])
        # print (values2)

        plt.figure(figsize=(20,20), dpi = 100)
        plt.xlabel ('Block Size')
        plt.ylabel (self.a['Select_Data'])
        
        for j in range(number_of_drbd):
            x = blocksize_range
            y = values2[j]
            plt.plot(x,y, label = drbd_type[j])
        
        plt.title(self.a['Table_Names'] + '-' + self.a['Select_Data'] + '-' + self.a['ReadWrite_Type'])
        plt.legend()
        plt.grid()

        file_name = self.a['Table_Names'] + '-' + self.a['ReadWrite_Type'] + '-' + self.a['Select_Data'] + ' ' + 'chart'
        plt.savefig(file_name)
        plt.draw()
        plt.close(1)
        # plt.show()

        cur.close()
        con.commit()
        con.close()


    def sql_print_drbd(self):
        
        con = sqlite3.connect ('sqldatabase_test.db') # create connection object and database file
        cur = con.cursor() # create a cursor for connection object

        sql_sentence = 'SELECT DRBD_Type From' + ' ' + self.a['Table_Names_rw']
        data = cur.execute(sql_sentence)

        for row in set(data):
            print (row[0])

        cur.close()
        con.commit()
        con.close()


    def sql_graph_rw(self):

        con = sqlite3.connect ('sqldatabase_test.db') # create connection object and database file
        cur = con.cursor() # create a cursor for connection object

        drbd = input ("Please enter the drbd type:")
        sql_sentence = 'SELECT'+ ' ' +'Readwrite_type, blocksize, '+ self.a['Select_Data_rw']+' '+'FROM'+' '+self.a['Table_Names_rw'] +' '+'WHERE'+' '+ 'DRBD_type =' + '"'+ drbd + '"' + ' ' + 'AND' + ' ' + 'Number_of_Job =' + self.a['Number_of_Job_rw'] + 'AND' + ' '+ 'IOdepth =' + self.a['IOdepth_rw']
        sql_result = cur.execute(sql_sentence)
        
        values = []
        readwrite = []
        all_blocksize = []
        
        for row in sql_result:
            values.append(row[2])
            all_blocksize.append(row[1])
            readwrite.append(row[0])
        blocksize_range = list(set(all_blocksize))
        blocksize_range.sort(key=all_blocksize.index)    
        number = len(values) // len(blocksize_range)
        
        values2 = []
        readwrite_type = []
        for i in range(number):
            values2.append(values[:len(blocksize_range)])
            values = values[len(blocksize_range):]
            readwrite_type.append(readwrite[len(blocksize_range)*i])
        # print (values2)

        plt.figure(figsize=(20,20), dpi = 100)
        plt.xlabel ('Block Size')
        plt.ylabel (self.a['Select_Data'])
        
        for j in range(number):
            x = blocksize_range
            y = values2[j]
            plt.plot(x,y, label = readwrite_type[j])
        
        plt.title(self.a['Table_Names_rw'] + '-' + self.a['Select_Data_rw'] + '-' + drbd)
        plt.legend()
        plt.grid()

        file_name = self.a['Table_Names_rw'] + '-' + drbd + '-' + self.a['Select_Data_rw'] + ' ' + 'chart'
        plt.savefig(file_name)
        # plt.show()
        
        cur.close()
        con.commit()
        con.close()





class Get_info_db (object):
    def __init__(self,Table_Names):
        self.Table_Names = Table_Names
        self.get_bs_db()
        self.get_rwType_db()
        self.get_nj_db()
        self.get_IOdepth_db()


    def get_bs_db(self):
        con = sqlite3.connect ('sqldatabase_test.db')
        cur = con.cursor() 
        sql_sentence = 'SELECT'+ ' ' +'Blocksize'+' '+'FROM'+' '+self.Table_Names
        sql_result = cur.execute(sql_sentence)
        bs = []
        for row in sql_result:
            bs.append(row[0])
        block_size = list(set(bs))
        block_size.sort(key=bs.index)
        cur.close()
        con.commit()
        con.close()
        return block_size


    def get_rwType_db(self):
        con = sqlite3.connect ('sqldatabase_test.db')
        cur = con.cursor() 
        sql_sentence2 = 'SELECT'+ ' ' +'ReadWrite_type'+' '+'FROM'+' '+self.Table_Names
        sql_result2 = cur.execute(sql_sentence2)
        rw_ty = []
        for row in sql_result2:
            rw_ty.append(row[0])
        rw_type = list(set(rw_ty))
        rw_type.sort(key=rw_ty.index)
        cur.close()
        con.commit()
        con.close()
        return rw_type


    def get_nj_db(self):
        con = sqlite3.connect ('sqldatabase_test.db')
        cur = con.cursor() 
        sql_sentence3 = 'SELECT'+ ' ' +'Number_of_Job'+' '+'FROM'+' '+self.Table_Names
        sql_result3 = cur.execute(sql_sentence3)
        nj_l = []
        for row in sql_result3:
            nj_l.append(row[0])
        nj = list(set(nj_l))
        nj.sort(key=nj_l.index)
        cur.close()
        con.commit()
        con.close()
        return nj


    def get_IOdepth_db(self):
        con = sqlite3.connect ('sqldatabase_test.db')
        cur = con.cursor() 
        sql_sentence4 = 'SELECT'+ ' ' +'IOdepth'+' '+'FROM'+' '+self.Table_Names
        sql_result4 = cur.execute(sql_sentence4)
        IOdepth_l = []
        for row in sql_result4:
            IOdepth_l.append(row[0])
        IOdepth = list(set(IOdepth_l))
        IOdepth.sort(key=IOdepth_l.index)
        cur.close()
        con.commit()
        con.close()
        return IOdepth


    def get_device_db(self):
        con = sqlite3.connect ('sqldatabase_test.db')
        cur = con.cursor() 
        sql_sentence5 = 'SELECT'+ ' ' +'DRBD_Type'+' '+'FROM'+' '+self.Table_Names
        sql_result5 = cur.execute(sql_sentence5)
        device_l = []
        for row in sql_result5:
            device_l.append(row[0])
        device_list = list(set(device_l))
        device_list.sort(key=device_l.index)
        
        cur.close()
        con.commit()
        con.close()
        return device_list





class sql_graph_chart (object):
    def __init__(self,Table_Name):
        self.table_n = Table_Name
        self.y_Data = ['IOPS','MBPS']
        get_info = Get_info_db(self.table_n)
        self.blocksize_range = get_info.get_bs_db()
        self.rwType_info = get_info.get_rwType_db()
        self.nj_info = get_info.get_nj_db()
        self.IOd_info = get_info.get_IOdepth_db()
        self.draw_graph_chart()


    def draw_graph_chart(self):
        con = sqlite3.connect ('sqldatabase_test.db')
        cur = con.cursor()
        values = []
        drbd= []
        for i in range(len(self.y_Data)):
            for rw in range(len(self.rwType_info)):
                rwType_info ='"{}"'.format(self.rwType_info[rw])
                for nj in range(len(self.nj_info)):
                    nj_info ='"{}"'.format(self.nj_info[nj])
                    for io in range(len(self.IOd_info)): 
                        IOd_info ='"{}"'.format(self.IOd_info[io])
                        sql_sentence = 'SELECT'+ ' ' +'DRBD_Type,'+self.y_Data[i]+' '+'FROM'+' '+self.table_n +' '+'WHERE'+' '+ 'Readwrite_type=' + rwType_info+ ' ' + 'AND' + ' ' + 'Number_of_Job =' + nj_info + ' ' + 'AND' + ' '+ 'IOdepth =' + IOd_info
                        sql_result = cur.execute(sql_sentence)
                        for row in sql_result:
                            values.append(row[1])
                            drbd.append(row[0])


        length = len(self.blocksize_range)
        number_of_drbd = len(values) // length
        
        values2 = []
        drbd_type = []
        for i in range(number_of_drbd):
            values2.append(values[:length])
            values = values[length:]
            drbd_type.append(drbd[length*i])

        plt.figure(figsize=(20,20), dpi = 100)
        plt.xlabel ('Block Size')
        ylabel = ''

        drbd_t = list(set(drbd_type))
        drbd_t.sort(key=drbd_type.index)
        n = len(drbd_t)
        num_of_picture = int(number_of_drbd / n)
        IO_MB_value = num_of_picture / 2

        flag = 0

        for b in [values2[i:i + n] for i in range(0, len(values2), n)]:
                if num_of_picture <= IO_MB_value:
                    ylabel = 'MBPS'
                else:
                    ylabel = 'IOPS'
                num_of_picture = num_of_picture -1
                plt.title(self.table_n + '-' + ylabel + '-' + self.rwType_info[flag])
                file_name = self.table_n+ '-' + ylabel + '-' + self.rwType_info[flag]

                x = self.blocksize_range
                for yy in range(len(b)):
                    plt.plot(x,b[yy],label = drbd_type[yy])

                flag +=1
                if flag == len(self.rwType_info):
                    flag = 0 
                plt.legend()
                plt.grid()
                plt.savefig(f"./kraken/performance_scenarios/performance_data/{file_name}")  
                str1 = 'Save ' +  file_name + '.png to performance_data directory , Done'
                utils.write_log('', str1, 0)
                plt.draw()
                plt.close(1)

        cur.close()
        con.commit()
        con.close()


if __name__ == '__main__':
    pass
    # sql_graph_output()


    
