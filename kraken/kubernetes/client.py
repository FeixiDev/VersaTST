from kubernetes import client, config
from kubernetes.stream import stream
from kubernetes.client.rest import ApiException
import logging
import kraken.invoke.command as runcommand
import sys
import re
import yaml
from os import path
import time
import sshv.utils as utils

kraken_node_name = ""


# Load kubeconfig and initialize kubernetes python client
def initialize_clients(kubeconfig_path):
    global cli
    global cli_dep
    print("initialize_clients")
    try:
        config.load_kube_config(kubeconfig_path)
        cli = client.CoreV1Api()
        cli_dep= client.AppsV1Api()
        print("结束 initialize_clients")
    except ApiException as e:
        utils.prt_log('', "Failed to initialize kubernetes client: %s\n" % e,0)
        sys.exit(1)


def create_namespace(namespace):
    body = {"kind":"Namespace","metadata":{"name":namespace}}
    try:
        cli.create_namespace(body)
    except Exception as e :
        logging.error("Namespace creation failed %s" % e)
        sys.exit(1)


def delete_namespace(namespace):
    try:
        cli.delete_namespace(namespace)
        while cli.read_namespace_status(namespace):
            time.sleep(1)
    except ApiException:
        logging.info(f"Namespace:{namespace} alreay deleted")


def list_pvc(label_selector=None,namespace=None):
    pvc_list = []
    try:
        if label_selector:
            ret = cli.list_persistent_volume_claim_for_all_namespaces(pretty=True, label_selector=label_selector)
        else:
            ret = cli.list_persistent_volume_claim_for_all_namespaces(pretty=True)
    except ApiException as e:
        logging.error("Exception when calling CoreV1Api->list_persistent_volume_claim_for_all_namespaces: %s\n" % e)
    for pvc in ret.items:
        if pvc.metadata.namespace == namespace:
            pvc_list.append(pvc.metadata.name)
    return pvc_list

def list_pv(label_selector=None,namespace=None):
    pv_list = []
    try:
        if label_selector:
            ret = cli.list_persistent_volume_claim_for_all_namespaces(pretty=True, label_selector=label_selector)
        else:
            ret = cli.list_persistent_volume_claim_for_all_namespaces(pretty=True)
    except ApiException as e:
        logging.error("Exception when calling CoreV1Api->list_persistent_volume_claim_for_all_namespaces: %s\n" % e)
    for pvc in ret.items:
        if pvc.metadata.namespace == namespace:
            pv_list.append(pvc.spec.volume_name)
    return pv_list

def get_pvc(pv):
    try:
        ret = cli.list_persistent_volume_claim_for_all_namespaces(pretty=True)
    except ApiException as e:
        logging.error("Exception when calling CoreV1Api->list_persistent_volume_claim_for_all_namespaces: %s\n" % e)
    for pvc in ret.items:
        if pvc.spec.volume_name == pv:
            return pvc.metadata.name

def get_pvc_status(name, namespace):
    pvc_status = {}
    try:
        ret = cli.read_namespaced_persistent_volume_claim_status(name,namespace)
    except ApiException as e:
        logging.error("Exception when calling CoreV1Api->read_namespaced_persistent_volume_claim_status: %s\n" % e)
    return ret.status.phase

def get_all_pvc_status(namespace):
    status = {}
    try:
        ret = cli.list_persistent_volume_claim_for_all_namespaces(pretty=True)
    except ApiException as e:
        logging.error("Exception when calling CoreV1Api->list_persistent_volume_claim_for_all_namespaces: %s\n" % e)

    for pvc in ret.items:
        if pvc.metadata.namespace == namespace:
            status.update({pvc.metadata.name:pvc.status.phase})
    return status
    
    

def get_storageclass():
    cli.get_st



