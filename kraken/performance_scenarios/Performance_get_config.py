# coding:utf-8
import yaml
import itertools
import time
import subprocess
import kraken.performance_scenarios.utils as utils
import kraken.performance_scenarios.log as log
import kraken.performance_scenarios.Performance_scenarios
from subprocess import *
from threading import Thread

from collections import OrderedDict as Odd
try:
    import configparser as cp
except Exception:
    import ConfigParser as cp




   
class Self_defined_scenarios(object):
    def __init__(self,config_file):
        self.config_file = config_file
        self.cfg = self.read_config_file()
        utils.prt_log('', f"Get config file information ", 0)
  

    def read_config_file(self): 
        a_yaml_file = open(self.config_file)
        all_config = yaml.load(a_yaml_file, Loader = yaml.FullLoader)
        return all_config


    def perforamce_global(self): 
        Global_str=""
        Get_Global=self.cfg.get('PerformanceGlobal')
        Get_Global_1= Get_Global.split()
        for i in range(len(Get_Global_1)):
            Global_str = Global_str + Get_Global_1[i] + '\n'
        return Global_str 


    def perforamce_setting(self):
        perforamce_setting=self.cfg.get('PerformanceSetting')
        return perforamce_setting






class Seq_rw_scenarios(object):
    def __init__(self,config_file):
        self.config_file = config_file
        self.cfg = self.read_config_file()
        utils.prt_log('', f"Get config file information ", 0)
  

    def read_config_file(self): 
        a_yaml_file = open(self.config_file)
        all_config = yaml.load(a_yaml_file, Loader = yaml.FullLoader)
        return all_config


    def perforamce_global(self): 
        Run_time = str(self.cfg.get('run_time'))
        size = self.cfg.get('size')
        Global_str = 'ioengine=libaio' + '\n' + 'direct=1' + '\n' + 'ramp_time=10' + '\n' + 'runtime=' + Run_time + '\n' + 'size=' + size + '\n' + 'group_reporting' + '\n' + 'new_group' + '\n'
        return Global_str 


    def perforamce_setting(self):
        device_info=self.cfg.get('test_device_info')
        perforamce_setting = {'filename': device_info, 'rw': ['read', 'write'], 'bs': ['1k', '2k', '4k', '8k', '16k', '32k', '64k', '128k', '256k', '512k', '1M','2M'], 'iodepth': ['8'], 'numjobs': ['8']}
        return perforamce_setting





class Video_scenarios(object):
    def __init__(self,config_file):
        self.config_file = config_file
        self.cfg = self.read_config_file()
        utils.prt_log('', f"Get config file information ", 0)
  

    def read_config_file(self): 
        a_yaml_file = open(self.config_file)
        all_config = yaml.load(a_yaml_file, Loader = yaml.FullLoader)
        return all_config


    def perforamce_global(self): 
        Run_time = str(self.cfg.get('run_time'))
        size = self.cfg.get('size')
        Global_str = 'ioengine=libaio' + '\n' + 'direct=1' + '\n' + 'ramp_time=10' + '\n' + 'runtime=' + Run_time + '\n' + 'size=' + size + '\n' + 'group_reporting' + '\n' + 'new_group' + '\n'
        return Global_str 


    def perforamce_setting(self):
        device_info=self.cfg.get('test_device_info')
        perforamce_setting = {'filename': device_info, 'rw': ['read', 'write'], 'bs': ['64k', '128k', '256k', '512k', '1M'], 'iodepth': ['8'], 'numjobs': ['1']}
        return perforamce_setting





class Random_rw_scenarios(object):
    def __init__(self,config_file):
        self.config_file = config_file
        self.cfg = self.read_config_file()
        utils.prt_log('', f"Get config file information ", 0)


    def read_config_file(self): 
        a_yaml_file = open(self.config_file)
        all_config = yaml.load(a_yaml_file, Loader = yaml.FullLoader)
        return all_config


    def perforamce_global(self): 
        Run_time = str(self.cfg.get('run_time'))
        size = self.cfg.get('size')
        Global_str = 'ioengine=libaio' + '\n' + 'direct=1' + '\n' + 'ramp_time=10' + '\n' + 'runtime=' + Run_time + '\n' + 'size=' + size + '\n' + 'group_reporting' + '\n' + 'new_group' + '\n' + 'rwmixread=75' + '\n'
        return Global_str 


    def perforamce_setting(self):
        device_info=self.cfg.get('test_device_info')
        perforamce_setting = {'filename': device_info, 'rw': ['randrw'], 'bs': ['1k', '2k', '4k', '8k', '16k', '32k', '64k'], 'iodepth': ['8'], 'numjobs': ['16']}
        return perforamce_setting





