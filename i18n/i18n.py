import pa


class I18n:
    zh_CN = 'zh_CN'
    en = 'en'

    locale = zh_CN  # default chinese
    _messages = {}

    @staticmethod
    def get_message(message_key):
        if I18n.locale not in I18n._messages:
            pa.log.error('I18nPlugin: unable found locale \'{0}\''.format(I18n.locale))
            raise KeyError('unable found locale \'{0}\''.format(I18n.locale))

        if message_key not in I18n._messages[I18n.locale]:
            pa.log.error('I18nPlugin: unable found message \'{0}\' in \'{1}\''.format(message_key, I18n.locale))
            raise KeyError('unable found message \'{0}\' in \'{1}\''.format(message_key, I18n.locale))

        return I18n._messages[I18n.locale][message_key]

    @staticmethod
    def regist(**kwargs):
        max_index = 0
        for loc_key, msg_value in kwargs.items():
            if loc_key not in I18n._messages:
                I18n._messages[loc_key] = {}
            else:
                if max_index < len(I18n._messages[loc_key].keys()):
                    max_index = len(I18n._messages[loc_key].keys())

        for loc_key, msg_value in kwargs.items():
            I18n._messages[loc_key][max_index] = msg_value

        return max_index


def i18n_set_locale(locale):
    I18n.locale = locale


def i18n(message_key):
    return I18n.get_message(message_key)
