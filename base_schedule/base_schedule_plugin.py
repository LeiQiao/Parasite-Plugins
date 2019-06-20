from pa.plugin import Plugin
import pa
import sys
from plugins.base import BasePlugin
from .guardian import ScheduleGuardian


class SchedulePlugin(Plugin):
    __pluginname__ = 'base_schedule'

    def __init__(self, plugin_name=None, manifest=None):
        super(SchedulePlugin, self).__init__(plugin_name, manifest)

        self.guardian = ScheduleGuardian()
        self.guardian.start()

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
        self.guardian.regist_schedule_job(schedule_id, schedule_class, schedule_time)

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
