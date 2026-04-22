print("app.py execution started")
from flask import Flask, render_template, redirect, url_for, request, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from datetime import timedelta
from sqlalchemy import func

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///retail.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Models ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.String(50))
    product_id = db.Column(db.String(50))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    quantity = db.Column(db.Integer)

# --- Routes ---
@app.route('/')
def home():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            return 'Username already exists!'
        new_user = User(username=username, password_hash=generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session['user'] = username
            return redirect(url_for('dashboard'))
        else:
            return 'Invalid username or password'
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=session['user'])

@app.route('/transactions')
def transactions():
    if 'user' not in session:
        return redirect(url_for('login'))
    customer_id = session['user']
    transactions = Transaction.query.filter_by(customer_id=customer_id).all()
    return render_template('transactions.html', transactions=transactions)

@app.route('/add_transaction', methods=['GET', 'POST'])
def add_transaction():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        product_id = request.form['product_id']
        quantity = int(request.form['quantity'])
        customer_id = session['user']
        new_transaction = Transaction(customer_id=customer_id, product_id=product_id, quantity=quantity)
        db.session.add(new_transaction)
        db.session.commit()
        return redirect(url_for('transactions'))
    return render_template('add_transaction.html')
@app.route('/recommendation')
def recommendation():
    if 'user' not in session:
        return redirect(url_for('login'))

    customer_id = session['user']
    cutoff_date = datetime.utcnow() - timedelta(days=30)

    overall = db.session.query(
        Transaction.product_id,
        func.count(Transaction.product_id).label('times')
    ).filter(
        Transaction.customer_id == customer_id
    ).group_by(Transaction.product_id).order_by(func.count(Transaction.product_id).desc()).first()

    recent = db.session.query(
        Transaction.product_id,
        func.count(Transaction.product_id).label('times')
    ).filter(
        Transaction.customer_id == customer_id,
        Transaction.date > cutoff_date
    ).group_by(Transaction.product_id).order_by(func.count(Transaction.product_id).desc()).first()

    overall_recommended = overall.product_id if overall else 'No purchases yet'
    recent_recommended = recent.product_id if recent else 'No recent purchases'

    return render_template('recommendation.html', overall=overall_recommended, recent=recent_recommended)
# Run the app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Starting Flask app..")
    app.run(debug=True)
    print("Flask app exited")
  # Add this with your other imports at the top if not already present

