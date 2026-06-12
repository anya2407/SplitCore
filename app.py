from flask import Flask,request,render_template,session,redirect,url_for
from config import Config
from models import Users,db,Group,GroupMember,Expense,ExpenseSplit
import bcrypt
from pydantic import BaseModel, EmailStr, Field
from pydantic import ValidationError
from flask import abort


class RegisterSchema(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=6)

class ExpenseSchema(BaseModel):
    description: str = Field(min_length=1, max_length=200)
    amount: float = Field(gt=0)
    paid_by: int
    split_type: str = Field(pattern="^(equal|custom)$")

class GroupSchema(BaseModel):
    name: str = Field(min_length=1, max_length=100)

class MemberSchema(BaseModel):
    username: str = Field(min_length=1)

class LoginSchema(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)

class SettleSchema(BaseModel):
    debitor: int
    creditor: int
    amount: float = Field(gt=0)


app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template("login.html")

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        try:
            data = RegisterSchema(
                name=request.form['name'],
                email=request.form['email'],
                password=request.form['password']
            )
        except ValidationError as e:
            return str(e), 400

        hashed_password = bcrypt.hashpw(data.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user = Users(name=data.name, email=data.email, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        try:
            data = LoginSchema(
                email=request.form['email'],
                password=request.form['password']
            )
        except ValidationError as e:
            return abort(400, description=str(e))

        user = Users.query.filter_by(email=data.email).first()
        if user:
            if bcrypt.checkpw(data.password.encode('utf-8'), user.password.encode('utf-8')):
                session['user_id'] = user.user_id
                return redirect(url_for('dashboard'))
            else:
                return abort(401, description="incorrect password")
        return abort(404, description="user does not exist, register first")
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    user_id=session['user_id']
    memberships = GroupMember.query.filter_by(user_id=user_id, is_active=True).all()

    groups = []
    for m in memberships:
        group = Group.query.get(m.group_id)
        groups.append(group)
        
    return render_template('dashboard.html',groups=groups)

@app.route('/logout')
def logout():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/create_group', methods=['GET', 'POST'])
def create_group():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            data = GroupSchema(name=request.form['name'])
        except ValidationError as e:
            return abort(400,description=str(e))

        group = Group(name=data.name, created_by=session['user_id'])
        db.session.add(group)
        db.session.commit()

        member = GroupMember(group_id=group.group_id, user_id=session['user_id'])
        db.session.add(member)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('create_group.html')

@app.route('/group/<int:group_id>')
def group_detail(group_id):
    if 'user_id' not in session :
        return redirect(url_for('login'))
    users= GroupMember.query.filter_by(group_id=group_id,user_id=session['user_id']).first()
    if not users:
        return redirect(url_for('dashboard'))

    group=Group.query.get_or_404(group_id)
    group_members = GroupMember.query.filter_by(group_id=group_id, is_active=True).all()
    expenses=Expense.query.filter_by(group_id=group_id).all()
    balances={}
    names={}
    for m in group_members:
        balances[m.user_id]=0
        names[m.user_id]=m.user.name
    for e in expenses:
        if not e.is_settlement:
            balances[e.paid_by] += e.amount
            for exp in e.splits:
                balances[exp.user_id] -= exp.amount
        else:
            balances[e.paid_by] -= e.amount
            for exp in e.splits:
                balances[exp.user_id] += exp.amount
    
    transactions=manage_transactions(balances)

    return render_template('group_detail.html',group=group,group_members=group_members,expenses=expenses,transactions=transactions,names=names)
            
def manage_transactions(balances):
    deb=[]
    cred=[]
    for b,amt in balances.items():
        if amt > 0:
            cred.append([b, amt])
        elif amt < 0:
            deb.append([b, amt])
    cred.sort(key=lambda x: -x[1])
    deb.sort(key=lambda x: -x[1])
    i=0
    j=0
    transactions=[]
    while i<len(cred) and j<len(deb):
        debitor,d_amt=deb[j]
        creditor,c_amt=cred[i]

        amount=min(c_amt,abs(d_amt))
        transactions.append([debitor,creditor,amount])

        deb[j][1]+=amount
        cred[i][1]-=amount

        if deb[j][1]==0: j+=1
        if cred[i][1]==0: i+=1
    return transactions



@app.route('/group/<int:group_id>/add_member', methods=['POST'])
def add_member(group_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    try:
        data = MemberSchema(username=request.form['username'])
    except ValidationError as e:
        return abort (400,str(e))

    user = Users.query.filter_by(name=data.username).first()
    if not user:
        return abort(404,"user does not exist")
    existing = GroupMember.query.filter_by(user_id=user.user_id, group_id=group_id, is_active=True).first()
    if existing:
        return abort(400,"user already in group")

    new = GroupMember(user_id=user.user_id, group_id=group_id)
    db.session.add(new)
    db.session.commit()
    return redirect(url_for('group_detail', group_id=group_id))

@app.route('/group/<int:group_id>/delete_member',methods=['POST'])
def delete_member(group_id):
    group=Group.query.get_or_404(group_id)
    group_members = GroupMember.query.filter_by(group_id=group_id, is_active=True).all()
    expenses=Expense.query.filter_by(group_id=group_id).all()
    balances={}
    names={}
    for m in group_members:
        balances[m.user_id]=0
        names[m.user_id]=m.user.name
    for e in expenses:

        if not e.is_settlement:
            balances[e.paid_by] += e.amount

            for exp in e.splits:
                balances[exp.user_id] -= exp.amount

        else:
            balances[e.paid_by] -= e.amount

            for exp in e.splits:
                balances[exp.user_id] += exp.amount
    person=int(request.form['person'])
    if balances[person]!=0:
        return abort (400,description="cant delete a person with pending balances")
    member=GroupMember.query.filter_by(group_id=group_id,user_id=person).first()
    member.is_active=False
    db.session.commit()
    if not member.is_active:print("hello")

    return redirect(url_for('group_detail',group_id=group_id)) 


@app.route('/group/<int:group_id>/add_expense', methods=['POST'])
def add_expense(group_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    try:
        data = ExpenseSchema(
            description=request.form['description'],
            amount=request.form['amount'],
            paid_by=request.form['paid_by'],
            split_type=request.form['split_type']
        )
    except ValidationError as e:
        return str(e), 400

    paid_for = request.form.getlist('participants')
    paid_for = [int(p) for p in paid_for if p]
    if not paid_for:
        return abort(400,"select at least one participant")

    expense = Expense(
        description=data.description,
        amount=data.amount,
        group_id=group_id,
        paid_by=data.paid_by,
        split_type=data.split_type
    )
    db.session.add(expense)
    db.session.flush()

    if data.split_type == 'equal':
        x = data.amount / len(paid_for)
        for person in paid_for:
            db.session.add(ExpenseSplit(expense_id=expense.id, user_id=person, amount=x))

    if data.split_type == 'custom':
        total = 0
        splits = []
        for uid in paid_for:
            amt = float(request.form.get(f"split_{uid}", 0))
            total += amt
            splits.append(ExpenseSplit(expense_id=expense.id, user_id=uid, amount=amt))
        if abs(total - data.amount) > 0.01:
            db.session.rollback()
            return abort(400,"split amounts do not match total")
        for s in splits:
            db.session.add(s)

    db.session.commit()
    return redirect(url_for('group_detail', group_id=group_id))

@app.route('/group/<int:group_id>/settle', methods=['POST'])
def settle(group_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    try:
        data = SettleSchema(
            debitor=request.form['debitor'],
            creditor=request.form['creditor'],
            amount=request.form['amount']
        )
    except ValidationError as e:
        return str(e), 400

    settle_balance = Expense(
        amount=data.amount,
        description="settlement",
        group_id=group_id,
        paid_by=data.creditor,
        split_type="custom",
        is_settlement=True
    )
    db.session.add(settle_balance)
    db.session.flush()
    db.session.add(ExpenseSplit(
        expense_id=settle_balance.id,
        user_id=data.debitor,
        amount=data.amount
    ))
    db.session.commit()
    return redirect(url_for('group_detail', group_id=group_id))

if __name__== "__main__":
    app.run(host='0.0.0.0',debug=False)