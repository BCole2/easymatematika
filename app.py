import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'super-tajny-klic-matika'

# Připojení k databázi na Renderu
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///local.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- MODELY ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='zak')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Modul(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rocnik = db.Column(db.String(20), nullable=False)
    tema = db.Column(db.String(50), nullable=False)
    typ = db.Column(db.String(20), nullable=False)
    obsah = db.Column(db.Text, nullable=False)

# Inicializace databáze
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- TRASY ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.check_password(request.form['password']):
            login_user(user)
            return redirect(url_for('index'))
        flash('Chybné jméno nebo heslo!')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if User.query.filter_by(username=request.form['username']).first():
            flash('Uživatel už existuje!')
        else:
            new_user = User(username=request.form['username'], role=request.form['role'])
            new_user.set_password(request.form['password'])
            db.session.add(new_user)
            db.session.commit()
            flash('Registrace úspěšná! Můžeš se přihlásit.')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/main/<rocnik>/<tema>')
def zobraz_tema(rocnik, tema):
    moduly = Modul.query.filter_by(rocnik=rocnik, tema=tema).all()
    je_editor = current_user.is_authenticated and current_user.role in ['admin', 'ucitel']
    return render_template('tema.html', rocnik=rocnik, tema=tema, moduly=moduly, je_editor=je_editor)

@app.route('/add_modul', methods=['POST'])
@login_required
def add_modul():
    if current_user.role not in ['admin', 'ucitel']: return "Zakázáno", 403
    novy = Modul(rocnik=request.form['rocnik'], tema=request.form['tema'], 
                 typ=request.form['typ'], obsah=request.form['obsah'])
    db.session.add(novy)
    db.session.commit()
    return redirect(request.referrer)

if __name__ == '__main__':
    app.run(debug=True)