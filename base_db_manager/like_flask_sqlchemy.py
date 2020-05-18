from sqlalchemy import Column, String, Integer, SmallInteger, BigInteger, DateTime, ForeignKey, create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, relationship, backref, Query, class_mapper
from sqlalchemy.ext.declarative import declarative_base


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
    def __del__(self):
        self.session.remove()


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
