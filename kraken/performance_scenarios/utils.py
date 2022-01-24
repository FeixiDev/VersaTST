# -*- coding: utf-8 -*-
import paramiko
import socket
import subprocess
import yaml
import sys
import re
import time
import traceback
from functools import wraps
import kraken.performance_scenarios.log
import os
from stat import S_ISDIR as isdir


def _init():  # 全局变量初始化
    global _GLOBAL_DICT
    _GLOBAL_DICT = {}

    global _TIMES
    _TIMES = 0

    global _LOGGER
    _LOGGER = None


def set_global_dict_value(key, value):
    _GLOBAL_DICT[key] = value


def get_global_dict_value(key):
    try:
        return _GLOBAL_DICT[key]
    except KeyError:
        # print("KeyError of global value.")
        return get_host_ip()


def set_times(value):
    global _TIMES
    _TIMES = value


def get_times():
    return _TIMES


def set_logger(value):
    global _LOGGER
    _LOGGER = value


def get_logger():
    return _LOGGER


def prt_log(conn, str_, warning_level):
    """
    print, write to log and exit.
    :param logger: Logger object for logging
    :param print_str: Strings to be printed and recorded
    """
    time_n = time.localtime(time.time())
    Date = time.strftime('%Y-%m-%d %H:%M:%S',time_n) 
    logger = get_logger()
    print(Date,str(str_))
    if warning_level == 0:
        logger.write_to_log(conn, 'INFO', 'INFO', 'finish', 'output', str_)
    elif warning_level == 1:
        logger.write_to_log(conn, 'INFO', 'WARNING', 'fail', 'output', str_)
    elif warning_level == 2:
        logger.write_to_log(conn, 'INFO', 'ERROR', 'exit', 'output', str_)
        sys.exit()

def write_log(conn, str_, warning_level):
    """
    print, write to log and exit.
    :param logger: Logger object for logging
    :param print_str: Strings to be printed and recorded
    """
    time_n = time.localtime(time.time())
    Date = time.strftime('%Y-%m-%d %H:%M:%S',time_n) 
    logger = get_logger()
    # print(Date,str(str_))
    if warning_level == 0:
        logger.write_to_log(conn, 'INFO', 'INFO', 'finish', 'output', str_)
    elif warning_level == 1:
        logger.write_to_log(conn, 'INFO', 'WARNING', 'fail', 'output', str_)
    elif warning_level == 2:
        logger.write_to_log(conn, 'INFO', 'ERROR', 'exit', 'output', str_)
        sys.exit()

def deco_yaml_dict(func):
    """
    装饰器，判断yaml文件的key是否存在，不存在则提示并退出
    :param func:
    :return:
    """

    @wraps(func)
    def wrapper(self, *args):
        try:
            result = func(self, *args)
            return result
        except Exception as e:
            self.logger.write_to_log(None, 'DATA', 'DEBUG', 'exception', '', str(traceback.format_exc()))
            print(f'Error:{e}')
            sys.exit()

    return wrapper


def exec_cmd(cmd, conn=None):
    logger = get_logger()
    oprt_id = log.create_oprt_id()
    func_name = traceback.extract_stack()[-2][2]
    logger.write_to_log(conn, 'DATA', 'STR', func_name, '', oprt_id)
    logger.write_to_log(conn, 'OPRT', 'CMD', func_name, oprt_id, cmd)
    if conn:
        result = conn.exec_cmd(cmd)
        logger.write_to_log(conn, 'DATA', 'CMD', func_name, oprt_id, result)
        return result
    else:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, encoding="utf-8")
        if p.returncode == 0:
            result = p.stdout
            logger.write_to_log(conn, 'DATA', 'CMD', func_name, oprt_id, {"st": True, "rt": result})
            return {"st": True, "rt": result}
        else:
            logger.write_to_log(conn, 'DATA', 'CMD', func_name, oprt_id, {"st": False, "rt": p.stderr})
            return {"st": False, "rt": p.stderr}


