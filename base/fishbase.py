import pathlib, sys
from collections import OrderedDict
import logging
from logging import FileHandler
import codecs
import time
import os

if sys.version > '3':
    import configparser
else:
    import ConfigParser as configparser



class MyConfigParser(configparser.ConfigParser):
    """
    自定义 MyConfigParser，重写 optionxform 方法，以便读取大小写敏感的配置文件
    """

    def __init__(self, defaults=None):
        configparser.ConfigParser.__init__(self, defaults=None)

    def optionxform(self, optionstr):
        return optionstr



def conf_as_dict(conf_filename, encoding=None, case_sensitive=False):
    """
    读入 ini 配置文件，返回根据配置文件内容生成的字典类型变量；
    :param:
        * conf_filename: (string) 需要读入的 ini 配置文件长文件名
        * encoding: (string) 文件编码
        * case_sensitive: (bool) 是否大小写敏感，默认为 False
    :return:
        * flag: (bool) 读取配置文件是否正确，正确返回 True，错误返回 False
        * d: (dict) 如果读取配置文件正确返回的包含配置文件内容的字典，字典内容顺序与配置文件顺序保持一致
        * count: (int) 读取到的配置文件有多少个 key 的数量
    举例如下::
        print('--- conf_as_dict demo---')
        # 定义配置文件名
        conf_filename = 'test_conf.ini'
        # 读取配置文件
        ds = conf_as_dict(conf_filename)
        ds1 = conf_as_dict(conf_filename, case_sensitive=True)
        # 显示是否成功，所有 dict 的内容，dict 的 key 数量
        print('flag:', ds[0])
        print('dict:', ds[1])
        print('length:', ds[2])
        d = ds[1]
        d1 = ds1[1]
        # 显示一个 section 下的所有内容
        print('section show_opt:', d['show_opt'])
        # 显示一个 section 下的所有内容，大小写敏感
        print('section show_opt:', d1['show_opt'])
        # 显示一个 section 下面的 key 的 value 内容
        print('section show_opt, key short_opt:', d['show_opt']['short_opt'])
        # 读取一个复杂的section，先读出 key 中的 count 内容，再遍历每个 key 的 value
        i = int(d['get_extra_rules']['erule_count'])
        print('section get_extra_rules, key erule_count:', i)
        for j in range(i):
            print('section get_extra_rules, key erule_type:', d['get_extra_rules']['erule_'+str(j)])
        print('---')
    执行结果::
        --- conf_as_dict demo---
        flag: True
        dict: (omit)
        length: 7
        section show_opt: {'short_opt': 'b:d:v:p:f:', 'long_opt': 'region=,prov=,mer_id=,mer_short_name=,web_status='}
        section show_opt: {'Short_Opt': 'b:d:v:p:f:', 'Long_Opt': 'region=,prov=,mer_id=,mer_short_name=,web_status='}
        section show_opt, key short_opt: b:d:v:p:f:
        section get_extra_rules, key erule_count: 2
        section get_extra_rules, key erule_type: extra_rule_1
        section get_extra_rules, key erule_type: extra_rule_2
        ---
    """
    flag = False

    # 检查文件是否存在
    if not pathlib.Path(conf_filename).is_file():
        return flag,

    # 判断是否对大小写敏感
    cf = configparser.ConfigParser() if not case_sensitive else MyConfigParser()

    # 读入 config 文件
    try:
        if sys.version > '3':
            cf.read(conf_filename, encoding=encoding)
        else:
            cf.read(conf_filename)
    except:
        flag = False
        return flag,

    d = OrderedDict(cf._sections)
    for k in d:
        d[k] = OrderedDict(cf._defaults, **d[k])
        d[k].pop('__name__', None)

    flag = True

    # 计算有多少 key
    count = len(d.keys())

    return flag, d, count



def check_sub_path_create(sub_path):
    """
    检查当前路径下的某个子路径是否存在, 不存在则创建；
    :param:
        * sub_path: (string) 下一级的某路径名称
    :return:
        * 返回类型 (tuple)，有两个值
        * True: 路径存在，False: 不需要创建
        * False: 路径不存在，True: 创建成功
    举例如下::

        print('--- check_sub_path_create demo ---')
        # 定义子路径名称
        sub_path = 'demo_sub_dir'
        # 检查当前路径下的一个子路径是否存在，不存在则创建
        print('check sub path:', sub_path)
        result = check_sub_path_create(sub_path)
        print(result)
        print('---')
    输出结果::

        --- check_sub_path_create demo ---
        check sub path: demo_sub_dir
        (True, False)
        ---

    """

    # 获得当前路径
    temp_path = pathlib.Path()
    cur_path = temp_path.resolve()

    # 生成 带有 sub_path_name 的路径
    path = cur_path / pathlib.Path(sub_path)

    # 判断是否存在带有 sub_path 路径
    if path.exists():
        # 返回 True: 路径存在, False: 不需要创建
        return True, False
    else:
        path.mkdir(parents=True)
        # 返回 False: 路径不存在  True: 路径已经创建
        return False, True



