#!/usr/bin/env python3
import subprocess
import re
import sys
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import logging



def run(cmd):
    try:
        output = subprocess.Popen(
            cmd, shell=True, universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        (out, err) = output.communicate()
    except Exception as e:
        logging.error("Failed to run %s, error: %s" % (cmd, e))
    return out


namespace = "kraken"
pods_running = 0

new_pods_running = run("kubectl get pods -n " + namespace + " | grep -c Running").rstrip()
try:
    pods_running += int(new_pods_running)
except Exception:
    pass
print(pods_running)
