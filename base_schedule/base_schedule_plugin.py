from pa.plugin import Plugin
import pa
import sys
from plugins.base import BasePlugin
from multiprocessing import Process
from .schedule import Schedule
from datetime import datetime


class SchedulePlugin(Plugin):
    __pluginname__ = 'base_schedule'

    def __init__(self, plugin_name=None, manifest=None):
        super(SchedulePlugin, self).__init__(plugin_name, manifest)

        self.schedule_jobs = {}

    @Plugin.after_load
    def regist_schedule_from_plugin_manifest(self):
        if self.manifest is None:
            return

        plugin_schedules = self.manifest['schedule'] if 'schedule' in self.manifest else None
        if plugin_schedules is None or len(plugin_schedules) == 0:
            return

        schedule_plugin = pa.plugin_manager.get_plugin(SchedulePlugin.__pluginname__)

        for schedule_class, schedule_time in plugin_schedules.items():
            schedule_id = '{0}.{1}'.format(self.manifest['name'], schedule_class)
            cls = SchedulePlugin._get_class_in_module(self, schedule_class)
            schedule_plugin.regist_schedule_job(schedule_id, cls, schedule_time)

    def regist_schedule_job(self, schedule_id, schedule_class, schedule_time):
        if schedule_id in self.schedule_jobs:
            return

        job_process = Process(target=worker_process,
                              args=(schedule_id, schedule_class, schedule_time))
        job_process.start()
        self.schedule_jobs[schedule_id] = job_process

    @staticmethod
    def _get_class_in_module(plugin, class_name):
        mod = sys.modules[BasePlugin.get_module_name(plugin)]
        cls = mod
        try:
            cls_path = class_name.split('.')
            for fn in cls_path:
                cls = getattr(cls, fn)
        except Exception as e:
            str(e)
            raise ModuleNotFoundError('unable found schedule class \'{0}\''.format(class_name))
        return cls


def worker_process(schedule_id, work_class, schedule_time):
    # 这里需要使用 __name__ 进行比较
    if work_class.__base__.__name__ != Schedule.__name__:
        raise ImportError('schedule class \'{0}\' is not a subclass of \'Schedule\''.format(work_class))

    schedule = work_class()
    schedule.start(schedule_time, schedule_id)
    pa.log.info('start schedule \'{0}\''.format(schedule_id))

    first_run = True
    while True:
        try:
            schedule.run_times += 1
            pa.log.debug('schedule {0} triggered at {1}, {2} times'
                         .format(schedule.schedule_id, datetime.now(), schedule.run_times))
            if first_run:
                first_run = False
                schedule.first_run()
            else:
                schedule.run()
        except Exception as e:
            pa.log.error('schedule {0} error: {1}'.format(schedule.schedule_id, e))

        schedule.sleep()