logger = logging.getLogger()



class SafeFileHandler(FileHandler):

    def __init__(self, filename, mode='a', encoding=None, delay=0,
                 file_name_format='%project_name-%log-%date'):
        """
        Use the specified filename for streamed logging
        """
        if codecs is None:
            encoding = None
        FileHandler.__init__(self, filename, mode, encoding, delay)

        # 日志文件路径
        self.file_path = os.path.split(filename)[0]
        # 日志文件名称
        file_name = os.path.split(filename)[1]

        temp_file_name = file_name.split('.')
        if len(temp_file_name) == 1:
            self.project_name = temp_file_name[0]
            self.log_suffix = 'log'
        else:
            self.project_name, self.log_suffix = temp_file_name[0], temp_file_name[1]

        self.mode = mode
        self.encoding = encoding
        self.suffix = "%Y-%m-%d"
        self.suffix_time = ""
        self.file_name_format = file_name_format

    def emit(self, record):
        """
        Emit a record.
        Always check time
        """
        try:
            if self.check_base_filename(record):
                self.build_base_filename()
            FileHandler.emit(self, record)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

    def check_base_filename(self, record):
        """
        Determine if builder should occur.
        record is not used, as we are just comparing times,
        but it is needed so the method signatures are the same
        """
        time_tuple = time.localtime()

        if self.file_name_format:
            pass

        if self.suffix_time != time.strftime(self.suffix, time_tuple) or not os.path.exists(
                self._get_format_filename()):
            return 1
        else:
            return 0

    def build_base_filename(self):
        """
        do builder; in this case,
        old time stamp is removed from filename and
        a new time stamp is append to the filename
        """
        if self.stream:
            self.stream.close()
            self.stream = None

        # remove old suffix
        # if self.suffix_time != "":
        #     index = self.baseFilename.find("." + self.suffix_time)
        #     if index == -1:
        #         index = self.baseFilename.rfind(".")
        #     self.baseFilename = self.baseFilename[:index]

        # add new suffix
        current_time_tuple = time.localtime()
        self.suffix_time = time.strftime(self.suffix, current_time_tuple)
        self.baseFilename = self._get_format_filename()

        self.mode = 'a'
        if not self.delay:
            self.stream = self._open()

    def _get_format_filename(self):
        split_list = self.file_name_format.split('-')
        name_mapping = {'%log': self.log_suffix,
                        '%project_name': self.project_name,
                        '%date': self.suffix_time}
        new_file_name = '.'.join([name_mapping.get(i) for i in split_list])
        return os.path.join(self.file_path, new_file_name)



def set_log_file(local_file=None, file_name_format='%project_name-%log-%date'):
    """
    设置日志记录，按照每天一个文件，记录包括 info 以及以上级别的内容；
    日志格式采取日志文件名直接加上日期，比如 fish_test.log.2018-05-27
    :param:
        * local_fie: (string) 日志文件名
        * file_name_format: (string) 日志文件名格式
    :return: 无
    举例如下::
        from fishbase.fish_logger import *
        from fishbase.fish_file import *
        log_abs_filename = get_abs_filename_with_sub_path('log', 'fish_test.log')[1]
        set_log_file(log_abs_filename)
        logger.info('test fish base log')
        logger.warn('test fish base log')
        logger.error('test fish base log')
        print('log ok')
    """

    default_log_file = 'default.log'

    _formatter = logging.Formatter(
        '%(asctime)s %(levelname)s %(filename)s[ln:%(lineno)d] %(message)s')

    if local_file is not None:
        default_log_file = local_file

    support_split = ['%project_name', '%log', '%date']

    file_format_split = file_name_format.split('-')
    if set(file_format_split) != set(support_split):
        raise ValueError('file_name_format error, please check and try again!')

    # time rotating file handler
    # _tfh = TimedRotatingFileHandler(default_log_file, when="midnight")
    _tfh = SafeFileHandler(filename=default_log_file, file_name_format=file_name_format)
    _tfh.setLevel(logging.INFO)
    _tfh.setFormatter(_formatter)

    logger.setLevel(logging.INFO)

    logger.addHandler(_tfh)
