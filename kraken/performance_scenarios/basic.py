import sqlite3
from prettytable.prettytable import from_db_cursor
from matplotlib.pyplot import table
import kraken.performance_scenarios.utils as utils
import kraken.performance_scenarios.log as log
import yaml




class Basic_function(object):
    def __init__(self):
        TABLE_NAME = ''

    def view_sql_data(self):
        
        a_yaml_file = open('./scenarios/P_sql_config.yml')
        a = yaml.load(a_yaml_file, Loader = yaml.FullLoader)

        con = sqlite3.connect ('sqldatabase_test.db') # create connection object and database file
        cur = con.cursor() # create a cursor for connection object

        for i in range(len(a['table view'])):

            sql_sentence = 'SELECT' + ' ' +  a['wanted data view'] + ' ' + 'From' + ' ' + a['table view'][i]
            # print (sql_sentence)
        
            # x = prettytable
            cur.execute(sql_sentence)
            
            x = from_db_cursor(cur)

            print (a['table view'][i])
            print (x)

        cur.close()
        con.commit()
        con.close()


    def sql_print_index(self):
    
        con = sqlite3.connect ('sqldatabase_test.db') # create connection object and database file
        cur = con.cursor() # create a cursor for connection object

        cur.execute('SELECT * From Index_Table')
            
        x = from_db_cursor(cur)
        # prscenarios./scenarios/P_sql_config.yml)
        utils.prt_log('', x , 0)

        cur.close()
        con.commit()
        con.close()


    def drop_table(self):
        drop = input('Please Enter the name of the table you want to delete:')
        
        global TABLE_NAME
        TABLE_NAME = drop

        while drop == 'Index_Table':
            Print ('Index Table could not be delected')
            drop = input('Please Enter the name of the table you want to delete:')
            
        con = sqlite3.connect ('sqldatabase_test.db') # create connection object and database file
        cur = con.cursor() # create a cursor for connection object

        sql_sentence_table = f'DROP TABLE {drop}'
        cur.execute(sql_sentence_table)
        cur.close()
        con.commit()
        con.close()

    def drop_row(self): 
        con = sqlite3.connect ('sqldatabase_test.db') # create connection object and database file
        cur = con.cursor() # create a cursor for connection object
        
        sql_sentence_row = f'DELETE FROM Index_Table WHERE Text_Table_Name = "{TABLE_NAME}"'
        cur.execute(sql_sentence_row)
        
        data = cur.execute('SELECT * from Index_Table')
        x = from_db_cursor(cur)
        print (x)

        cur.close()
        con.commit()
        con.close()


if __name__ == '__main__':
    pass
    # drop_table()
    # drop_row()
