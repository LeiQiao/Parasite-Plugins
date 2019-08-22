# noinspection PyStatementEffect
{
    'name': 'db_config_manager',
    'summary': '数据库配置托管模块，数据库中的配置会覆盖 config 文件中的配置项，可以通过数据库动态修改配置; \n'
               '该模块依赖于 base_db_manager 因此无法设置其相关配置',
    'description': '',
    'author': '',
    'website': '',
    'source': {'git': 'http://172.31.13.131:8088/parasite/Parasite-Plugins.git', 'branch': 'master'},

    'category': 'tools',
    'version': '0.1',

    # any plugin necessary for this one to work correctly
    'depends': ['base', 'base_db_manager']
}
