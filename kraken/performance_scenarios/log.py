# coding:utf-8
import logging
import logging.handlers
import logging.config
import threading
import getpass
import time
from random import shuffle
import sys
from kraken.performance_scenarios import utils 

LOG_PATH = f'{sys.path[0]}/kraken/performance_scenarios/performance_log/'
CLI_LOG_NAME = f'test_{time.strftime("%Y%m%d_%H%M%S", time.localtime())}.log'


def get_username():
    return getpass.getuser()


def create_transaction_id():
    return int(time.time())


def create_oprt_id():
    time_stamp = str(create_transaction_id())
    str_list = list(time_stamp)
    shuffle(str_list)
    return ''.join(str_list)


class MyLoggerAdapter(logging.LoggerAdapter):
    """
    实现一个LoggerAdapter的子类，重写process()方法。
    其中对于kwargs参数的操作应该是先判断其本身是否包含extra关键字，如果包含则不使用默认值进行替换；
    如果kwargs参数中不包含extra关键字则取默认值。
    """
    extra_dict = {
        "user": "USERNAME",
        "tid": "",
        "t1": "TYPE1",
        "t2": "TYPE2",
        "d1": "",
        "d2": "",
        "data": ""}

    def __init__(self, log_path, file_name):
        super().__init__(self.get_my_logger(log_path, file_name), self.extra_dict)

    def process(self, msg, kwargs):
        if 'extra' not in kwargs:
            kwargs["extra"] = self.extra
        return msg, kwargs

    def get_my_logger(self, log_path, file_name):
        handler_input = logging.handlers.RotatingFileHandler(filename=f'{log_path}{file_name}',
                                                             mode='a',
                                                             maxBytes=10 * 1024 * 1024, backupCount=20)
        fmt = logging.Formatter(
            "%(asctime)s [%(times)s] [%(node)s] [%(t1)s] [%(t2)s] [%(d1)s] [%(d2)s] [%(data)s]|",
            datefmt='[%Y/%m/%d %H:%M:%S]')
        handler_input.setFormatter(fmt)
        logger = logging.getLogger('test_logger')
        logger.addHandler(handler_input)
        logger.setLevel(logging.DEBUG)
        self.handler_input = handler_input
        return logger

    def remove_my_handler(self):
        # 可以考虑修改为异常处理
        if self.handler_input:
            self.logger.removeHandler(self.handler_input)


class Log(object):
    _instance_lock = threading.Lock()
    # _instance = None
    # user = None  # 新的进程
    # tid = None
    file_name = CLI_LOG_NAME
    log_path = LOG_PATH
    log_switch = True
    logger = None

    def __init__(self):

        """
        日志格式：
        asctime：时间
        tid：transaction id，事务的唯一标识
        user：username，操作系统的用户
        t1：type1，日志数据的类型一
        t2：type2，日志数据的类型二
        d1：description1，日志数据的描述一
        d2：description2，日志数据的描述二
        data：具体的结果或者数据

        :param user:
        :param tid:
        :param file_name:
        """
        pass

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):
            with Log._instance_lock:
                if not hasattr(cls, '_instance'):
                    Log._instance = super().__new__(cls)
                    Log._instance.logger = MyLoggerAdapter(cls.log_path, cls.file_name)

        return Log._instance

    # write to log file
    def write_to_log(self, conn, t1, t2, d1, d2, data):
        logger = Log._instance.logger

        # 获取到日志开关不为True时，移除处理器，不再将数据记录到文件中
        if not self.log_switch:
            logger.remove_my_handler()

        # if not self.user:
        #     self.user = get_username()
        # if not self.tid:
        #     self.tid = create_transaction_id()
        logger.debug(
            "",
            extra={
                'times': utils.get_times(),
                'node': utils.get_global_dict_value(conn),
                't1': t1,
                't2': t2,
                'd1': d1,
                'd2': d2,
                'data': data})

