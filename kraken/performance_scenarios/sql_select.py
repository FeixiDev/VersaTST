import sqlite3
import csv
from prettytable.prettytable import from_db_cursor
import yaml
# import Performance_get_config as gc
# import sql_chart as gcdb
from xlwt import Workbook
import xlrd
import xlwt
import kraken.performance_scenarios.utils as utils
import kraken.performance_scenarios.log as log


class write_excel_manual (object):
    def __init__(self):
        a_yaml_file = open('./scenarios/P_sql_config.yml')
        self.a = yaml.load(a_yaml_file, Loader = yaml.FullLoader)


    def sql_analysis_output(self):

        con = sqlite3.connect ('sqldatabase_test.db') # create connection object and database file
        cur = con.cursor() # create a cursor for connection object
        for i in range(len(self.a['table'])):
            sql_sentence = 'SELECT' + ' ' +  self.a['wanted data'] + ' ' + 'From' + ' ' + self.a['table'][i]+' '+'where'+' '+self.a['statement']
            cur.execute(sql_sentence)
            x = from_db_cursor(cur)
            print (self.a['table'][i])
            print (x)
        

        Excel_filename = input ('Please Enter the name of the Excel file will be created:')
        cur.execute(sql_sentence)
        with open(f"{Excel_filename}.csv","w") as csv_file:
            csv_writer = csv.writer(csv_file, delimiter="\t")
            csv_writer.writerow([i[0] for i in cur.description])
            csv_writer.writerows(cur)

        cur.close()
        con.commit()
        con.close()


    def sql_analysis_output_2(self):

        con = sqlite3.connect ('sqldatabase_test.db') # create connection object and database file
        cur = con.cursor() # create a cursor for connection object
        sql_sentence = 'SELECT'+' '+self.a['wanted data1']+' '+'FROM'+' '+self.a['table1'] +' '+'where'+' '+self.a['statement1'] +' '+ 'UNION ALL' + ' ' + 'SELECT'+' '+self.a['wanted data2']+' '+'from'+' '+self.a['table2'] +' '+'where'+' '+self.a['statement2']
       
        cur.execute((sql_sentence))
        x = from_db_cursor(cur)
        print(x)

        excel_filename = input ('Please Enter the name of the Excel file will be created:')
        
        cur.execute(sql_sentence)
        with open(f"{excel_filename}.csv","w") as csv_file:
            csv_writer = csv.writer(csv_file, delimiter="\t")
            csv_writer.writerow([i[0] for i in cur.description])
            csv_writer.writerows(cur)

        cur.close()
        con.commit()
        con.close()






