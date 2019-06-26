from base.config_model import ConfigModel
import ldap
import pa


class LDAPUserConfig(ConfigModel):
    __configname__ = 'ldap_user'

    ldap_url = ConfigModel.Column(None)
    ldap_dn = ConfigModel.Column(None)
    ldap_admin_user_name = ConfigModel.Column(None)
    ldap_admin_password = ConfigModel.Column(None)

    unlogin_session_expire = ConfigModel.Column(10 * 60)
    logined_session_expire = ConfigModel.Column(2 * 60 * 60)
    debug_captcha = ConfigModel.Column(None)
