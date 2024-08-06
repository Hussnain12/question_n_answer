from flask import Flask, render_template, g, request,session, redirect,url_for
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db, connect_db
import os
app = Flask(__name__)

app.config['SECRET_KEY']=os.urandom(24)

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


@app.route('/')
def index():
    user=None
    if 'user' in session:
        user=session['user']
    
    return render_template('home.html',user=user)


@app.route('/register', methods=['POST', 'GET'])
def register():
    db = get_db()
    if request.method == 'POST':
        name = request.form['name']
        hashed_password = generate_password_hash(
            request.form['password'], method='pbkdf2:sha512')
        db.execute('insert into users (name, password, expert, admin) values (?, ?, ?, ?)', [
                   name, hashed_password, '0', '0'])
        db.commit()
        return 'user registered'
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    db = connect_db()
    if request.method == 'POST':
        name = request.form['name']
        password=request.form['password']
        cur=db.execute('select id,name,password from users where name=?', [name])
        result=cur.fetchone()
        if check_password_hash(result['password'],password):
            session['user']=result['name']
        else:
            return '<h1>Password not matched</h1>'
    return render_template('login.html')


@app.route('/question')
def question():
    return render_template('question.html')


@app.route('/answer')
def answer():
    return render_template('answer.html')


@app.route('/ask')
def ask():
    return render_template('ask.html')


@app.route('/unanswered')
def unanswered():
    return render_template('unanswered.html')


@app.route('/users')
def users():
    return render_template('users.html')

@app.route('/logout')
def logout():
    session.pop('user')
    return redirect(url_for('index'))
if __name__ == '__main__':
    app.run(debug=True)
