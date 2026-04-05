from flask_sqlalchemy import SQLAlchemy
db= SQLAlchemy()
class Users(db.Model):
    __tablename__="users"

    user_id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(100))
    email=db.Column(db.String(100),unique=True)
    password=db.Column(db.String(255))

class Group(db.Model):
    __tablename__ = "groups"
    group_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    created_by = db.Column(db.Integer, db.ForeignKey('users.user_id'))

class GroupMember(db.Model):
    __tablename__ = "group_members"

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.group_id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))