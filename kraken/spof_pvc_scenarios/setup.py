import subprocess
import re
from charset_normalizer import logging
from matplotlib import set_loglevel
import yaml
import time
import signal
from threading import Thread
import kraken.kubernetes.client as kubecli
import sshv.utils as utils
import sshv.log as log
import sshv.control as control
from linstorclient import client as linstorcli



STOP_FLAG = None
PVC_ID = 0
NAME_SPACE = "pvctest"

class PVCNumError(Exception):
    pass

class TimeoutExpired(Exception):
    pass

def run(scenarios_list, config):
    global STOP_FLAG
    global PVC_ID

    # 检查 namespace 中是否为空
    if kubecli.list_pvc(namespace=NAME_SPACE):
        logging.error("There already exists pvc, please clear it and try again")
        return
        
    # read pvc config
    conf = scenarios_list[0][0]
    with open(conf, "r") as f:
        spof_pvc_conf = yaml.full_load(f)
    pvc = spof_pvc_conf['pvc']
    times = spof_pvc_conf['times']
    f = open(f'./kraken{pvc}')
    pvc = yaml.safe_load(f)
    f.close()

    utils._init()
    logger = log.Log()
    utils.set_logger(logger)
    stor_config = utils.ConfFile(conf)
    actuator = control.IscsiTest(stor_config)

    fault_setter = FaultSetter(spof_pvc_conf, actuator)

    while times:
        STOP_FLAG = None
        PVC_ID = 0
        create_timeout = 1
        # 创建
        # print("开始创建")
        logging.info("start creating pvc")
        Thread(target=pvc_create,args=(pvc,NAME_SPACE,create_timeout)).start()


        # print("故障设置")
        logging.info("start setting failure")
        # 人工故障设置, kind 设置为 'manual' 时启动
        if fault_setter.manual_setting():
            STOP_FLAG = True
            logging.info("stop the creation of pvc")
            # print("已停止创建")

        # 故障
        STOP_FLAG = True
        fault_setter.setting()

        # 检查及处理
        # print("开始检查")
        logging.info("start checking resource status")
        if not check_pvc_status(NAME_SPACE):
            logging.info("The pvc status is not passed, log collection is performed")
            collect_pvc_describe(NAME_SPACE)
            actuator.get_log(False)
            STOP_CREATE = True
                    
        if not check_drbd_status(NAME_SPACE):
            logging.info("The drbd status is not passed, log collection is performed")
            collect_drbd_log(NAME_SPACE)
            actuator.get_log(False)
            STOP_CREATE = True

        # 检查不通过是否停止
        if STOP_CREATE:
            logging.info("resource status is not passed, exit")
            return


        # 检查资源是否转移
        if spof_pvc_conf['kind'] == 'interface_down':
            if fault_setter.check_running_node():
                logging.info("resources have been moved to other nodes")
                actuator.get_log(False)

        
        # 清空 pvc
        # print("开始清空资源")
        logging.info("start clearing resources")
        delete_all_pvc(NAME_SPACE)

        # 删除后的检查 
        # print("执行清除操作后的检查")
        logging.info("start environment check")
        if not is_clean(NAME_SPACE):
            logging.info("The resource is not cleared normally, log collection is performed")
            collect_pvc_describe(NAME_SPACE)
            actuator.get_log(False)
            return


        # 恢复环境
        logging.info("recovery environment")
        fault_setter.recover()
        time.sleep(10)
        
        # 后置检查及处理
        # print("环境检查")
        logging.info("check if the environment is normal")
        if not check_env(pvc,NAME_SPACE):
            collect_pvc_describe(NAME_SPACE)
            actuator.get_log(False)
            # print("后置检查环境失败，收集日志")
            logging.info("environment does not pass inspection")
            return

        times -= 1
        print("* remaining times:",times)
        
        
        
def pvc_create(pvc,namesapce,timeout=3):
    time_end = time.time() + timeout
    global PVC_ID
    global STOP_FLAG
    while time.time() <= time_end:
        if STOP_FLAG:
            logging.info("interrupt pvc creation")
            break
        PVC_ID += 1
        pvc['metadata']['name'] = f'pvc-test{PVC_ID}'
        kubecli.create_pvc_(pvc,namesapce)
        time.sleep(1.5)
    return PVC_ID

def check_pvc_status(namesapce, timeout=5 * 60):
    time.sleep(10)
    time_end = time.time() + timeout
    while time.time() <= time_end:
        bound_num = 0
        pvcs = kubecli.get_all_pvc_status(namespace=namesapce)
        for pvc,state in pvcs.items():
            if state == 'Bound':
                bound_num += 1
            else:
                break

        if len(pvcs) == bound_num:
            return True
        time.sleep(3)   

    logging.info("check pvc status timeout")
    return False

