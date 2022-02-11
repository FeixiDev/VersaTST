# coding:utf-8
import yaml
import itertools
import time
import subprocess
from pathlib import Path
import os.path
import sys
import kraken.performance_scenarios.Performance_get_config as gc
import kraken.performance_scenarios.sql_input as sql
import kraken.performance_scenarios.sql_chart as chart
import kraken.performance_scenarios.sql_histogram as histogram
import kraken.performance_scenarios.sql_select as excel
import kraken.performance_scenarios.utils as utils
import kraken.performance_scenarios.log as log
import kraken.performance_scenarios.basic as ind
import sqlite3
from threading import Thread


   

Client_Name = 'Auto_GZ'
Disk_Type = 'Auto_type'




class Check_log_dir(object):
    def __init__(self):
        self.Log_dir = Path("./kraken/performance_scenarios/performance_log")
        self.check_log_file_fun()
        self.check_performance_test_yaml()

    def check_log_file_fun(self): 
        if self.Log_dir.exists() == False:
            os.mkdir(self.Log_dir)

    def check_performance_test_yaml(self):

        config_file = Path('./config/performance_test.yaml')
        config_str = '''#performance test config yaml file 
kraken:
    signal_state: RUN                                                            
    VersaTest_version: v1.0.0                               
    distribution: performance                                # Required,performance test distribution
    chaos_scenarios:                                     
        -   performance_scenarios:
              - -    scenarios/P_self_defined_scenario.yml
                #- -    scenarios/P_seq_rw_scenario.yml
                #- -    scenarios/P_random_rw_scenario.yml
                #- -    scenarios/P_video_scenario.yml
                #- -    scenarios/P_sql_config.yml 

        '''

        if config_file.exists() == False:
            file = open(config_file,'w')
            file.write(config_str)
            file.close()






class Check_file_dir(object):
    def __init__(self):
        self.Performance_dir = Path("./kraken/performance_scenarios/performance_data")
        self.Config_dir = Path("config")
        self.Sql_db_file = Path('sqldatabase_test.db')
        #self.Sql_db_file = Path('./kraken/performance_scenarios/sqldatabase_test.db')
        self.check_dir_file_fun()
        self.check_db_file()
        self.check_self_defined_yml()
        self.check_seq_rw_yml()
        self.check_video_yml()
        self.check_random_rw_file()


    def check_dir_file_fun(self): 

        if self.Performance_dir.exists() == False:
            utils.prt_log('', f"Creating performance_data directory automatically", 0)
            os.mkdir(self.Performance_dir)

        if self.Config_dir.exists() == False:
            utils.prt_log('', f"Creating config directory automatically", 0)
            os.mkdir(self.Config_dir)


    def check_db_file(self): 
        if self.Sql_db_file.exists() == False:
            utils.prt_log('', f"Creating sqldatabase_test.db file automatically", 0)
            command = 'touch ' + 'sqldatabase_test.db'
            subprocess.run(command,shell=True)
            con = sqlite3.connect ('sqldatabase_test.db') 
            cur = con.cursor()
            cur.execute('''CREATE TABLE Index_Table
                            (Key_ID integer,
                            Client_Name text,
                            Date text,
                            Disk_Type text,
                            Text_Table_Name text
                            )''')
            cur.close()
            con.commit()
            con.close()


    def check_self_defined_yml(self): 

        config_file = Path('./scenarios/P_self_defined_scenario.yml')
        config_str = '''#self_defined_config yaml file
PerformanceGlobal:
  ioengine=libaio 
  direct=1 
  ramp_time=10
  runtime=120
  size=70%
  group_reporting
  new_group

#if test directory,please input size=size_capacity on PerformanceGlobal
PerformanceSetting: 
  filename: [/dev/sdx,/dev/sdxx]
  bs: [1k,2k,4k,8k,16k,32k,64k,128k,256k,512k,1M,2M]
  rw: [read,write,randread,randwrite]
  iodepth: ['8']
  numjobs: ['8']

run_count: 1
unique_ID: 10000
write_to_excel: False
line_chart: False
histogram: False

        '''

        if config_file.exists() == False:
            file = open(config_file,'w')
            file.write(config_str)
            file.close()
            utils.prt_log('', f"Creating P_self_defined_scenario.yml file automatically", 0)


    def check_seq_rw_yml(self): 

        config_file = Path('./scenarios/P_seq_rw_scenario.yml')
        config_str = '''#sequential read/write test
run_count: 1
run_time: 120
test_device_info: [/dev/sdxx,/dev/sdxxx] 
size: 70%

unique_ID: 20000
write_to_excel: False
line_chart: False
histogram: False

        '''

        if config_file.exists() == False:
            file = open(config_file,'w')
            file.write(config_str)
            file.close()
            utils.prt_log('', f"Creating P_seq_rw_scenario.yml file automatically", 0)



    def check_video_yml(self): 

        config_file = Path('./scenarios/P_video_scenario.yml')
        config_str = '''#Video scenario read/write test

run_count: 1
run_time: 120
test_device_info: [/dev/sdxx,/dev/sdxxx] 
size: 70%

unique_ID: 30000
write_to_excel: False
line_chart: False
histogram: False

        '''

        if config_file.exists() == False:
            file = open(config_file,'w')
            file.write(config_str)
            file.close()
            utils.prt_log('', f"Creating P_video_scenario.yml file automatically", 0)


    def check_random_rw_file(self): 

        config_file = Path('./scenarios/P_random_rw_scenario.yml')
        config_str = '''#random read/write scenario test

run_count: 1
run_time: 120
test_device_info: [/dev/sdxx,/dev/sdxxx] 
size: 70%

unique_ID: 40000
write_to_excel: False
line_chart: False
histogram: False

        '''

        if config_file.exists() == False:
            file = open(config_file,'w')
            file.write(config_str)
            file.close()
            utils.prt_log('', f"Creating P_random_rw_scenario.yml file automatically", 0)





