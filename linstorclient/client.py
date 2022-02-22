import re
import logging
import sys
import time
import http

try:
    import linstor
except ImportError:
    logging.error("linstor is not installed")
    sys.exit(1)

class LinstorClientError(Exception):
    """
    Linstor exception with a message and exit code information
    """
    def __init__(self, msg, exit_code):
        self._msg = msg
        self._exit_code = exit_code

    @property
    def exit_code(self):
        return self._exit_code

    @property
    def message(self):
        return self._msg

    def __str__(self):
        return "Error: {msg}".format(msg=self._msg)

    def __repr__(self):
        return "LinstorError('{msg}', {ec})".format(msg=self._msg, ec=self._exit_code)

class ExitCode(object):
    OK = 0
    UNKNOWN_ERROR = 1
    ARGPARSE_ERROR = 2
    OBJECT_NOT_FOUND = 3
    OPTION_NOT_SUPPORTED = 4
    ILLEGAL_STATE = 5
    CONNECTION_ERROR = 20
    CONNECTION_TIMEOUT = 21
    UNEXPECTED_REPLY = 22
    API_ERROR = 10
    NO_SATELLITE_CONNECTION = 11


# Load kubeconfig and initialize kubernetes python client
def initialize_clients():
    global cli
    try:
        cli = get_linstor_client()
    except LinstorClientError as e:
        logging.error("Failed to initialize kubernetes client: %s\n" % e)
        sys.exit(1)

def get_replies_state(replies):
    """
    :param list[ApiCallResponse] replies:
    :return:
    :rtype: (str, int)
    """
    errors = 0
    warnings = 0
    for reply in replies:
        if reply.is_error():
            errors += 1
        if reply.is_warning():
            warnings += 1
    if errors:
        return "Error"
    elif warnings:
        return "Warning"

    return "Ok"


def get_linstor_client(**kwargs):
    LINSTOR_CONF = '/etc/linstor/linstor-client.conf'
    KEY_LS_CONTROLLERS = 'LS_CONTROLLERS'
    # TODO also read config overrides
    # servers = ['linstor://localhost']
    # 通过
    with open(LINSTOR_CONF) as f:
        data = f.read()
        contrl_list = re.findall('controllers=(.*)',data)[0]
    servers = linstor.MultiLinstor.controller_uri_list(contrl_list)
    
    if 'parsed_args' in kwargs:
        cliargs = kwargs['parsed_args']
        servers = linstor.MultiLinstor.controller_uri_list(cliargs.controllers)
    if not servers:
        return None

    for server in servers:
        try:
            _linstor_completer = linstor.Linstor(server)
            _linstor_completer.connect()
            break
        except linstor.LinstorNetworkError as le:
            pass

    return _linstor_completer

def get_volume_state(volume_states, volume_nr):
    for volume_state in volume_states:
        if volume_state.number == volume_nr:
            return volume_state
    return None

def get_resource(node=None,storagepool=None,resource=None):
    while True:
        try:
            msg = cli.volume_list(node,storagepool,resource)[0]
            break
        except linstor.errors.LinstorNetworkError:
            logging.error("Failed to connect to linstor, automatic retry later(linstor.errors.LinstorNetworkError)")
            time.sleep(5)
            initialize_clients()
        except http.client.CannotSendRequest:
            logging.error("Failed to connect to linstor, automatic retry later(http.client.CannotSendRequest)")
            time.sleep(5)
            initialize_clients()


    # try:
    #     msg = cli.volume_list(node,storagepool,resource)[0]
    # except linstor.errors.LinstorNetworkError:
    #     logging.error("Failed to connect to linstor, automatic retry later")
    #     time.sleep(10)
    #     msg = cli.volume_list(node,storagepool,resource)[0]
    lst = []
    rsc_state_lkup = {x.node_name + x.name: x for x in msg.resource_states}

    for rsc in msg.resources:
        rsc_state = rsc_state_lkup.get(rsc.node_name + rsc.name)
        # rsc_usage = ""
        # if rsc_state and rsc_state.in_use is not None:
        #     if rsc_state.in_use:
        #         rsc_usage = 'Inused'
        #     else:
        #         rsc_usage = "Unused"

        for vlm in rsc.volumes:
            vlm_state = get_volume_state(
                rsc_state.volume_states,
                vlm.number
            ) if rsc_state else None

            # vlm_drbd_data = vlm.drbd_data
            # mirror_num = str(vlm_drbd_data.drbd_volume_definition.minor) if vlm_drbd_data else ""

            lst.append({'Node':rsc.node_name,
                        'Resource':rsc.name,
                        # 'StoragePool':vlm.storage_pool_name,
                        # 'VolNr':str(vlm.number),
                        # 'MinorNr':mirror_num,
                        # 'DeviceName':vlm.device_path,
                        # 'Allocated':linstor.SizeCalc.approximate_size_string(vlm.allocated_size) if vlm.allocated_size else "",
                        # 'InUse':rsc_usage,
                        'State':vlm_state.disk_state,
                        })

    return lst