def upload_file(local, remote, conn=None):
    logger = get_logger()
    oprt_id = log.create_oprt_id()
    func_name = traceback.extract_stack()[-2][2]
    logger.write_to_log('', 'DATA', 'STR', func_name, '', oprt_id)
    logger.write_to_log('', 'OPRT', 'upload', func_name, oprt_id, f"{local} ==> {get_global_dict_value(conn)}:{remote}")
    if conn:
        result = conn.sftp_upload(local, remote)
    else:
        cmd = f'cp -r {local} {remote}'
        result = exec_cmd(cmd)
    logger.write_to_log('', 'DATA', 'upload', func_name, oprt_id, result)
    return result


def download_file(remote, local, conn=None):
    logger = get_logger()
    oprt_id = log.create_oprt_id()
    func_name = traceback.extract_stack()[-2][2]
    logger.write_to_log('', 'DATA', 'STR', func_name, '', oprt_id)
    logger.write_to_log('', 'OPRT', 'download', func_name, oprt_id,
                        f"{get_global_dict_value(conn)}:{remote} ==> {local}")
    if conn:
        result = conn.sftp_download(remote, local)
    else:
        cmd = f'cp -r {remote} {local}'
        result = exec_cmd(cmd)
    logger.write_to_log('', 'DATA', 'download', func_name, oprt_id, result)
    return result


def check_ip(ip):
    """检查IP格式"""
    re_ip = re.compile(
        r'^((2([0-4]\d|5[0-5]))|[1-9]?\d|1\d{2})(\.((2([0-4]\d|5[0-5]))|[1-9]?\d|1\d{2})){3}$')
    result = re_ip.match(ip)
    if result:
        return True
    else:
        print(f"ERROR in IP format of {ip}, please check.")
        return False


def _check_local(local):
    if not os.path.exists(local):
        try:
            # 可多层创建目录
            os.makedirs(local)
        except IOError as err:
            print(err)


# def get_file_on_path(path, type):
#     file_list = None
#     if type == "dmesg":
#         file_list = [log_file for log_file in os.listdir(path) if
#                      log_file.endswith('.log') and log_file.startswith('dmesg')]
#     return file_list


