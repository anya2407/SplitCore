from flask_sqlalchemy import SQLAlchemy
db= SQLAlchemy()
class Users(db.Model):
    __tablename__="users"

    user_id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(100))
    email=db.Column(db.String(100),unique=True)
    password=db.Column(db.String(255))

class Group(db.Model):
    __tablename__ = "group"
    group_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    created_by = db.Column(db.Integer, db.ForeignKey('users.user_id'))

    expenses = db.relationship('Expense', backref='group')

class GroupMember(db.Model):
    __tablename__ = "group_members"

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.group_id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))

    user=db.relationship('Users')

class Expense(db.Model):
    __tablename__="expense"

    id=db.Column(db.Integer,primary_key=True)
    amount=db.Column(db.Float,nullable=False)
    description=db.Column(db.String(200))

    group_id=db.Column(db.Integer,db.ForeignKey('group.group_id'))
    paid_by = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    payer = db.relationship('Users', foreign_keys=[paid_by])