def create_pvc(pvcfile):
    with open(path.join(path.dirname(__file__), pvcfile)) as f:
        pvc = yaml.safe_load(f)
        resp = cli.create_namespaced_persistent_volume_claim(body=pvc,namespace="default")
        utils.prt_log('', "Pvc created. name='%s'" % resp.metadata.name,0)

        return "pvc-"+resp.metadata.uid

def create_pvc_(body,namespace):
    try:
        resp = cli.create_namespaced_persistent_volume_claim(body=body,namespace=namespace)
        # logging.info("PVC created. name='%s'" % resp.metadata.name)
        return "pvc-"+resp.metadata.uid
    except Exception as e:
        logging.error("PVC creation failed %s" % e)
        sys.exit(1)


def create_dep(depfile):    
    with open(path.join(path.dirname(__file__), depfile)) as f:
        dep = yaml.safe_load(f)
        resp = cli_dep.create_namespaced_deployment(body=dep,namespace="default")
        utils.prt_log('', "Deployment created. status='%s'" % resp.metadata.name,0)


def delete_pvc(pvcfile):
    #with open(pvcfile, "r") as f:
    with open(path.join(path.dirname(__file__), pvcfile)) as f:
        config_yaml = yaml.full_load(f)
        scenario_config = config_yaml["metadata"]
        pvc_name = scenario_config.get("name", "")
        resp = cli.delete_namespaced_persistent_volume_claim(name=pvc_name,namespace="default")
        utils.prt_log('', "Pvc delete",0)

def delete_pvc_(name,namespace):
    try:
        cli.delete_namespaced_persistent_volume_claim(name, namespace)
        while cli.read_namespaced_persistent_volume_claim(name, namespace):
            time.sleep(1)
    except ApiException:
        logging.info(f"PVC:{name} alreay deleted")

def delete_all_pvc(namespace):
    try:
        cli.delete_collection_namespaced_persistent_volume_claim(namespace)
    except ApiException as e:
        logging.info(f"PVC alreay deleted")


def delete_dep(depfile):
    #with open(pvcfile, "r") as f:
    with open(path.join(path.dirname(__file__), depfile)) as f:
        config_yaml = yaml.full_load(f) 
        scenario_config = config_yaml["metadata"]
        dep_name = scenario_config.get("name", "")
        resp = cli_dep.delete_namespaced_deployment(name=dep_name,namespace="default")
        utils.prt_log('', "Deployment delete",0)

def delete_pod(name, namespace):
    try:
        cli.delete_namespaced_pod(name=name, namespace=namespace)
        while cli.read_namespaced_pod(name=name, namespace=namespace):
            time.sleep(1)
    except ApiException:
        utils.prt_log('', "Pod already deleted",0)


def create_pod(body, namespace, timeout=180):
    try:
        pod_stat = None
        pod_stat = cli.create_namespaced_pod(body=body, namespace=namespace)
        end_time = time.time() + timeout
        while True:
            pod_stat = cli.read_namespaced_pod(name=body["metadata"]["name"], namespace=namespace)
            if pod_stat.status.phase == "Running":
                utils.prt_log('', "Successfully create pod",0)
                break
            if time.time() > end_time:
                raise Exception("Starting pod failed")
            time.sleep(1)
    except Exception as e:
        utils.prt_log('', "Pod creation failed %s" % e,0)
        if pod_stat:
            utils.prt_log('', pod_stat.status.container_statuses,0)
        delete_pod(body["metadata"]["name"], namespace)
        sys.exit(1)

def create_pod_spof(body, namespace, pvcfile, timeout=120):
    try:
        pod_stat = None
        pod_stat = cli.create_namespaced_pod(body=body, namespace=namespace)
        end_time = time.time() + timeout
        while True:
            pod_stat = cli.read_namespaced_pod(name=body["metadata"]["name"], namespace=namespace)
            if pod_stat.status.phase == "Running":
                utils.prt_log('', "Successfully create pod",0)
                break
            if time.time() > end_time:
                raise Exception("Starting pod failed")
            time.sleep(1)
    except Exception as e:
        utils.prt_log('', "Pod creation failed %s" % e,0)
        if pod_stat:
            utils.prt_log('', pod_stat.status.container_statuses,0)
        delete_pod(body["metadata"]["name"], namespace)
        delete_pvc(pvcfile)
        sys.exit(1)