def get_host_ip():
    """
    查询本机ip地址
    :return: ip
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 100))
        ip = s.getsockname()[0]
    finally:
        s.close()

    return ip


def re_search(re_string, tgt_string, output_type='bool'):
    logger = get_logger()
    oprt_id = log.create_oprt_id()
    re_obj = re.compile(re_string)
    re_result = re_obj.search(tgt_string)
    logger.write_to_log(None, 'OPRT', 'REGULAR', 're_search', oprt_id, {'re': re_string, 'string': tgt_string})
    if re_result:
        if output_type == 'bool':
            re_result = True
        if output_type == 'groups':
            re_result = re_result.groups()
        if output_type == 'group':
            re_result = re_result.group()
    logger.write_to_log(None, 'DATA', 'REGULAR', 're_search', oprt_id, re_result)
    return re_result


def re_findall(re_string, tgt_string):
    logger = get_logger()
    oprt_id = log.create_oprt_id()
    re_obj = re.compile(re_string)
    logger.write_to_log(None, 'OPRT', 'REGULAR', 're_findall', oprt_id, {'re': re_string, 'string': tgt_string})
    re_result = re_obj.findall(tgt_string)
    logger.write_to_log(None, 'DATA', 'REGULAR', 're_findall', oprt_id, re_result)
    return re_result


class SSHConn(object):

    def __init__(self, host, port=22, username="root", password=None, timeout=8):
        self._host = host
        self._port = port
        self._timeout = timeout
        self._username = username
        self._password = password
        self.SSHConnection = None
        self.ssh_connect()

    def _connect(self):
        try:
            objSSHClient = paramiko.SSHClient()
            objSSHClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            objSSHClient.connect(self._host, port=self._port,
                                 username=self._username,
                                 password=self._password,
                                 timeout=self._timeout,
                                 allow_agent=False)
            # time.sleep(1)
            # objSSHClient.exec_command("\x003")
            self.SSHConnection = objSSHClient
        except:
            print(f" Failed to connect {self._host}")

    def ssh_connect(self):
        self._connect()
        if not self.SSHConnection:
            print(f'Connect retry for {self._host}')
            self._connect()
            if not self.SSHConnection:
                sys.exit()

    def exec_cmd(self, command):
        # TODO paramiko.ssh_exception.SSHException
        if self.SSHConnection:
            stdin, stdout, stderr = self.SSHConnection.exec_command(command)
            err = stderr.read()
            if len(err) > 0:
                err = err.decode() if isinstance(err, bytes) else err
                return {"st": False, "rt": err}
            data = stdout.read()
            if len(data) >= 0:
                data = data.decode() if isinstance(data, bytes) else data
                return {"st": True, "rt": data}

    def down_interface(self, device):
        cmd = f"ifconfig {device} down"
        result = self.exec_cmd(cmd)
        if result["st"]:
            str_info = 'Shutdowned interface:' + str(device)
            prt_log('',str_info,0)
            return True

    def up_interface(self, device):
        cmd = f"ifconfig {device} up"
        result = self.exec_cmd(cmd)
        if result["st"]:
            str_info = 'Opened interface:' + str(device)
            prt_log('',str_info,0)

            
            return True

    def sftp_upload(self, local, remote):
        sf = paramiko.Transport((self._host, self._port))
        sf.connect(username=self._username, password=self._password)
        sftp = paramiko.SFTPClient.from_transport(sf)

        def _is_exists(path, function):
            path = path.replace('\\', '/')
            try:
                function(path)
            except Exception as error:
                return False
            else:
                return True

        # 拷贝文件
        def _copy(sftp, local, remote):
            # 判断remote是否是目录
            if _is_exists(remote, function=sftp.chdir):
                # 是，获取local路径中的最后一个文件名拼接到remote中
                filename = os.path.basename(os.path.normpath(local))
                remote = os.path.join(remote, filename).replace('\\', '/')
            # 如果local为目录
            if os.path.isdir(local):
                # 在远程创建相应的目录
                _is_exists(remote, function=sftp.mkdir)
                # 遍历local
                for file in os.listdir(local):
                    # 取得file的全路径
                    localfile = os.path.join(local, file).replace('\\', '/')
                    # 深度递归_copy()
                    _copy(sftp=sftp, local=localfile, remote=remote)
            # 如果local为文件
            if os.path.isfile(local):
                try:
                    sftp.put(local, remote)
                except Exception as error:
                    print(error)
                    return {"st": False, "rt": f"{error}"}

        # 检查local
        if not _is_exists(local, function=os.stat):
            return {"st": False, "rt": f"{local}: No such file or directory in local"}
        # 检查remote的父目录
        remote_parent = os.path.dirname(os.path.normpath(remote))
        if not _is_exists(remote_parent, function=sftp.chdir):
            return {"st": False, "rt": f"{remote}: No such file or directory in remote"}
        # 拷贝文件
        _copy(sftp=sftp, local=local, remote=remote)
        return {"st": True, "rt": f"{local} ==> {remote}"}

    def sftp_download(self, remote, local):
        sf = paramiko.Transport((self._host, self._port))
        sf.connect(username=self._username, password=self._password)
        sftp = paramiko.SFTPClient.from_transport(sf)
        self.download(sftp, remote, local)
        return {"st": True, "rt": f"{remote} ==> {local}"}

    def download(self, sftp, remote, local):
        # 检查远程文件是否存在
        try:
            result = sftp.stat(remote)
        except IOError as err:
            error = '[ERROR %s] %s: %s' % (err.errno, os.path.basename(os.path.normpath(remote)), err.strerror)
            return {"st": False, "rt": error}
        else:
            # 判断远程文件是否为目录
            if isdir(result.st_mode):
                dirname = os.path.basename(os.path.normpath(remote))
                local = os.path.join(local, dirname)
                _check_local(local)
                for file in sftp.listdir(remote):
                    sub_remote = os.path.join(remote, file)
                    sub_remote = sub_remote.replace('\\', '/')
                    self.download(sftp, sub_remote, local)
            else:
                # 拷贝文件
                if os.path.isdir(local):
                    local = os.path.join(local, os.path.basename(remote))
                try:
                    sftp.get(remote, local)
                except IOError as err:
                    return {"st": False, "rt": err}

    def exec_cmd_and_print(self, command):
        result = ''
        if self.SSHConnection:
            stdin, stdout, stderr = self.SSHConnection.exec_command(command, get_pty=True, bufsize=1)
            while not stdout.channel.exit_status_ready():
                # print(f"{command} in progress....")
                time.sleep(1)
                result = stdout.readline()
                print(result)
                if stdout.channel.exit_status_ready():
                    # a = stdout.readlines()
                    # print(a)
                    print(f"{command} finished....")
                    break
            if len(stderr) > 0:
                err = stderr.decode() if isinstance(stderr, bytes) else stderr
                return {"st": False, "rt": err}
            data = stdout.read()
            if len(data) >= 0:
                data = data.decode() if isinstance(data, bytes) else data
                return {"st": True, "rt": data}
            return {"st": True, "rt": result}


class ConfFile(object):
    def __init__(self, file):
        self.yaml_file = file
        self.logger = get_logger()
        self.config = self.read_yaml()

    def read_yaml(self):
        """读YAML文件"""
        try:
            with open(self.yaml_file, 'r', encoding='utf-8') as f:
                yaml_dict = yaml.safe_load(f)
                self.logger.write_to_log(None, "DATA", 'INPUT', 'yaml_file', self.yaml_file, yaml_dict)
            return yaml_dict
        except FileNotFoundError:
            prt_log(None, f"Please check the file name: {self.yaml_file}", 2)
        except TypeError:
            prt_log(None, "Error in the type of file name.", 2)

    @deco_yaml_dict
    def get_vplx_configs(self):
        for vplx_config in self.config["versaplx"]:
            if not check_ip(vplx_config['public_ip']):
                prt_log(None, f"Please check the config of {vplx_config['public_ip']}", 2)
        return self.config["versaplx"]

    @deco_yaml_dict
    def get_test_mode(self):
        test_mode_list = ["quorum", "iscsi", "drbd_in_used"]
        if self.config["test_mode"] not in test_mode_list:
            prt_log(None, f"Please check whether the config of test_mode in {test_mode_list}", 2)
        return self.config["test_mode"]

    @deco_yaml_dict
    def get_use_case(self):
        return self.config["use_case"]

    @deco_yaml_dict
    def get_test_times(self):
        if not isinstance(self.config["test_times"], int):
            prt_log(None, "Please enter test_times of int type", 2)
        return self.config["test_times"]

    @deco_yaml_dict
    def get_resource_size(self):
        return self.config["resource_size"]

    @deco_yaml_dict
    def get_resource(self):
        return self.config["resource"]

    @deco_yaml_dict
    def get_target(self):
        return self.config["target"]

    @deco_yaml_dict
    def get_log_path(self):
        return self.config["log_path"]

    @deco_yaml_dict
    def get_device(self):
        return self.config["device"]

    @deco_yaml_dict
    def get_P_interface_info(self):
        scenario_config = self.config["down_up_nic_scenario"]
        down_interface_host = scenario_config["down_up_interface_host"]
        hostname = down_interface_host["hostname"]
        port = down_interface_host["port"]
        ip = down_interface_host["public_ip"]
        password = down_interface_host["password"]
        interf = down_interface_host["interface"]
        return hostname,port,ip,password,interf

