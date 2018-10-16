from pa.plugin import Plugin
from flask import Blueprint
import pa
import sys


class APIWarpperPlugin(Plugin):
    def on_load(self):
        super(APIWarpperPlugin, self).on_load()
        internal_ip_list = pa.plugin_config[self.plugin_name]['internal_ip_list'].strip()
        if len(internal_ip_list) == 0:
            internal_ip_list = []
        else:
            internal_ip_list = internal_ip_list.split(',')
        pa.plugin_config[self.plugin_name]['internal_ip_list'] = internal_ip_list

    @Plugin.before_load
    def regist_api(self):
        if self.manifest is not None:
            api = self.manifest['api'] if 'api' in self.manifest else None
            if api is not None and len(api) > 0:
                # 注册接口
                blueprint = Blueprint(
                    name=self.manifest['name'],
                    import_name=__name__,
                    url_prefix=''
                )
                setattr(self, 'blueprint', blueprint)
                for api_name, api_method in api.items():
                    APIWarpperPlugin._regist_api(self, api_name, api_method)
                pa.web_app.register_blueprint(blueprint)

    @staticmethod
    def _regist_api(plugin, api_name, api_method):
        blueprint = getattr(plugin, 'blueprint')
        if isinstance(api_method, str):
            func = APIWarpperPlugin._get_func_in_module(plugin, api_method)
            blueprint.add_url_rule(api_name, view_func=func)
            return

        for method, func_name in api_method.items():
            func = APIWarpperPlugin._get_func_in_module(plugin, func_name)
            blueprint.add_url_rule(api_name, view_func=func, methods=[method])

    @staticmethod
    def _get_func_in_module(plugin, func_name):
        mod = sys.modules['plugins.{0}'.format(plugin.plugin_name)]
        func = mod
        try:
            func_path = func_name.split('.')
            for fn in func_path:
                func = getattr(func, fn)
        except Exception as e:
            pa.web_app.log.error('unable found api function \'{0}\''.format(func_name))
            raise e
        return func
