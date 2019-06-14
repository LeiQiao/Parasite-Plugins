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

    ldap_service = None

    def __init__(self):
        super(LDAPUserConfig, self).__init__()

        if LDAPUserConfig.ldap_service is not None:
            return

        LDAPUserConfig.ldap_service = ldap.initialize(self.ldap_url)
        LDAPUserConfig.ldap_service.protocol_version = ldap.VERSION3

        try:
            LDAPUserConfig.ldap_service.simple_bind_s(self.ldap_admin_user_name, self.ldap_admin_password)
        except Exception as e:
            pa.log.error('LDAPUserPlugin: unable login ldap with admin user {0}'.format(e))
            raise e
