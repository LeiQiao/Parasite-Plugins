# noinspection PyStatementEffect
{
    'name': 'jarvis_man_client',
    'summary': '',
    'description': 'Jarvis Man 客户端软件',

    'author': '',
    'website': '',
    'source': {'git': 'https://github.com/LeiQiao/Parasite-Plugins.git', 'branch': 'master', 'path': 'jarvis_man_client'},

    'category': 'tools-jarvis',
    'version': '0.1',

    'exports': ['JarvisManClient'],

    # any plugin necessary for this one to work correctly
    'depends': ['base', 'redis_client']
}
