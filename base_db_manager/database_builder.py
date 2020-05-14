import pa
from .db_config import *


def build(engine, db_uri):
    if engine == DATABASE_ENGINE_FLASK_SQLALCHEMY:
        if pa.web_app is not None:
            _build_flask_sqlalchemy(db_uri)
        else:
            _build_like_flask_sqlchemy(db_uri)
    else:
        raise NotImplementedError('sqlalchemy 引擎数据库无法初始化，逻辑未实现')


def _build_flask_sqlalchemy(db_uri):
    from flask_sqlalchemy import SQLAlchemy
    pa.database = SQLAlchemy()

    pa.web_app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    pa.web_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # pa.web_app.config["SQLALCHEMY_ECHO"] = True
    pa.database.app = pa.web_app
    pa.database.init_app(pa.web_app)

def _build_like_flask_sqlchemy(db_uri):
    from .like_flask_sqlchemy import SQLAlchemy
    pa.database = SQLAlchemy(db_uri)