def check_drbd_status(namespace,timeout= 60):
    time_end = time.time() + timeout
    pvcs = kubecli.list_pv(namespace=namespace)
    replicas = 3
    success_flag = ['UpToDate','Diskless']

    time.sleep(10)
    while time.time() <= time_end:
        success_pvc = 0
        resources = linstorcli.get_resource()
        for pvc in pvcs:
            success_res = 0
            for res in resources:
                if res["Resource"] == pvc and res["State"] in success_flag:
                    success_res += 1
            if success_res == replicas:
                success_pvc += 1

        if len(pvcs) == success_pvc:
            return True
        
        time.sleep(5)

    logging.info("check drbd status timeout")
    return False

def delete_all_pvc(namespace):
    kubecli.delete_all_pvc(namespace)
            
def is_clean(namespace, timeout= 3*60):
    time_end = time.time() + timeout
    while time.time() <= time_end:
        flag = True
        pvcs = kubecli.list_pv(namespace=namespace)
        if pvcs:
            flag = False

        drbds = linstorcli.get_resource()
        for pvc in pvcs:
            for drbd in drbds:
                if drbd["Resource"] == pvc:
                    flag = False
                    break

        if flag == True:
            return flag

        time.sleep(3)

    return flag

def check_env(pvc,namespace):
    global PVC_ID
    PVC_ID += 1
    pvc['metadata']['name'] = f'pvc-test{PVC_ID}'
    kubecli.create_pvc_(pvc,NAME_SPACE)
    if check_pvc_status(NAME_SPACE) and check_drbd_status(NAME_SPACE):
        kubecli.delete_pvc_(pvc['metadata']['name'],namespace)
    
    # 检查删除情况
    if is_clean(namespace):
        return True

def collect_pvc_describe(namespace):
    # 收集状态不是Bound的 pvc 的相关信息
    pvcs = kubecli.get_all_pvc_status(namespace=namespace)
    for pvc,state in pvcs.items():
        if state != 'Bound':
            # 收集信息
            # crm_report、kubectl describe PVC和dmesg信息
            describe = get_pvc_describe(pvc,namespace)
            logging.error(describe)

def collect_drbd_log(namespace):
    pvcs = kubecli.list_pv(namespace=namespace)
    success_flag = ['UpToDate','Diskless']
    resources = linstorcli.get_resource()

    for pvc in pvcs:
        for res in resources:
            if res["Resource"] == pvc and res["State"]  not in success_flag:
                # 收集日志
                describe = get_pvc_describe(pvc,namespace)
                logging.error(describe)

def get_pvc_describe(pvc,namespace):
    pvc_descibe =  subprocess.getoutput(f'kubectl describe pvc {pvc} -n {namespace}')
    return pvc_descibe

            
class FaultSetter():
    def __init__(self,conf, actuator):
        self.node_running_vip = None
        self.node_running_controller = None
        self.kind = conf['kind']
        self.vip = conf['vip']
        self.linstor_controller = conf['linstor_controller']
        self.actuator = actuator


    def _alarm_handler(self, signum, frame):
        raise TimeoutExpired

    def input_with_timeout(self, prompt, timeout):
        signal.signal(signal.SIGALRM, self._alarm_handler)
        signal.alarm(timeout) # produce SIGALRM in `timeout` seconds
        try:
            return input(prompt)
        except TimeoutExpired:
            pass
        finally:
            signal.alarm(0)

    def get_res_running_node(self,res):
        output = subprocess.getoutput(f'crm res show {res}')
        result =  re.findall(rf"resource {res} is running on: (.*)",output)
        if result:
            return result[0]


    def setting(self):
        if self.kind == 'interface_down':
            self.node_running_vip = self.get_res_running_node(self.vip)
            self.node_running_controller = self.get_res_running_node(self.linstor_controller)
            # self.actuator.change_node_interface(False)
        elif self.kind == 'switch_port_down':
            # self.actuator.change_switch_port(False)
            pass

    def manual_setting(self,timeout=2):
        if self.kind == 'manual':
            user_input = self.input_with_timeout("Enter y/yes to stop PVC creation: ",timeout)
            if user_input == 'y' or user_input == 'yes':
                return True
            else:
                time.sleep(timeout)
                


    def recover(self):
        # 故障恢复
        if self.kind == 'switch_port_down':
            # self.actuator.change_switch_port(True)
            pass
        elif self.kind == 'interface_down':
            # self.actuator.change_node_interface(True)
            pass


    def check_running_node(self):
        is_transferred = False
        node_vip_now = self.get_res_running_node(self.vip)
        node_controller_now = self.get_res_running_node(self.linstor_controller)

        if node_vip_now != self.node_running_vip:
            print(node_vip_now)
            print(self.node_running_vip)
            logging.info(f"The vip resource has been transferred: {node_vip_now} ")
            is_transferred = True

        if node_controller_now != self.node_running_controller:
            print(node_controller_now)
            print(self.node_running_controller)
            logging.info(f"The linstor controller has been transferred: {node_vip_now} ")
            is_transferred = True

        return is_transferred
        

        