class Handle_performance_data():
    def __init__(self,dict_data):
        self.dict_data=dict_data


    def global_setting(self):
        self.list_value = []
        self.list_key = []
        list_value_all = []
        self.perforamce_setting_list=[]

        for key, value in sorted(self.dict_data.items()):
            if key=="filename" or key=="directory":
                self.list_key.insert(0,key)
                self.list_value.insert(0,self.dict_data[key])

            elif key=="rw":
                self.list_key.insert(1,key)
                self.list_value.insert(1,self.dict_data[key])

            else:
                self.list_key.append(key)
                self.list_value.append(value)

        for i in itertools.product(*self.list_value, repeat=1):
            list_value_all.append(i)
        for i in range(len(list_value_all)):
            dict_aaa=dict(zip(self.list_key,list_value_all[i]))
            self.perforamce_setting_list.append(dict_aaa)
        return self.perforamce_setting_list


    def file_name(self):
        self.name_list=[]
        for dict_l in self.perforamce_setting_list:
            dict_temp = dict_l.copy()
            if 'filename' in dict_l.keys():
                path = dict_l['filename'].split('/')[-1]
                dict_temp.update({'filename':path})
            elif 'directory' in dict_l.keys():
                path = dict_l['directory'].split('/')[-1]
                dict_temp.update({'directory':path})
            name = '_'.join(dict_temp.values())
            self.name_list.append(name)
        return self.name_list





class Run_performance_case():
    def __init__(self,results_name,global_str,perforamce_setting_list,name_list):
        self.results_name = results_name
        self.global_str = global_str
        self.perforamce_setting_list = perforamce_setting_list
        self.name_list = name_list
        self.create_fio_file()
        utils.prt_log('', f"Create fio file automatically", 0)
        self.run_fio()


    def create_fio_file(self):
        str_setting_list_all=[]
        str_setting_list=[]
        for i in range(len(self.perforamce_setting_list)):
            for j,k  in zip(self.perforamce_setting_list[i].keys(),self.perforamce_setting_list[i].values()):
                str_setting='{}={}'.format(j,k)
                str_setting_list_all.append(str_setting)
        count=len(self.perforamce_setting_list[i].keys())
        for i in range(0,len(str_setting_list_all),count):
            str_setting_list.append(str_setting_list_all[i:i+count])

        length=len(self.name_list)
        for index in range(length):
            fio_file=open(self.name_list[index]+'.fio','w')
            str_to_file='\n'.join(str_setting_list[index])
            fio_file.write('[global]'+'\n'+self.global_str+'\n'+'['+self.name_list[index]+']'+'\n'+str_to_file+'\n')
        fio_file.close()
        return True


    def clear_copy(self):
        directory_list = []
        for i in range(len(self.perforamce_setting_list)):
            if 'directory' in self.perforamce_setting_list[i]:
                aa = self.perforamce_setting_list[i]['directory']
                directory_list.append(aa)
        directory_list = list(set(directory_list))
        if len(directory_list) != 0:
            for i in directory_list:
                command='rm -f ' + i + '/*'
                subprocess.call (command,shell=True)



    def run_fio(self):
        time_n = time.localtime(time.time())
        Date = time.strftime('%Y-%m-%d %H:%M:%S',time_n) 
        command_update = ['apt update --fix-missing'] 
        subprocess.getstatusoutput(command_update)
        command_f = ['apt install -y fio'] 
        code,data = subprocess.getstatusoutput(command_f)
        if code == 0:
            utils.write_log('', f"install software fio, Done", 0)
        else:
            utils.write_log('', data, 1)
        utils.prt_log('', f"running fio , it could be take a long time......", 0)
        for name_l in range(len(self.name_list)):
            self.clear_copy()
            Thread(target = Get_sys_info).start()
            fio_command="fio"+" "+self.name_list[name_l]+".fio"+" "+">>"+" "+self.results_name
            code = subprocess.call (fio_command,shell=True)
            if code ==0:
                utils.prt_log('', fio_command , 0)
            else:
                rm_command = "rm *.fio"
                subprocess.call (rm_command,shell=True)
                utils.prt_log('', f"Device does not exist or fio command failed,please check /scenarios/P_xxx.yml file!", 2)
            #Get_sys_info()