class Self_defined_case(object):
    def __init__(self,config_file):
        self.config_file =  config_file
        time_n = time.localtime(time.time())
        self.results_name = time.strftime('%m_%d_%H_%M',time_n)+'_'+'results.txt'  
        self.perforamce_info()
        self.run_test()
        IOd = self.per_setting.get('iodepth')[0] #only support the first iodepth value
        job = self.per_setting.get('numjobs')[0] #only support the first numjobs value
        Run_selected_function(self.config_file,self.results_name,self.per_setting,IOd,job )
        self.rm_fio()


    def perforamce_info(self): 
        Performance_config = gc.Self_defined_scenarios(self.config_file)
        self.Global_str = Performance_config.perforamce_global()
        self.per_setting = Performance_config.perforamce_setting()

        Performance_data = gc.Handle_performance_data(self.per_setting)
        self.perforamce_setting_list = Performance_data.global_setting()
        self.name_list = Performance_data.file_name()


    def run_test(self):
        test = gc.Run_performance_case(self.results_name,self.Global_str,self.perforamce_setting_list,self.name_list)


    def rm_fio(self):
        for i in range(len(self.name_list)):
            command = 'rm ' + self.name_list[i]+'.fio'
            subprocess.run(command,shell=True)
        utils.prt_log('', f"Remove all .fio file automatically after test", 0)



class Seq_rw_case(object):
    def __init__(self,config_file):
        self.config_file = config_file
        time_n = time.localtime(time.time())
        self.results_name = time.strftime('%m_%d_%H_%M',time_n)+'_'+'results.txt'  
        self.perforamce_info()
        self.run_test()
        IOd = self.per_setting.get('iodepth')[0]
        job = self.per_setting.get('numjobs')[0]
        Run_selected_function(self.config_file,self.results_name,self.per_setting,IOd,job)
        self.rm_fio()


    def perforamce_info(self): 
        Performance_config = gc.Seq_rw_scenarios(self.config_file)
        self.Global_str = Performance_config.perforamce_global()
        self.per_setting = Performance_config.perforamce_setting()
        Performance_data = gc.Handle_performance_data(self.per_setting)
        self.perforamce_setting_list = Performance_data.global_setting()
        self.name_list = Performance_data.file_name()


    def run_test(self):
        test = gc.Run_performance_case(self.results_name,self.Global_str,self.perforamce_setting_list,self.name_list)


    def rm_fio(self):
        for i in range(len(self.name_list)):
            command = 'rm ' + self.name_list[i]+'.fio'
            subprocess.run(command,shell=True)
        utils.prt_log('', f"Remove all .fio file automatically after test", 0)


class Video_scenarios_case(object):
    def __init__(self,config_file):
        self.config_file = config_file
        time_n = time.localtime(time.time())
        self.results_name = time.strftime('%m_%d_%H_%M',time_n)+'_'+'results.txt' 
        self.perforamce_info()
        self.run_test()
        IOd = self.per_setting.get('iodepth')[0]
        job = self.per_setting.get('numjobs')[0]
        Run_selected_function(self.config_file,self.results_name,self.per_setting,IOd,job)
        self.rm_fio()


    def perforamce_info(self): 
        Performance_config = gc.Video_scenarios(self.config_file)
        self.Global_str = Performance_config.perforamce_global()
        self.per_setting = Performance_config.perforamce_setting()
        Performance_data = gc.Handle_performance_data(self.per_setting)
        self.perforamce_setting_list = Performance_data.global_setting()
        self.name_list = Performance_data.file_name()


    def run_test(self):
        test = gc.Run_performance_case(self.results_name,self.Global_str,self.perforamce_setting_list,self.name_list)


    def rm_fio(self):
        for i in range(len(self.name_list)):
            command = 'rm ' + self.name_list[i]+'.fio'
            subprocess.run(command,shell=True)
        utils.prt_log('', f"Remove all .fio file automatically after test", 0)


