# noinspection PyStatementEffect
{
    'name': 'base_config_manager',
    'summary': '',
    'description': '配置管理模块，提供接口级的配置管理功能',
    'author': '',
    'website': '',
    'source': {'git': 'git@git.chinapnr.com:parasite/Parasite-Plugins.git', 'branch': 'master'},

    'category': 'tools',
    'version': '0.1',

    'api': {
        '/plugin_config': {
            'GET': 'config_manager_api.get_plugin_config',
            'PUT': 'config_manager_api.put_plugin_config'
        }
    },

    # any plugin necessary for this one to work correctly
    'depends': ['base', 'base_api_wrapper']
}
