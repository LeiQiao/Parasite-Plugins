from sqlalchemy import Column, String, Integer, SmallInteger, BigInteger, DateTime, ForeignKey, create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, relationship, backref, Query, class_mapper
from sqlalchemy.ext.declarative import declarative_base


"""
    like_flask_sqlalchemy
    ~~~~~~~~~~~~~~~~

    用于在非 flask 项目中像 flask_sqlalchemy 一样操作数据库

    !重要，因为没有 flask 的请求规则，所以在具体的使用场景中(一般在多线程中使用较多)
    记住一定要在数据库操作完毕(最好推迟到线程结束前)时调用下面语句用来释放数据库连接：

    db.session.remove()

    否则会出现以下类似错误：

    QueuePool limit of size 5 overflow 10 reached, connection timed out, timeout 30
"""
class SQLAlchemy:
    def __init__(self, db_uri):
        self.engine = create_engine(db_uri, pool_recycle=3600)
        self.session_factory = sessionmaker(bind=self.engine)
        self.session = scoped_session(self.session_factory)
        self.Model =declarative_base(
                cls=Model,
                name='Model',
                metadata=None
            )
        self.Model.query = _QueryProperty(self)
        self.Column = Column
        self.String = String
        self.DateTime = DateTime
        self.Integer = Integer
        self.SmallInteger = SmallInteger
        self.BigInteger = BigInteger
        self.ForeignKey = ForeignKey
        self.relationship = relationship
        self.backref = backref


class BaseQuery(Query):
    pass


class Model:
    query = None
    query_class = BaseQuery


class _QueryProperty:
    def __init__(self, sa):
        self.sa = sa

    def __get__(self, obj, class_type):
        mapper = class_mapper(class_type)
        return class_type.query_class(mapper, session=self.sa.session())
        # return class_type.query_class().query(class_type)
