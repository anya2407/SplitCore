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
    is_active=db.Column(db.Boolean,default=True)

    user=db.relationship('Users')

class Expense(db.Model):
    __tablename__="expense"

    id=db.Column(db.Integer,primary_key=True)
    amount=db.Column(db.Float,nullable=False)
    description=db.Column(db.String(200))

    group_id=db.Column(db.Integer,db.ForeignKey('group.group_id'))
    paid_by = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    split_type=db.Column(db.String(50),default="equal")
    is_settlement=db.Column(db.Boolean,default=False)

    payer = db.relationship('Users', foreign_keys=[paid_by])
    splits = db.relationship('ExpenseSplit', backref='expense')
    

class ExpenseSplit(db.Model):
    __tablename__='expensesplit'

    id=db.Column(db.Integer,primary_key=True)
    expense_id=db.Column(db.Integer, db.ForeignKey('expense.id'))
    user_id=db.Column(db.Integer, db.ForeignKey('users.user_id'))
    amount=db.Column(db.Float)

    user = db.relationship('Users')



