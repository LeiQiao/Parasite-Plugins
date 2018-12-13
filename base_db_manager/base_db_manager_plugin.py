from pa.plugin import Plugin
from plugins.base import BasePlugin
import importlib
from sqlalchemy import inspect, func
import pa
from .db_config import DBConfig


class BaseDBManagerPlugin(Plugin):
    __pluginname__ = 'base_db_manager'

    # 是否自动创建表
    __createtable__ = True

    def on_load(self):
        dbc = DBConfig()
        BaseDBManagerPlugin.__createtable__ = dbc.create_table
        BaseDBManagerPlugin.load_database(dbc.db_uri)

    @staticmethod
    def load_database(db_uri):
        pa.web_app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
        pa.web_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        # pa.web_app.config["SQLALCHEMY_ECHO"] = True
        pa.database.app = pa.web_app
        pa.database.init_app(pa.web_app)

    @Plugin.before_load
    def install_tables(self):
        # 获取模块的数据库表
        module_name = BasePlugin.get_module_name(self)
        plugin = importlib.import_module(module_name)
        plugin_tables = []
        for attribute_name in dir(plugin):
            if attribute_name.startswith('__'):
                continue
            attribute_value = getattr(plugin, attribute_name)
            if isinstance(attribute_value, type) and issubclass(attribute_value, pa.database.Model):
                plugin_tables.append(attribute_value)

        for table in plugin_tables:
            BaseDBManagerPlugin._install_table(table)

    @staticmethod
    def _install_table(table):
        if not BaseDBManagerPlugin.__createtable__:
            if not table.__table__.exists(pa.database.engine):
                pa.log.error('table \'{0}\' not exist.'.format(table.__tablename__))
            return

        # 如果表记录为空则尝试删除原表重新创建新表
        try:
            if table.__table__.exists(pa.database.engine):
                record_count = pa.database.session.query(func.count(table.__table__).label('count')).first()
                record_count = record_count.count
                if record_count == 0:
                    table.__table__.drop(pa.database.engine)
        except Exception as e:
            pa.log.info('unable drop table {0} {1}'.format(table.__tablename__, e))

        if not table.__table__.exists(pa.database.engine):
            table.__table__.create(pa.database.engine)
            return

        # 获取原表和新表的列
        iengine = inspect(pa.database.engine)
        old_cols = iengine.get_columns(table.__tablename__)
        new_cols = inspect(table).attrs
        if len(old_cols) != len(new_cols):
            raise TypeError('exists table has {0} columns but new table needs {1} columns in table \'{2}\''
                            .format(len(old_cols), len(new_cols), table.__tablename__))
        # 对比原表和新表的列是否一致，不一致则报错
        for new_col_conf in new_cols:
            new_col = None
            for column in new_col_conf.columns:
                if column.key == new_col_conf.key:
                    new_col = column
                    break
            old_col = None
            for oc in old_cols:
                if oc['name'] == new_col_conf.key:
                    old_col = oc
                    break
            if old_col is None or new_col is None:
                raise TypeError('column \'{0}\' is not exist in table \'{1}\''
                                .format(new_col_conf.key, table.__tablename__))

            for key in old_col.keys():
                if not hasattr(new_col, key):
                    raise TypeError('type \'{0}\' not defined in {1}.{2}'
                                    .format(key, table.__tablename__, new_col_conf.key))
                old_col_value = old_col[key]
                new_col_value = getattr(new_col, key)

                if not BaseDBManagerPlugin._check_columns_match(key, old_col_value, new_col_value):
                    raise TypeError('type \'{0}\' not match ({1} != {2}) in {3}.{4}'
                                    .format(key, old_col_value, new_col_value, table.__tablename__, new_col_conf.key))
        # 检查表结构一致则跳过建表
        pass

    @staticmethod
    def _check_columns_match(key, old_column_value, new_column_value):
        if key == 'type':
            matching = (old_column_value.Comparator == new_column_value.Comparator)
            if matching and (hasattr(old_column_value, 'length') or hasattr(new_column_value, 'length')):
                old_column_value_length = getattr(old_column_value, 'length', 0)
                new_column_value_length = getattr(new_column_value, 'length', 0)
                matching = (old_column_value_length == new_column_value_length)
        elif key == 'autoincrement':
            matching = True
        elif key == 'primary_key':
            matching = (old_column_value == 1)
            matching = (matching == new_column_value)
        elif key == 'default':
            matching = True
        elif key == 'nullable':
            matching = True
        else:
            matching = (old_column_value == new_column_value)
        return matching
