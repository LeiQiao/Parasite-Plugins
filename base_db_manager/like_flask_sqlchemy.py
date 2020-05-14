from sqlalchemy import Column, String, Integer, SmallInteger, BigInteger, DateTime, ForeignKey, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


class SQLAlchemy:
    def __init__(self, db_uri):
        self.database = create_engine(db_uri)
        self.session = sessionmaker(bind=self.database)()
        self.Model =declarative_base(
                cls=Model,
                name='Model',
                metadata=None
            )
        self.Model.query_class = self.session
        self.Model.query = _QueryProperty(self)
        self.Column = Column
        self.String = String
        self.DateTime = DateTime
        self.Integer = Integer
        self.SmallInteger = SmallInteger
        self.BigInteger = BigInteger
        self.ForeignKey = ForeignKey

class Model:
    query = None
    query_class = None

class _QueryProperty:
    def __init__(self, sa):
        self.sa = sa

    def __get__(self, obj, class_type):
        return class_type.query_class.query(class_type)
