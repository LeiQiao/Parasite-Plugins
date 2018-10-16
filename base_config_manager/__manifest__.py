# noinspection PyStatementEffect
{
    'name': 'base_config_manager',
    'summary': '',
    'description': '配置管理模块，提供方法级和接口级的配置管理功能，可以使用 \'server\' 来替换配置文件中的服务器设置项',

    'author': '',
    'website': '',
    'source': {'git': '', 'branch': '', 'folder': ''},

    'category': 'base',
    'version': '0.1',

    'api': {
        '/plugin_config': {
            'POST': 'config_manager_api.set_plugin_config',
            'GET': 'config_manager_api.get_plugin_config',
            'PUT': 'config_manager_api.put_plugin_config'
        }
    },

    'exports': ['config_manager_api'],

    # any plugin necessary for this one to work correctly
    'depends': ['base', 'base_api_warpper']
}
