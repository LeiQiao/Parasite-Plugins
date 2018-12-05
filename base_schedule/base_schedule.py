from pa.plugin import Plugin
import pa
import threading
import sys
from plugins.base import BasePlugin
from .schedule import Schedule
from datetime import datetime


class SchedulePlugin(Plugin):
    __pluginname__ = 'base_schedule'

    def __init__(self, plugin_name=None, manifest=None):
        super(SchedulePlugin, self).__init__(plugin_name, manifest)
        self.jobs = []

    @Plugin.after_load
    def regist_schedule(self):
        if self.manifest is None:
            return

        plugin_schedules = self.manifest['schedule'] if 'schedule' in self.manifest else None
        if plugin_schedules is not None and len(plugin_schedules) > 0:
            for schedule_class, schedule_time in plugin_schedules.items():
                SchedulePlugin._regist_schedule_job(self, schedule_class, schedule_time)

    @staticmethod
    def _regist_schedule_job(plugin, schedule_class, schedule_time):
        schedule_plugin = pa.plugin_manager.get_plugin(SchedulePlugin.__pluginname__)
        cls = SchedulePlugin._get_class_in_module(plugin, schedule_class)
        if cls.__base__ != Schedule:
            raise ImportError('schedule class \'{0}\' is not a subclass of \'Schedule\''.format(schedule_class))

        schedule_id = '{0}.{1}'.format(plugin.manifest['name'], schedule_class)
        schedule = cls()
        schedule.start(schedule_time, schedule_id)
        schedule_plugin.jobs.append(schedule)

        thread = threading.Thread(target=SchedulePlugin.run_schedule,
                                  kwargs={'schedule_id': schedule.schedule_id})
        thread.start()

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

    @staticmethod
    def run_schedule(**kwargs):
        schedule_plugin = pa.plugin_manager.get_plugin(SchedulePlugin.__pluginname__)
        schedule_id = kwargs['schedule_id']
        schedule = None
        for sch in schedule_plugin.jobs:
            if sch.schedule_id == schedule_id:
                schedule = sch
                break

        if schedule is None:
            return

        first_run = True
        while True:
            try:
                pa.log.debug('schedule {0} triggered at {1}'.format(schedule.schedule_id, datetime.now()))
                if first_run:
                    first_run = False
                    schedule.first_run()
                else:
                    schedule.run()
            except Exception as e:
                pa.log.error('schedule {0} error: {1}'.format(schedule.schedule_id, e))

            schedule.sleep()
