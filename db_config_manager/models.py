from pa import database as db


class Configuration(db.Model):
    __tablename__ = 'configuration'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    config_name = db.Column(db.String(500), nullable=False)
    config_json = db.Column(db.String(1024000), nullable=False)