class Get_draw_info(object):
    def __init__(self,config_name):
        self.config_name = config_name
        self.cfg = self.read_config_file()
        self.count_info()
  

    def read_config_file(self): 
        try:
            a_yaml_file = open(self.config_name)    
            all_config = yaml.load(a_yaml_file, Loader = yaml.FullLoader)
            return all_config
        except OSError as reason:
            str11 = str(self.config_name) + ' file does not exist'
            utils.prt_log('', str11, 2)

    def UID_info(self): 
        UID = self.cfg.get('unique_ID')
        return UID 

    def count_info(self): 
        self.count = self.cfg.get('run_count')
        return self.count

    def draw_info(self):
        draw_list = []
        excel_info = self.cfg.get('write_to_excel')
        chart_info = self.cfg.get('line_chart')
        histogram_info = self.cfg.get('histogram')
        draw_list.append(excel_info)
        draw_list.append(chart_info)
        draw_list.append(histogram_info)
        return draw_list
 


class Get_sys_info(object):
    def __init__(self):
        time_n = time.localtime(time.time())
        self.Date = time.strftime('%Y-%m-%d %H:%M:%S',time_n) 
        self.install_soft()
        self.get_htop_info()
        self.get_atop_info()
        self.get_top_info()
        self.get_iostat_info()
        


    def install_soft(self): 
        command = 'apt install -y htop atop sysstat aha html2text'
        code,data = subprocess.getstatusoutput(command)
        if code == 0 :
            utils.write_log('', f"install htop or atop or aha or html2text software , Done", 0)
            utils.write_log('', f"\n \n", 0)
        else:
            utils.write_log('', f"htop or atop or aha or html2text software install failed", 1)


    def get_htop_info(self): 
        try:
            date_command = 'date >> ./kraken/performance_scenarios/performance_data/sysinfo.txt'
            subprocess.run(date_command,shell=True)

            #command1 = 'ls *.txt >> ./kraken/performance_scenarios/performance_data/sysinfo.txt'
            command1 = 'echo q | htop -C | aha --line-fix | html2text -width 999 | grep -v "F1Help" | grep -v "xml version=" >> ./kraken/performance_scenarios/performance_data/sysinfo.txt'
            check = subprocess.run(command1,shell=True)
            check_code = check.check_returncode()
            utils.write_log('', f"Write htop info to kraken/performance_scenarios/performance_data/sysinfo.txt file , Done", 0)

            echo_command = 'echo " " >> ./kraken/performance_scenarios/performance_data/sysinfo.txt'
            subprocess.run(echo_command,shell=True)
        except:
            utils.write_log('', f"htop command not found or aha/html2text software not install", 1)


    def get_atop_info(self): 
        try:
            date_command = 'date >> ./kraken/performance_scenarios/performance_data/sysinfo.txt'
            subprocess.run(date_command,shell=True)

            command1 = 'atop -r | head -60  >> ./kraken/performance_scenarios/performance_data/sysinfo.txt'
            check = subprocess.run(command1,shell=True)
            check_code = check.check_returncode()
            utils.write_log('', f"Write atop info to kraken/performance_scenarios/performance_data/sysinfo.txt file , Done", 0)

            echo_command = 'echo " "  >> ./kraken/performance_scenarios/performance_data/sysinfo.txt'
            subprocess.run(echo_command,shell=True)
        except:
            utils.write_log('', f"atop command not found or software not install", 1)


    def get_top_info(self): 
        try:
            date_command = 'date >> ./kraken/performance_scenarios/performance_data/sysinfo.txt'
            subprocess.run(date_command,shell=True)

            command1 = 'top  -n 55 -b -d 30 | head -55 >> ./kraken/performance_scenarios/performance_data/sysinfo.txt'
            check = subprocess.run(command1,shell=True)
            check_code = check.check_returncode()
            utils.write_log('', f"Write top info to kraken/performance_scenarios/performance_data/sysinfo.txt file , Done", 0)

            echo_command = 'echo " "  >> ./kraken/performance_scenarios/performance_data/sysinfo.txt'
            subprocess.run(echo_command,shell=True)
        except:
            utils.write_log('', f"top command not found or software not install", 1)


    def get_iostat_info(self): 
        try:
            date_command = 'date >> ./kraken/performance_scenarios/performance_data/sysinfo.txt'
            subprocess.run(date_command,shell=True)

            command1 = 'iostat -x 1 5 /dev/* >> ./kraken/performance_scenarios/performance_data/sysinfo.txt'
            check = subprocess.run(command1,shell=True)
            check_code = check.check_returncode()
            utils.write_log('', f"Write iostat info to kraken/performance_scenarios/performance_data/sysinfo.txt file , Done", 0)

            echo_command = 'echo " "  >> ./kraken/performance_scenarios/performance_data/sysinfo.txt'
            subprocess.run(echo_command,shell=True)
            #print('iostatttttttttttttttttttttttt info')
        except:
            utils.write_log('', f"iostat command not found or software not install", 1)





if __name__ == '__main__':
    pass
    
