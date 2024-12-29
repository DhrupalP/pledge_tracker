from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pledges.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
Bootstrap(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mis_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)

class Pledge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)  # Weekly/Package/One-Time
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='Pending')

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(100), nullable=False)
    mis_id = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/users', methods=['GET', 'POST'])
def manage_users():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        mis_id = request.form['mis_id']
        user = User(name=name, email=email, mis_id=mis_id)
        db.session.add(user)
        db.session.commit()
        flash('User added successfully!', 'success')
        return redirect(url_for('manage_users'))

    users = User.query.all()
    return render_template('users.html', users=users)

@app.route('/pledges', methods=['GET', 'POST'])
def manage_pledges():
    if request.method == 'POST':
        user_id = request.form['user_id']
        event_type = request.form['event_type']
        amount = request.form['amount']
        pledge = Pledge(user_id=user_id, event_type=event_type, amount=amount)
        db.session.add(pledge)
        db.session.commit()
        flash('Pledge created successfully!', 'success')
        return redirect(url_for('manage_pledges'))

    pledges = Pledge.query.all()
    users = User.query.all()
    return render_template('pledges.html', pledges=pledges, users=users)

@app.route('/upload_transactions', methods=['GET', 'POST'])
def upload_transactions():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            filepath = os.path.join('uploads', file.filename)
            file.save(filepath)
            transactions = pd.read_excel(filepath)
            for _, row in transactions.iterrows():
                transaction = Transaction(
                    transaction_id=row['Transaction ID'],
                    mis_id=row['MIS ID'],
                    amount=row['Amount'],
                    date=row['Date']
                )
                db.session.add(transaction)
            db.session.commit()
            flash('Transactions uploaded successfully!', 'success')
            return redirect(url_for('upload_transactions'))

    return render_template('upload_transactions.html')

@app.route('/dashboard')
def dashboard():
    pledges = Pledge.query.all()
    transactions = Transaction.query.all()

    total_pledges = sum(p.amount for p in pledges)
    total_collected = sum(t.amount for t in transactions)
    remaining = total_pledges - total_collected

    return render_template('dashboard.html', 
                           total_pledges=total_pledges, 
                           total_collected=total_collected, 
                           remaining=remaining)

# Run setup
def setup():
    if not os.path.exists('uploads'):
        os.mkdir('uploads')
    db.create_all()

if __name__ == '__main__':
    setup()
    app.run(debug=True)
