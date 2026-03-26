import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'super_tajne_heslo_zmen_me'

# Nastavení databáze (Render ti dá URL, vlož ji sem nebo do Env Variables)
# Pro lokální testování použije sqlite, na Renderu použije PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///matika.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- MODELY PRO DATABÁZI ---

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    # Role: 'admin', 'ucitel', 'zak'
    role = db.Column(db.String(20), nullable=False, default='zak')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class TémaObsah(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rocnik = db.Column(db.String(20), nullable=False) # např. '9-trida'
    tema = db.Column(db.String(50), nullable=False)   # např. 'zlomky'
    typ = db.Column(db.String(20), nullable=False)    # 'teorie', 'test'
    obsah = db.Column(db.Text, nullable=False)

# Vytvoření databáze (spustí se jen jednou)
with app.app_context():
    db.create_all()
    # Vytvoříme prvního admina, pokud neexistuje (Jméno: admin, Heslo: admin123)
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- TRASY (ROUTES) ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role', 'zak') # Výchozí role je žák

        if User.query.filter_by(username=username).first():
            flash('Uživatelské jméno již existuje.')
            return redirect(url_for('register'))

        new_user = User(username=username, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registrace úspěšná. Nyní se můžeš přihlásit.')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Nesprávné jméno nebo heslo.')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/main/<rocnik>/<tema>')
def zobraz_tema(rocnik, tema):
    moduly = TémaObsah.query.filter_by(rocnik=rocnik, tema=tema).all()
    # Zkontrolujeme, jestli je přihlášený uživatel admin nebo učitel
    je_editor = current_user.is_authenticated and current_user.role in ['admin', 'ucitel']
    return render_template('tema.html', rocnik=rocnik, tema=tema, moduly=moduly, je_editor=je_editor)

# --- Nastavení na Renderu ---
if __name__ == '__main__':
    # Lokálně poběží na portu 5000
    app.run(debug=True)
