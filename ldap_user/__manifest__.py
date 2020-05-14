# noinspection PyStatementEffect
{
    'name': 'ldap_user',
    'summary': '',
    'description': '域账号用户管理，登录及查询用户信息',
    'author': '',
    'website': '',
    'source': {'git': 'https://github.com/LeiQiao/Parasite-Plugins.git', 'branch': 'master'},

    'category': '',
    'version': '0.1',

    'api': {
        '/user/token': 'user_api.gen_token',
        '/user/captcha': 'user_api.gen_captcha',
        '/user/login': {
            'POST': 'user_api.login'
        },
        '/user/search': 'user_api.search_users'
    },

    # any plugin necessary for this one to work correctly
    'depends': ['base', 'base_api_wrapper', 'redis_client', 'i18n']
}