class Random_rw_scenarios_case(object):
    def __init__(self,config_file):
        self.config_file = config_file
        time_n = time.localtime(time.time())
        self.results_name = time.strftime('%m_%d_%H_%M',time_n)+'_'+'results.txt' 
        self.perforamce_info()
        self.run_test()
        IOd = self.per_setting.get('iodepth')[0]
        job = self.per_setting.get('numjobs')[0]
        Run_selected_function(self.config_file,self.results_name,self.per_setting,IOd,job)
        self.rm_fio()


    def perforamce_info(self): 
        Performance_config = gc.Random_rw_scenarios(self.config_file)
        self.Global_str = Performance_config.perforamce_global()
        self.per_setting = Performance_config.perforamce_setting()
        Performance_data = gc.Handle_performance_data(self.per_setting)
        self.perforamce_setting_list = Performance_data.global_setting()
        self.name_list = Performance_data.file_name()


    def run_test(self):
        test = gc.Run_performance_case(self.results_name,self.Global_str,self.perforamce_setting_list,self.name_list)


    def rm_fio(self):
        for i in range(len(self.name_list)):
            command = 'rm ' + self.name_list[i]+'.fio'
            subprocess.run(command,shell=True)
        utils.prt_log('', f"Remove all .fio file automatically after test", 0)




class Run_selected_function(object):
    def __init__(self,config_file,results_name,per_setting,iodepth,job):
        time_n = time.localtime(time.time())
        self.Date = time.strftime('%y%m%d%H%M',time_n)
        self.results_name = results_name
        self.config_file = config_file
        self.per_setting = per_setting 
        self.iodepth = iodepth
        self.job = job
        Draw_config = gc.Get_draw_info(self.config_file)
        self.UID = Draw_config.UID_info()
        self.function_info()
        self.write_to_db()
        self.run_funtion()


    def function_info(self): 
        Draw_config = gc.Get_draw_info(self.config_file)
        self.draw_info = Draw_config.draw_info()


    def write_to_db(self): 
        handle_data = sql.Handle_data_function(self.results_name)
        self.list_data = handle_data.handle_mbps()
        sql.Write_to_database(self.UID,Client_Name,self.Date,Disk_Type,self.list_data)
        str_old = 'unique_ID: ' + str(self.UID)
        self.UID = self.UID + 1
        str_new = 'unique_ID: ' + str(self.UID)
        with open(self.config_file,'r+',encoding='utf-8') as filetxt:
            lines=filetxt.read()
            filetxt.seek(0)
            lines=lines.replace(str_old,str_new)
            filetxt.write(lines)
        filetxt.close()
        utils.prt_log('', f"Write data to sqldatabase_test.db automatically", 0)


    def run_funtion(self):
        Select_Data = ['IOPS','MBPS']
        Table_Names = Client_Name + '_' + self.Date + '_' + Disk_Type

        if self.draw_info[0] == True:
            get_info = chart.Get_info_db(Table_Names)
            rwType_info = get_info.get_rwType_db()
            exc = excel.sql_write_excel(Table_Names,rwType_info)
            exc.write_to_excel_all()
            utils.prt_log('', f"Write all data to excel one table automatically , Done", 0)

            for i in range(len(rwType_info)):
                exc.get_data_IO_MB(rwType_info[i])    
                exc.write_to_excel_bs(self.per_setting,rwType_info[i],self.iodepth,self.job)
            utils.prt_log('', f"Write all data to excel bs table automatically , Done", 0)

        else:
            utils.prt_log('', f"Not write to excel.....", 0)

        if self.draw_info[1] == True:
            chart.sql_graph_chart(Table_Names)
            utils.prt_log('', f"Drawing line chart , Done", 0)
        else:
            utils.prt_log('', f"Not draw line chart.....", 0)
            
        if self.draw_info[2] == True:
            utils.prt_log('', f"Drawing histogram picture", 0)
            IOPS_4K_list = ['IOPS','4k']
            MBPS_1M_list = ['MBPS','1M']
            histogram_run = histogram.sql_graph_histogram(Table_Names)
            fn_l,val=histogram_run.get_data_histogram(IOPS_4K_list)
            if len(val) != 0:
                histogram_run.draw_graph_histogram(fn_l,val)
                utils.prt_log('', f"Draw IOPS_4k histogram picture , Done", 0)
            fn_l2,val2=histogram_run.get_data_histogram(MBPS_1M_list)
            if len(val2) != 0:
                histogram_run.draw_graph_histogram(fn_l2,val2)
                utils.prt_log('', f"Draw MBPS_1M histogram picture , Done", 0)

        else:
            utils.prt_log('', f"Not draw histogram picture.....", 0)



