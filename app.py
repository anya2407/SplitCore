from flask import Flask,request,render_template,session,redirect,url_for
from config import Config
from models import Users,db,Group,GroupMember,Expense
import bcrypt

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template("login.html")

@app.route('/register',methods=['POST','GET'])
def register():
    if request.method=='POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        hashed_password=bcrypt.hashpw(password.encode('utf-8'),bcrypt.gensalt()).decode('utf-8')
        user= Users(
            name=name,
            email=email,
            password=hashed_password
        )
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login',methods=['POST','GET'])
def login():
    if request.method=='POST':
        email = request.form['email']
        password = request.form['password']

        user = Users.query.filter_by(email=email).first()
        if user:
            if bcrypt.checkpw(password.encode('utf-8'),user.password.encode('utf-8')):
                session['user_id']=user.user_id
                return redirect(url_for('dashboard'))
            else:
                return "incorrect pass"
        return "user does not exist, register first"
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    user_id=session['user_id']
    memberships = GroupMember.query.filter_by(user_id=user_id).all()

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
        name = request.form['name']

        group = Group(
            name=name,
            created_by=session['user_id']
        )
        db.session.add(group)
        db.session.commit()

        member = GroupMember(
        group_id=group.group_id,
        user_id=session['user_id']
        )

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
    group_members = GroupMember.query.filter_by(group_id=group_id).all()
    expenses=Expense.query.filter_by(group_id=group_id).all()
    return render_template('group_detail.html',group=group,group_members=group_members,expenses=expenses)
            

@app.route('/group/<int:group_id>/add_member',methods=['POST'])
def add_member(group_id):
    username=request.form['username']

    user=Users.query.filter_by(name=username).first()
    if not user:
        return "user does not exist"
    group=GroupMember.query.filter_by(user_id=user.user_id,group_id=group_id).first()
    if group:
        return "user already exists"
    
    new=GroupMember(user_id=user.user_id,group_id=group_id)
    db.session.add(new)
    db.session.commit()
    return redirect(url_for('group_detail',group_id=group_id))

@app.route('/group/<int:group_id>/add_expense',methods=['POST'])
def add_expense(group_id):
    description=request.form['description']
    amount=float(request.form['amount'])
    paid_by=int(request.form['paid_by']
    )
    expense=Expense(
        description=description,
        amount=amount,
        group_id=group_id,
        paid_by=paid_by
    )
    db.session.add(expense)
    db.session.commit()

    return redirect(url_for('group_detail',group_id=group_id))





if __name__== "__main__":
    app.run(host='0.0.0.0',debug=True)