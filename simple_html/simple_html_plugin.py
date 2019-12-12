from pa.plugin import Plugin
from flask import Blueprint, request, send_file
import glob
import os
import sys
import pa
import mimetypes
import io
from .frame import FrameDecorator
from .inherit import InheritRoute


class SimpleHTMLPlugin(Plugin):
    __pluginname__ = 'simple_html'

    @Plugin.before_load
    def regist_html(self):
        if self.manifest is None or 'html' not in self.manifest:
            return

        # 注册接口
        blueprint = Blueprint(
            name='{0}_{1}_blueprint'.format(self.manifest['name'], SimpleHTMLPlugin.__pluginname__),
            import_name=__name__,
            url_prefix=''
        )
        setattr(self, 'blueprint', blueprint)
        spc_files = {}
        setattr(self, 'blueprint_route', spc_files)

        html = self.manifest['html']
        for route, files in html.items():
            if isinstance(files, list):
                for file in files:
                    file_path = os.path.join(os.path.dirname(sys.modules[self.__module__].__file__), file)
                    spc_files.update(SimpleHTMLPlugin.find_all_files(route, file_path))
            elif isinstance(files, str):
                file_path = os.path.join(os.path.dirname(sys.modules[self.__module__].__file__), files)
                spc_files.update(SimpleHTMLPlugin.find_all_files(route, file_path))
            else:
                raise TypeError('{0}: route \'{1}\' has unknown type, either str or list'
                                .format(self.__pluginname__, route))

        for file_route in spc_files.keys():
            pa.log.info('{0}: add static file rule: {1}'.format(self.__pluginname__, file_route))
            blueprint.add_url_rule(file_route, view_func=SimpleHTMLPlugin.static_file_route, methods=['GET'])
        pa.web_app.register_blueprint(blueprint)

    @staticmethod
    def find_all_files(route, file):
        files = glob.glob(file)
        route_files = {}
        for file_path in files:
            if os.path.isdir(file_path):
                sub_route = os.path.join(route, os.path.basename(file_path)) + '/'
                route_files.update(SimpleHTMLPlugin.find_all_files(sub_route, os.path.join(file_path, '*')))
            else:
                if len(files) > 1 or route[-1] == '/':
                    file_route = os.path.join(route, os.path.basename(file_path))
                elif route[-8:] == '/<index>':
                    file_route = route[:-7]
                else:
                    file_route = route
                route_files[file_route] = file_path
        return route_files

    @staticmethod
    def static_file_route():
        for plugin in pa.plugin_manager.all_installed_plugins:
            if not hasattr(plugin, 'blueprint_route'):
                continue
            routes = getattr(plugin, 'blueprint_route')
            file_route = request.url_rule.rule
            if file_route not in routes.keys():
                continue

            file_path = routes[file_route]
            mime_type = mimetypes.guess_type(file_path)[0] or 'application/stream'

            file_pointer = open(file_path, 'rb')
            fp = io.BytesIO(file_pointer.read())
            file_pointer.close()

            fp = FrameDecorator.decorator_route(file_route, fp)
            fp = InheritRoute.inherit_route(file_route, fp)

            return send_file(fp, mimetype=mime_type)
        return None
