from flask import Flask, render_template, g, request, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db, connect_db
import os
app = Flask(__name__)

app.config['SECRET_KEY'] = os.urandom(24)


def get_current_user():
    user_result = None
    if 'user' in session:
        db = connect_db()
        user = session['user']

        cur = db.execute(
            'select id,name,password,expert,admin from users where name = ?', [user])
        user_result = cur.fetchone()
    return user_result


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


@app.route('/')
def index():
    user = get_current_user()
    db = get_db()

    questions_cur = db.execute('select questions.id as question_id, questions.question_text, askers.name as asker_name, experts.name as expert_name from questions join users as askers on askers.id = questions.asked_by_id join users as experts on experts.id = questions.expert_id where questions.answer_text !="" ')
    questions_result = questions_cur.fetchall()

    return render_template('home.html', user=user, questions=questions_result)


@app.route('/register', methods=['POST', 'GET'])
def register():
    user = get_current_user()
    db = get_db()
    if request.method == 'POST':
        name = request.form['name']
        cur = db.execute('select id from users where name = ?', [name])
        existing_user = cur.fetchone()
        if existing_user:
            return render_template('register.html', user=user, error="User exists already")
        hashed_password = generate_password_hash(
            request.form['password'], method='pbkdf2:sha512')
        db.execute('insert into users (name, password, expert, admin) values (?, ?, ?, ?)', [
                   name, hashed_password, '0', '0'])
        db.commit()
        return render_template('register.html', user=user)
    return render_template('register.html', user=user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    user = get_current_user()
    db = connect_db()
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        cur = db.execute(
            'select id,name,password from users where name=?', [name])
        result = cur.fetchone()
        if check_password_hash(result['password'], password):
            session['user'] = result['name']
            return redirect(url_for('index'))
        else:
            return '<h1>Password not matched</h1>'
    return render_template('login.html', user=user)


@app.route('/question/<question_id>')
def question(question_id):

    user = get_current_user()
    db = get_db()
    cur = db.execute(
        'select questions.question_text,questions.answer_text, askers.name as asker_name, experts.name as expert_name from questions join users as askers on askers.id = questions.asked_by_id join users as experts on experts.id = questions.expert_id where questions.id=? ', [question_id])
    result = cur.fetchone()
    return render_template('question.html', user=user, data=result)


@app.route('/answer/<question_id>', methods=['POST', 'GET'])
def answer(question_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    if user['expert'] == 0:
        return redirect(url_for('index'))
    db = get_db()
    cur = db.execute(
        'select id,question_text from questions where id=?', [question_id])
    result = cur.fetchone()
    if request.method == "POST":

        answer_text = request.form['answer-text']
        db.execute('update questions set answer_text = ? where id = ? ',
                   [answer_text, question_id])
        db.commit()
    return render_template('answer.html', user=user, question=result)


@app.route('/ask', methods=['POST', 'GET'])
def ask():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    db = get_db()
    print(user['id'])
    if request.method == "POST":
        question_text = request.form['question']
        answer_text = ""
        asked_by_id = user['id']
        expert_id_ask = request.form['select-expert']
        db.execute(
            'INSERT INTO questions (question_text, answer_text, asked_by_id, expert_id) VALUES (?, ?, ?, ?)', [question_text, answer_text, asked_by_id, expert_id_ask])
        db.commit()

        return redirect(url_for('ask'))
    cur = db.execute('select id, name from users where expert = 1')
    results = cur.fetchall()
    return render_template('ask.html', experts=results, user=user)


@app.route('/unanswered')
def unanswered():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    print(user['expert'])
    if user['expert'] == 0:
        return redirect(url_for('index'))
    print('mein idr bund mara ra hn')
    db = get_db()
    cur = db.execute('''SELECT q.id AS question_id, q.question_text, q.answer_text, q.asked_by_id, q.expert_id, u.name AS asked_by_name
               FROM questions q
               JOIN users u ON q.asked_by_id=u.id
               WHERE q.expert_id=? AND q.answer_text == "" ''', [user['id']])
    results = cur.fetchall()
    return render_template('unanswered.html', all_question=results, user=user)


@app.route('/users')
def users():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    if user['admin'] == 0:
        return redirect(url_for('index'))
    db = get_db()
    cur = db.execute('select id, name, expert, admin from users')
    results = cur.fetchall()
    return render_template('users.html', user=user, users=results)


@app.route('/logout')
def logout():
    session.pop('user')
    return redirect(url_for('index'))


@app.route('/promote/<user_id>')
def promote(user_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    if user['admin'] == 0:
        return redirect(url_for('index'))
    db = get_db()
    cur = db.execute('select expert from users where id = ?', [user_id])
    results = cur.fetchone()
    if results['expert'] == 1:
        db.execute('update users set expert = 0 where id = ?', [user_id])
        db.commit()
    else:
        db.execute('update users set expert = 1 where id = ?', [user_id])
        db.commit()
    return redirect(url_for('users'))


if __name__ == '__main__':
    app.run(debug=True)
