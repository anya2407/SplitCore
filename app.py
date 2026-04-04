from flask import Flask,request,render_template,session
app =Flask(__name__, template_folder='templates')

app.secret_key="some key"

@app.route('/')
def index():
    return render_template('index.html',message="hello")

@app.route('/hello')
def hello():
    return render_template(template_name_or_list= 'index.html',message="hello")

@app.route("/home")
def home():
    if "name" in request.args.keys() and "age" in request.args.keys():
        name=request.args.get("name")
        age=request.args.get("age")
        return f"name is {name}, age is {age}" 
    else:
        return "parameters missing" 

@app.route("/form",methods=['GET','POST'])
def form():
    if request.method=='GET':
        return render_template('auth.html')
    else:
        name=request.form.get('name')
        email=request.form.get('email')
        gender=request.form.get('gender')
        
        if name=="anya" and email=="anyarora2407@gmail.com" and gender=='female':
            return 'success'
        return "fail"


@app.route("/set_data")
def set_data():
    session['name']='anya'
    session['age']=20
    return render_template(template_name_or_list="index.html",message="data is set")

@app.route("/get_data")
def get_data():
    name=session['name']
    age =session['age']
    return render_template(template_name_or_list="index.html",message="data is gotten",name=name,age=age)

if __name__== "__main__":
    app.run(host='0.0.0.0',debug=True)