class sql_write_excel (object):
    def __init__(self,Table_Names,rw_type):
        self.table_n = Table_Names
        self.rwType_info = rw_type


    def write_to_excel_all(self):
        con = sqlite3.connect ('sqldatabase_test.db')
        cur = con.cursor()
        table = 'Index_table,' + self.table_n
        Excel_filename = self.table_n + '_' + 'all_data_excel'

        for i in range(len(self.rwType_info)):
            rw = '"{}"'.format(self.rwType_info[i])
            statement = 'Index_table.Key_ID = '+ self.table_n + '.Key_ID' + ' '+ 'AND Readwrite_type =' + rw #+ ' ' +'ORDER BY IOPS'
            SQL_Sentence = 'select'+' '+ '*' +' '+'from'+' '+ table +' '+'where'+' '+ statement
            sql_result = cur.execute((SQL_Sentence))
            cur.execute(SQL_Sentence)
            with open(f"./kraken/performance_scenarios/performance_data/{Excel_filename}.csv","a+") as csv_file:
                csv_writer = csv.writer(csv_file, delimiter="\t")
                csv_writer.writerow([i[0] for i in cur.description])
                csv_writer.writerows(cur)
        str1 = 'Save ' +  Excel_filename + '.csv to performance_data directory , Done'
        utils.write_log('', str1, 0)
        cur.close()
        con.commit()
        con.close()


    def get_data_IO_MB(self,rwType_bs):
        self.rwType = rwType_bs
        con = sqlite3.connect ('sqldatabase_test.db')
        cur = con.cursor()
        self.IOPS_list = []
        self.MBPS_list = []
        rwType_info ='"{}"'.format(self.rwType)
        SQL_Sentence = 'select'+' '+ 'IOPS'+' '+'FROM'+' '+self.table_n +' '+'WHERE'+' '+ 'Readwrite_type='+ ' '+rwType_info
        sql_result = cur.execute((SQL_Sentence))
        for row in sql_result:
            self.IOPS_list.append(row[0])

        SQL_Sentence = 'select'+' '+ 'MBPS'+' '+'FROM'+' '+self.table_n +' '+'WHERE'+' '+ 'Readwrite_type='+ ' '+rwType_info
        sql_result = cur.execute((SQL_Sentence))
        for row in sql_result:
            self.MBPS_list.append(row[0])
        cur.close()
        con.commit()
        con.close()


    def write_to_excel_bs(self,dict_data,rwType,iodepth,numjobs):
        # self.excel_name = '222222-read.csv'
        self.dict_data = dict_data
        self.rwType = rwType
        self.iodepth = iodepth
        self.numjobs = numjobs
        self.excel_name = self.table_n + '_' + self.rwType + '.csv'
        if "filename" in self.dict_data:
            self.parameter_dict =  {'filename': '\\w+', 'rw': self.rwType, 'bs': '\\w+', 'iodepth': self.iodepth, 'numjobs': self.numjobs}
            filename_value='true'
        else:
            self.parameter_dict =  {'directory': '\\w+', 'rw': self.rwType, 'bs': '\\w+', 'iodepth': self.iodepth, 'numjobs': self.numjobs}
            filename_value='false'
        wb = Workbook(encoding='utf-8')
        table = wb.add_sheet('IOPS',cell_overwrite_ok=True)
        sheet = wb.add_sheet('MBPS',cell_overwrite_ok=True)
        attri=['bs','iodepth','numjobs']
        for value in attri:
            if self.parameter_dict[value]=='\w+':
                for i in range(len(self.dict_data[value])):
                    # print('ddddvvv',self.MBPS_list)
                    sheet.write(1,i+1,self.dict_data[value][i]) 
                    sheet.write(2,i+1,self.MBPS_list[i])  
                    table.write(1,i+1,self.dict_data[value][i]) 
                    table.write(2,i+1,self.IOPS_list[i]) 
                    number=len(self.MBPS_list)/len(self.dict_data[value])
                    for row in range(int(number)):
                        sheet.write(2+row,i+1,self.MBPS_list[i+len(self.dict_data[value])*row])
                        table.write(2+row,i+1,self.IOPS_list[i+len(self.dict_data[value])*row]) 
        if filename_value == 'true':
            attri_l=['rw','filename']
        else:
            attri_l=['rw','directory']

        for value in attri_l:
            if self.parameter_dict[value]=='\w+':
                for i in range(len(self.dict_data[value])):
                    sheet.write(i+2,0,self.dict_data[value][i])
                    table.write(i+2,0,self.dict_data[value][i]) 
        list_param=[]
        for k,v in self.parameter_dict.items():
            if self.parameter_dict[k]!='\w+':
                list_param.append(f'{k}={v}')
        sheet.write_merge(0,0,0,5,','.join(list_param),self.excel_style())
        table.write_merge(0,0,0,5,','.join(list_param),self.excel_style())
        # file_dir = '/performance_data'
        wb.save(f"./kraken/performance_scenarios/performance_data/{self.excel_name}")
        str1 = 'Save ' +  self.excel_name + ' to performance_data directory , Done'
        utils.write_log('', str1, 0)


    def excel_style(self):
        style = xlwt.XFStyle() # 初始化样式
        al = xlwt.Alignment()
        al.horz = 0x02     
        al.vert = 0x01      
        style.alignment = al
        return style
 



if __name__ == '__main__':
    pass