# List all namespaces
def list_namespaces(label_selector=None):
    namespaces = []
    try:
        if label_selector:
            ret = cli.list_namespace(pretty=True, label_selector=label_selector)
        else:
            ret = cli.list_namespace(pretty=True)
    except ApiException as e:
        logging.error("Exception when calling CoreV1Api->list_namespaced_pod: %s\n" % e)
    for namespace in ret.items:
        namespaces.append(namespace.metadata.name)
    return namespaces


# Get namespace status
def get_namespace_status(namespace_name):
    ret = ""
    try:
        ret = cli.read_namespace_status(namespace_name)
    except ApiException as e:
        logging.error("Exception when calling CoreV1Api->read_namespace_status: %s\n" % e)
    return ret.status.phase


# Check if all the watch_namespaces are valid
def check_namespaces(namespaces, label_selectors=None):
    try:
        valid_namespaces = list_namespaces(label_selectors)
        regex_namespaces = set(namespaces) - set(valid_namespaces)
        final_namespaces = set(namespaces) - set(regex_namespaces)
        valid_regex = set()
        if regex_namespaces:
            for namespace in valid_namespaces:
                for regex_namespace in regex_namespaces:
                    if re.search(regex_namespace, namespace):
                        final_namespaces.add(namespace)
                        valid_regex.add(regex_namespace)
                        break
        invalid_namespaces = regex_namespaces - valid_regex
        if invalid_namespaces:
            raise Exception("There exists no namespaces matching: %s" % (invalid_namespaces))
        return list(final_namespaces)
    except Exception as e:
        logging.info("%s" % (e))
        sys.exit(1)


# List nodes in the cluster
def list_nodes(label_selector=None):
    nodes = []
    try:
        if label_selector:
            ret = cli.list_node(pretty=True, label_selector=label_selector)
        else:
            ret = cli.list_node(pretty=True)
    except ApiException as e:
        logging.error("Exception when calling CoreV1Api->list_node: %s\n" % e)
    for node in ret.items:
        nodes.append(node.metadata.name)
    return nodes


# List nodes in the cluster that can be killed
def list_killable_nodes(label_selector=None):
    nodes = []
    try:
        if label_selector:
            ret = cli.list_node(pretty=True, label_selector=label_selector)
        else:
            ret = cli.list_node(pretty=True)
    except ApiException as e:
        logging.error("Exception when calling CoreV1Api->list_node: %s\n" % e)
    for node in ret.items:
        if kraken_node_name != node.metadata.name:
            for cond in node.status.conditions:
                if str(cond.type) == "Ready" and str(cond.status) == "True":
                    nodes.append(node.metadata.name)
    return nodes


# List pods in the given namespace
def list_pods(namespace, label_selector=None):
    pods = []
    try:
        if label_selector:
            ret = cli.list_namespaced_pod(namespace, pretty=True, label_selector=label_selector)
        else:
            ret = cli.list_namespaced_pod(namespace, pretty=True)
    except ApiException as e:
        logging.error(
            "Exception when calling \
                       CoreV1Api->list_namespaced_pod: %s\n"
            % e
        )
    for pod in ret.items:
        pods.append(pod.metadata.name)
    return pods


def get_all_pods(label_selector=None):
    pods = []
    if label_selector:
        ret = cli.list_pod_for_all_namespaces(pretty=True, label_selector=label_selector)
    else:
        ret = cli.list_pod_for_all_namespaces(pretty=True)
    for pod in ret.items:
        pods.append([pod.metadata.name, pod.metadata.namespace])
    return pods

def check_all_pods():
    err = False
    ret = cli.list_pod_for_all_namespaces(pretty=True)
    for pod in ret.items:
        if(pod.status.phase == "Pending" or pod.status.phase == "Failed"):
            err = True
    return err

