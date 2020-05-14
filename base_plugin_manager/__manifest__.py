# noinspection PyStatementEffect
{
    'name': 'base_plugin_manager',
    'summary': '',
    'description': '插件管理 API，允许内网动态安装/卸载插件',

    'author': '',
    'website': '',
    'source': {'git': 'https://github.com/LeiQiao/Parasite-Plugins.git', 'branch': 'master'},

    'category': '',
    'version': '0.1',

    'api': {
        '/plugin_manager': {
            'GET': 'plugin_manager_api.query_plugin',
            'POST': 'plugin_manager_api.install_plugin',
            'DELETE': 'plugin_manager_api.uninstall_plugin',
        }
    },

    # any plugin necessary for this one to work correctly
    'depends': ['base', 'base_api_wrapper']
}
