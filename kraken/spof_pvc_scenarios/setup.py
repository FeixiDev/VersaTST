# from asyncio import subprocess
import subprocess
from charset_normalizer import logging
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
    if kubecli.list_pvc(namespace=NAME_SPACE):
        logging.error("There already exists pvc, please clear it and try again")
        return
        

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

    utils._init()
    logger = log.Log()
    utils.set_logger(logger)
    stor_config = utils.ConfFile(conf)
    iscsitest = control.IscsiTest(stor_config)

    while times:
        STOP_FLAG = None
        PVC = 0
        # 创建
        print("开始创建")
        Thread(target=pvc_create,args=(pvc,NAME_SPACE,1)).start()

        # 手动故障设置
        # user_input = input_with_timeout("Enter y/yes to stop PVC creation: ",2)
        # if user_input == 'y' or user_input == 'yes':
        # STOP_FLAG = True

        # 故障
        print("故障设置")
        # failure(kind,iscsitest)

        # 故障恢复
        # recover(kind,iscsitest)


        # 检查及处理
        print("开始检查")
        if not check_pvc_status(NAME_SPACE):
            # collect_pvc_describe(NAME_SPACE)
            # iscsitest.get_log(False)
            print("pvc 不为 bound 收集日志")
                    
        if not check_drbd_status(NAME_SPACE):
            # collect_drbd_log(NAME_SPACE)
            # iscsitest.get_log(False)
            print("drbd 状态有误，收集日志")

        # 检查不通过是否停止
            

        # 清空 pvc
        print("开始清空资源")
        delete_all_pvc(NAME_SPACE)
        time.sleep(60)

        # 删除后的检查 
        print("执行清除操作后的检查")
        if not is_clean(NAME_SPACE):
            # collect_pvc_describe(NAME_SPACE)
            # iscsitest.get_log(False)
            print("没有正常清除")


        # 恢复环境
            

        # 后置检查及处理
        print("环境检查")
        if not check_env(pvc,NAME_SPACE):
            # collect_pvc_describe(NAME_SPACE)
            # iscsitest.get_log(False)
            print("后置检查环境失败，收集日志")

        times -= 1
        print("剩余次数：",times)







def pvc_create(pvc,namesapce,timeout=2):
    time_end = time.time() + timeout
    global PVC_ID
    while time.time() <= time_end:
        if STOP_FLAG:
            logging.info("interrupt pvc creation")
            break
        PVC_ID += 1
        pvc['metadata']['name'] = f'pvc-test{PVC_ID}'
        kubecli.create_pvc_(pvc,namesapce)
        time.sleep(0.5)
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
                logging.info(f'The status of "{pvc}" is not updated to "Bound"')
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

    logging.info("check drbd status timeout")
    return False

    

def delete_all_pvc(namespace):
    kubecli.delete_all_pvc(namespace)


def failure(kind,iscsitest):
    global STOP_FLAG
    STOP_FLAG = True
    if kind == 'down_inferface':
        iscsitest.change_node_interface(False)
    elif kind == 'switch_port_down':
        iscsitest.change_switch_port(False)
        

def recover(kind, iscsitest):
    # 故障恢复
    if kind == 'switch_port_down':
        iscsitest.change_switch_port(True)
    elif kind == 'down_inferface':
        iscsitest.change_node_interface(True)
        
    
    

def is_clean(namespace, timeout= 3*60):
    time_end = time.time() + timeout
    while time.time() <= time_end:
        flag = True
        pvcs = kubecli.list_pv(namespace=namespace)
        if pvcs:
            logging.info("pvc still exists")
            flag = False

        drbds = linstorcli.get_resource()
        for pvc in pvcs:
            for drbd in drbds:
                if drbd["Resource"] == pvc:
                    logging.info("drbd still exists")
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

            