# Execute command in pod
def exec_cmd_in_pod(command, pod_name, namespace, container=None):

    exec_command = ["bash", "-c", command]
    try:
        if container:
            ret = stream(
                cli.connect_get_namespaced_pod_exec,
                pod_name,
                namespace,
                container=container,
                command=exec_command,
                stderr=True,
                stdin=False,
                stdout=True,
                tty=False,
            )
        else:
            ret = stream(
                cli.connect_get_namespaced_pod_exec,
                pod_name,
                namespace,
                command=exec_command,
                stderr=True,
                stdin=False,
                stdout=True,
                tty=False,
            )
    except Exception:
        return False
    return ret


def get_containers_in_pod(pod_name, namespace):
    pod_info = cli.read_namespaced_pod(pod_name, namespace)
    container_names = []

    for cont in pod_info.spec.containers:
        container_names.append(cont.name)
    return container_names


# Obtain node status
def get_node_status(node):
    try:
        node_info = cli.read_node_status(node, pretty=True)
    except ApiException as e:
        logging.error(
            "Exception when calling \
                       CoreV1Api->read_node_status: %s\n"
            % e
        )
    for condition in node_info.status.conditions:
        if condition.type == "Ready":
            return condition.status


# Monitor the status of the cluster nodes and set the status to true or false
def monitor_nodes():
    nodes = list_nodes()
    notready_nodes = []
    node_kerneldeadlock_status = "False"
    for node in nodes:
        try:
            node_info = cli.read_node_status(node, pretty=True)
        except ApiException as e:
            logging.error(
                "Exception when calling \
                           CoreV1Api->read_node_status: %s\n"
                % e
            )
        for condition in node_info.status.conditions:
            if condition.type == "KernelDeadlock":
                node_kerneldeadlock_status = condition.status
            elif condition.type == "Ready":
                node_ready_status = condition.status
            else:
                continue
        if node_kerneldeadlock_status != "False" or node_ready_status != "True":  # noqa  # noqa
            notready_nodes.append(node)
    if len(notready_nodes) != 0:
        status = False
    else:
        status = True
    return status, notready_nodes


# Monitor the status of the pods in the specified namespace
# and set the status to true or false
def monitor_namespace(namespace):
    pods = list_pods(namespace)
    notready_pods = []
    for pod in pods:
        try:
            pod_info = cli.read_namespaced_pod_status(pod, namespace, pretty=True)
        except ApiException as e:
            logging.error(
                "Exception when calling \
                           CoreV1Api->read_namespaced_pod_status: %s\n"
                % e
            )
        pod_status = pod_info.status.phase
        if pod_status != "Running" and pod_status != "Completed" and pod_status != "Succeeded":
            notready_pods.append(pod)
    if len(notready_pods) != 0:
        status = False
    else:
        status = True
    return status, notready_pods


# Monitor component namespace
def monitor_component(iteration, component_namespace):
    watch_component_status, failed_component_pods = monitor_namespace(component_namespace)
    logging.info("Iteration %s: %s: %s" % (iteration, component_namespace, watch_component_status))
    return watch_component_status, failed_component_pods


# Find the node kraken is deployed on
# Set global kraken node to not delete
def find_kraken_node():
    pods = get_all_pods()
    kraken_pod_name = None
    for pod in pods:
        if "kraken-deployment" in pod[0]:
            kraken_pod_name = pod[0]
            kraken_project = pod[1]
            break
    # have to switch to proper project

    if kraken_pod_name:
        # get kraken-deployment pod, find node name
        try:
            node_name = runcommand.invoke(
                "kubectl get pods/"
                + str(kraken_pod_name)
                + ' -o jsonpath="{.spec.nodeName}"'
                + " -n"
                + str(kraken_project)
            )

            global kraken_node_name
            kraken_node_name = node_name
        except Exception as e:
            logging.info("%s" % (e))
            sys.exit(1)
