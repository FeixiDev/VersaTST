from enum import Flag
from tabnanny import check
from charset_normalizer import logging
import yaml
from os import path
import time
import signal
from threading import Thread
import kraken.cerberus.setup as cerberus
import kraken.kubernetes.client as kubecli
import kraken.invoke.command as runcommand
import kraken.pvc.pvc_scenario as pvc_scenario
import sshv.utils as utils
import sshv.log as log
import sshv.control as control
from linstorclient import client as linstorcli



STOP_FLAG = None
PVC_ID = 0


class PVCNumError(Exception):
    pass

class TimeoutExpired(Exception):
    pass

def alarm_handler(signum, frame):
    raise TimeoutExpired

def input_with_timeout(prompt, timeout):
    signal.signal(signal.SIGALRM, alarm_handler)
    signal.alarm(timeout) # produce SIGALRM in `timeout` seconds
    try:
        return input(prompt)
    except TimeoutExpired:
        pass
    finally:
        signal.alarm(0)


def run(scenarios_list, config):
    global STOP_FLAG
    global PVC
    # 检查 namespace 中是否为空
    

    # read pvc config
    conf = scenarios_list[0][0]
    with open(conf, "r") as f:
        spof_pvc_conf = yaml.full_load(f)
    pvc = spof_pvc_conf['pvc']
    times = spof_pvc_conf['times']
    kind = spof_pvc_conf['kind']
    f = open(f'./kraken{pvc}')
    pvc = yaml.safe_load(f)
    f.close()


    while times:
        STOP_FLAG = None
        PVC = 0
        # 创建
        # Thread(target=pvc_create,args=(pvc,"pvctest",1)).start()

        # 手动故障设置
        # user_input = input_with_timeout("Enter y/yes to stop PVC creation: ",2)
        # if user_input == 'y' or user_input == 'yes':
        # STOP_FLAG = True

        # 故障
        failure(kind)

        # 故障恢复
        recover()

        # 检查及处理
        if not check_pvc_status("pvctest"):
            pass
        
        if not check_drbd_status("pvctest"):
            pass
            

        # 清空 pvc
        delete_all_pvc("pvctest")

        # 后置检查及处理
        
        
        print(times)
        times -= 1
        print("剩余次数：",times)
        print("FLAG:",STOP_FLAG)
        print("PVCID:",PVC)







    # 清除配置
    # delete
    # delete_all_pvc("pvctest")

    # pvc_create(pvc, "kraken", 1) # 10个之后可以设置为到配置文件，或者修改为时间，持续时间内进行创建


    # num = pvc_create(pvc,"pvctest",3)
    # print("Number of PVCs created: ",num)

    # 等待一段时间，或者设置为一定时间内进行持续的状态检查

    # 一定时间内循环监听，有触发人工输入，则停止PVC创建


    # check
    # check_pvc_status('kraken',10)

    
    # kubecli.create_namespace("nstest2")
    # kubecli.delete_namespace("nstest2")
    

    # 清楚后的环境检查
    # 

def pvc_create(pvc,namesapce,timeout=3):
    time_end = time.time() + timeout
    global PVC_ID
    while time.time() <= time_end:
        if STOP_FLAG:
            logging.info("interrupt pvc creation")
            break
        PVC_ID += 1
        pvc['metadata']['name'] = f'pvc-test{PVC_ID}'
        kubecli.create_pvc_(pvc,namesapce)
    return PVC_ID



def check_pvc_status(namesapce, timeout=5 * 60):
    time.sleep(10)
    time_end = time.time() + timeout
    while time.time() <= time_end:
        bound_num = 0
        pvc = kubecli.get_all_pvc_status(namespace=namesapce)
        # if len(pvc) != num:
        #     raise PVCNumError
        for k,v in pvc.items():
            if v == 'Bound':
                bound_num += 1
            else:
                print(f'The status of "{k}" is not updated to "Bound"')
                break

        if len(pvc) == bound_num:
            return True
        time.sleep(3)

    logging.info("check pvc status timeout")
    return False

def check_drbd_status(namespace,timeout= 60):
    time_end = time.time() + timeout
    pvcs = kubecli.list_pv(namespace=namespace)
    replicas = 3
    success_flag = ['UpToDate','Diskless']

    # time.sleep(10)
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

    logging.info("check drbd status timeout")
    return False
    

def delete_all_pvc(namespace):
    kubecli.delete_all_pvc(namespace)


def pvc_delete(namesapce,num):
	for i in range(0,num):
		name = f'pvc-test{i}'
		kubecli.delete_pvc_(name,namesapce)


def failure(kind):
    time.sleep(1)
    global STOP_FLAG
    STOP_FLAG = True
    if kind == 'down_inferface':
        pass

def recover():
    # 故障恢复
    pass
    
    


def check_env(pvc,namespace,timeout=5 * 60):
    global PVC_ID
    PVC_ID += 1
    pvc['metadata']['name'] = f'pvc-test{PVC_ID}'
    kubecli.create_pvc_(pvc,"pvctest")
    if check_pvc_status("pvctest") and check_drbd_status("pvctest"):
        kubecli.delete_pvc_(pvc['metadata']['name'],namespace)
    
    # 检查删除情况



def collect_log(namespace):
    # 收集状态不是Bound的 pvc 的相关信息
    pvc = kubecli.get_all_pvc_status(namespace=namesapce)
    for k,v in pvc.items():
        if v != 'Bound':
            # 收集信息
            # crm_report、kubectl describe PVC和dmesg信息
            cmd = f'kubectl decribe pvc {k} -n {namespace}'

    

            
