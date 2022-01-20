import re
import os
import os.path
import sqlite3
import yaml
import sys
from prettytable.prettytable import from_db_cursor



class Get_database_info(object):
    def __init__(self):
        self.all_config()


    def all_config(self):
        a_yaml_file = open('./scenarios/P_sql_config.yml')
        self.all_config = yaml.load(a_yaml_file, Loader = yaml.FullLoader)


    def test_file_config(self):
        file_input = self.all_config['file input']
        return file_input


    def kid_config(self):
        K_ID = self.all_config['Key ID']
        return K_ID


    def client_config(self):
        K_name = self.all_config['Client Name']
        return K_name


    def date_config(self):
        Date_info = self.all_config['Date']
        return Date_info


    def disk_config(self):
        disk_t = self.all_config['Disk Type']
        return disk_t





class Run_test_for_main(object):
    def __init__(self):
        self.handle_data()


    def handle_data(self):
        test = Get_database_info()
        file_input = test.test_file_config()
        run = Handle_data_function(file_input)
        list_data = run.handle_mbps()

        Key_ID = test.kid_config()
        Client_Name = test.client_config()
        Date = test.date_config()
        Disk_Type = test.disk_config()

        Write_to_database(Key_ID,Client_Name,Date,Disk_Type,list_data)





class Handle_data_function(object):
    def __init__(self,file_input):
        self.file_input = file_input
        self.list_data = []
        self.get_all_data()
        self.handle_iops()



    def get_all_data(self):
        file = open(self.file_input,'r')
        results = file.read()
        re_=r'([a-zA-Z0-9_]+)_([a-zA-Z0-9]+)_([a-zA-Z0-9]+)_(\d+)_(\d+).*\s*.*IOPS=([a-zA-Z0-9.]+).*\s*.*B/s\s\((.+/s)\)' # Regular Expression
        re_pattern = re.compile(re_)
        re_result = re_pattern.findall(results)

        for i in re_result:
            self.list_data.append(list(i))
        file.close()


    def handle_iops(self):
        for data in self.list_data:
            iops_value = data[5]
            if iops_value == '':
                data[5]= ''
            elif iops_value[-1]=='k': 
                IOPS_k = float(float(iops_value[:-1]) * 1000)
                data[5] = IOPS_k
            else:
                IOPS_r = float(iops_value)


    def handle_mbps(self):
        for data in self.list_data:
            mbps_value = data[6]
            if mbps_value == '':
                data[6]= ''
            elif mbps_value[3:][-4:] == 'kB/s': 
                MBPS_k = float(mbps_value[:-4]) / 1000
                MBPS_k = float("%.2f" % MBPS_k)
                data[6]= MBPS_k
            elif mbps_value[3:][-4:] == 'GB/s':
                MBPS_g = float((mbps_value[:-4]))*1.07
                MBPS_g = float("%.1f" % MBPS_g)
                MBPS_g = int(MBPS_g*1000)
                data[6]= MBPS_g
            else:
                MBPS_r = float(mbps_value[:-4]) 
                data[6]= MBPS_r
        return self.list_data





class Write_to_database(object):
    def __init__(self,Key_ID,Client_Name,Date,Disk_Type,list_data):
        self.Key_ID = Key_ID
        self.Client_Name = Client_Name
        self.Date = Date
        self.Disk_Type = Disk_Type
        self.list_data = list_data
        self.create_db_table()
        self.SQL_text_input()


    def create_db_table(self):
        con = sqlite3.connect ('sqldatabase_test.db') # create connection object and database file
        cur = con.cursor() # create a cursor for connection object
        self.Text_Table_Name = (self.Client_Name + '_' + self.Date + '_' + self.Disk_Type)

        # print('tttttbbbbname',self.Text_Table_Name )
        if self.Key_ID == '' or self.Key_ID == None or self.Key_ID == ' ':
            print ("Please enter a unique_ID or Key ID in config file")
            sys.exit()


        try:
            cur.execute('''CREATE TABLE Index_Table
                            (Key_ID integer,
                            Client_Name text,
                            Date text,
                            Disk_Type text,
                            Text_Table_Name text
                            )''')
        except:
            pass
            # print('Index table already exist！')

        query = '''INSERT INTO Index_Table (Key_ID, Client_Name, Date, Disk_Type, Text_Table_Name) values (?, ?, ?, ?, ?)'''

        check_query = 'SELECT KeY_ID, Text_Table_Name from Index_Table'
        check_list = cur.execute (check_query)
        check_ID = []
        check_table_name = []
        for row in check_list:
            check_ID.append(row[0])
            check_table_name.append(row[1])


        if int(self.Key_ID) in check_ID:
            print ("The key ID is repeated. Please enter another key ID")
            sys.exit()

        if self.Text_Table_Name in check_table_name:
            print ("The table already exist! Please check on yml config file")
            sys.exit()

        values = (self.Key_ID, self.Client_Name, self.Date, self.Disk_Type, self.Text_Table_Name )
        cur.execute (query,values)
        
        sql_result = cur.execute('SELECT * FROM Index_Table')
        x = from_db_cursor(cur)
        print (x)
        cur.close()
        con.commit()
        con.close()



    def SQL_text_input(self):
        con = sqlite3.connect ('sqldatabase_test.db') # create connection object and database file
        cur = con.cursor() # create a cursor for connection object
        
        try:
            cur.execute(f'''CREATE TABLE {self.Text_Table_Name}
                            (Key_ID integer,
                            DRBD_type text,
                            Readwrite_type text,
                            blocksize text,
                            IOdepth text,
                            Number_of_Job text,
                            IOPS real,
                            MBPS real
                            )''')
        
            table_info= '+----------------------------+' + self.Text_Table_Name + ' informastion' + '+------------------------+'
            print(table_info)
            query = f'''INSERT INTO {self.Text_Table_Name} (Key_ID, DRBD_type, Readwrite_type, blocksize, IOdepth, Number_of_Job, IOPS, MBPS) values (?,?,?,?,?,?,?,?)'''
            for data in self.list_data:      
                DRBD_type = data[0]
                Readwrite_type = data[1]
                blocksize = data[2]
                IOdepth = data[3]
                Number_of_Job = data[4]
                IOPS = data[5]
                MBPS = data[6]

                values = (self.Key_ID, DRBD_type, Readwrite_type, blocksize, IOdepth, Number_of_Job, IOPS, MBPS)
                cur.execute(query, values)
                sql_result = f'SELECT * FROM {self.Text_Table_Name}'

            cur.execute(sql_result)
            x = from_db_cursor(cur)
            print (x)
            cur.close()
            con.commit()
            con.close()

        except:
            print('Table already exist！')




if __name__ == '__main__':
    pass
    # Run_test_for_main()