class Run_test(object):
    def __init__(self,config_yml,signal=False):
        self.config_yml = config_yml
        self.signal = signal
        #Check_file_dir()
        Draw_config = gc.Get_draw_info(self.config_yml)
        self.count = Draw_config.count_info()
        self.run_selected_test()


    def run_selected_test(self): 
        if self.count is None:
            self.count = 1

        for i in range(self.count):
            basic_fun = ind.Basic_function()
            print_info = basic_fun.sql_print_index()
            if 'self_defined' in self.config_yml:
                utils.prt_log('', f"run self defined test", 0)
                if self.signal == True:
                    get_down_info = utils.ConfFile('./scenarios/P_nic_info.yml')
                    hostname,port,ip,password,interface= get_down_info.get_P_interface_info()
                    action = utils.SSHConn(host=ip,password=password)
                    action.down_interface(interface)
                    Self_defined_case(self.config_yml)
                    action.up_interface(interface)
                else:
                    Self_defined_case(self.config_yml)
                utils.prt_log('', f"run self defined test , Done", 0)
                subprocess.run('mv *.txt ./kraken/performance_scenarios/performance_data',shell=True)
                command = 'mv ./kraken/performance_scenarios/performance_data/requirements.txt ' + str(sys.path[0])
                subprocess.run(command,shell=True)
                utils.prt_log('', f"\n \n \n ", 0)
                time.sleep(20)

            elif 'seq_rw' in self.config_yml:
                utils.prt_log('', f"run seq rw test", 0)
                if self.signal == True:
                    get_down_info = utils.ConfFile('./scenarios/P_nic_info.yml')
                    hostname,port,ip,password,interface= get_down_info.get_P_interface_info()
                    action = utils.SSHConn(host=ip,password=password)
                    action.down_interface(interface)
                    Seq_rw_case(self.config_yml)
                    action.up_interface(interface)
                else:
                    Seq_rw_case(self.config_yml)
                utils.prt_log('', f"run seq rw test , Done", 0)
                subprocess.run('mv *.txt ./kraken/performance_scenarios/performance_data',shell=True)
                command = 'mv ./kraken/performance_scenarios/performance_data/requirements.txt ' + str(sys.path[0])
                subprocess.run(command,shell=True)
                utils.prt_log('', f"\n \n \n ", 0)
                time.sleep(20)

            elif 'video_scenario' in self.config_yml:
                utils.prt_log('', f"run Video scenarios test", 0)
                if self.signal == True:
                    get_down_info = utils.ConfFile('./scenarios/P_nic_info.yml')
                    hostname,port,ip,password,interface= get_down_info.get_P_interface_info()
                    action = utils.SSHConn(host=ip,password=password)
                    action.down_interface(interface)
                    Video_scenarios_case(self.config_yml)
                    action.up_interface(interface)
                else:
                    Video_scenarios_case(self.config_yml)
                utils.prt_log('', f"run Video scenarios test , Done", 0)
                subprocess.run('mv *.txt ./kraken/performance_scenarios/performance_data',shell=True)
                command = 'mv ./kraken/performance_scenarios/performance_data/requirements.txt ' + str(sys.path[0])
                subprocess.run(command,shell=True)
                utils.prt_log('', f"\n \n \n ", 0)
                time.sleep(20)

            elif 'random_rw' in self.config_yml:
                utils.prt_log('', f"run random rw scenarios test", 0)
                if self.signal == True:
                    get_down_info = utils.ConfFile('./scenarios/P_nic_info.yml')
                    hostname,port,ip,password,interface= get_down_info.get_P_interface_info()
                    action = utils.SSHConn(host=ip,password=password)
                    action.down_interface(interface)
                    Random_rw_scenarios_case(self.config_yml)
                    action.up_interface(interface)
                else:
                    Random_rw_scenarios_case(self.config_yml)
                utils.prt_log('', f"run random rw scenarios test , Done", 0)
                subprocess.run('mv *.txt ./kraken/performance_scenarios/performance_data',shell=True)
                command = 'mv ./kraken/performance_scenarios/performance_data/requirements.txt ' + str(sys.path[0])
                subprocess.run(command,shell=True)
                utils.prt_log('', f"\n \n \n ", 0)
                time.sleep(20)

            else:
                utils.prt_log('', f"cannot found scenarios,please check!", 2)
                sys.exit(1)



if __name__ == '__main__':
    pass
    # utils._init()
    # logger = log.Log()
    # utils.set_logger(logger)
    # Run_test('P_self_defined_scenario.yml')
    # Control_test('P_seq_rw_scenario.yml')
    # Control_test('P_random_rw_scenario.yml')
    # Control_test('P_video_scenario.yml')




