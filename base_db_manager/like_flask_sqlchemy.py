from sqlalchemy import Column, String, Integer, SmallInteger, BigInteger, DateTime, ForeignKey, create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, relationship, backref, Query
from sqlalchemy.ext.declarative import declarative_base


class SQLAlchemy:
    def __init__(self, db_uri):
        self.engine = create_engine(db_uri, isolation_level='READ COMMITTED')
        self.session = sessionmaker(bind=self.engine)()
        self.Model =declarative_base(
                cls=Model,
                name='Model',
                metadata=None
            )
        self.Model.query_class = self._create_scoped_session(Query)
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

    def _create_scoped_session(self, query_cls):
        session = sessionmaker(autoflush=True, autocommit=False,
                               bind=self.engine, query_cls=query_cls)
        return scoped_session(session)

class Model:
    query = None
    query_class = None

class _QueryProperty:
    def __init__(self, sa):
        self.sa = sa

    def __get__(self, obj, class_type):
        return class_type.query_class.query(class_type)
