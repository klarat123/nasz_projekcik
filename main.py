from flask import Flask, render_template, request, redirect, url_for, flash, make_response, session, Response, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf.csrf import CSRFProtect
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'  
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'supersecretkey'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
csrf = CSRFProtect(app)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False) 
    games_played = db.Column(db.Integer, default=0)
    games_won = db.Column(db.Integer, default=0)
    percentage = db.Column(db.Integer, default=0)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


with app.app_context():
    db.create_all()

@app.route('/')
def home():
    dark_mode = session.get('dark_mode', False)
    return render_template('home.html', dark_mode=dark_mode)

@app.route('/glowna')
@login_required
def glowna():
    dark_mode = session.get('dark_mode', False)
    return render_template('glowna.html', dark_mode=dark_mode)

@app.route('/register', methods=['GET', 'POST'])
def register():
    dark_mode = session.get('dark_mode', False)
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

       
        if password != confirm_password:
            flash('Hasła się nie zgadzają!', 'danger')
            return redirect(url_for('register'))

        
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Nazwa użytkownika lub e-mail już istnieje.', 'danger')
            return redirect(url_for('register'))

        
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('Rejestracja zakończona sukcesem! Możesz się teraz zalogować.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', dark_mode=dark_mode)

@app.route('/login', methods=['GET', 'POST'])
def login():
    dark_mode = session.get('dark_mode', False)
    if request.method == 'POST':
        identifier = request.form['identifier']
        password = request.form['password']

      
        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier)
        ).first()

      
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('Zalogowano pomyślnie!', 'success') 
            return redirect(url_for('glowna'))  
        else:
            flash('Błędna nazwa użytkownika/email lub hasło', 'danger') 

    return render_template('login.html', dark_mode=dark_mode)

@app.route('/update_statistics', methods=['POST'])
@login_required
def update_statistics_route():
    won_game = request.json.get('won_game')  
    user_id = request.json.get('user_id') 
    
    
    user = User.query.get(user_id)
    
    if user:
        update_statistics(user, won_game)  
        return jsonify({"message": "Statystyki zostały zaktualizowane"})
    else:
        return jsonify({"message": "Nie znaleziono użytkownika"}), 404



def update_statistics(user, won_game):
    
    user.games_played += 1
    
   
    if won_game:
        user.games_won += 1
    
    
    if user.games_played > 0:
        user.percentage = int((user.games_won / user.games_played) * 100)
    else:
        user.percentage = 0 
    
   
    db.session.commit()


@app.route('/wordiez')
@login_required
def gra_wordiez():
    plik = open("slowa.txt", "r")
    klucz = losowy_klucz_plik(plik)
    user = current_user
    return render_template('wordiez.html', user=user, klucz=klucz)

def losowy_klucz_plik(plik):
    try:
        with plik as pliczek:
            linijki = pliczek.readlines()
            losowy_klucz = random.choice(linijki).strip()
            print(losowy_klucz)
        return losowy_klucz
    except FileNotFoundError:
        return None
           

@app.route('/zasady')
def zasady():
    dark_mode = session.get('dark_mode', False)
    return render_template('zasady.html', dark_mode=dark_mode)

@app.route('/toggle-dark-mode')
def toggle_dark_mode():
    session['dark_mode'] = not session.get('dark_mode', False)
    return redirect(request.referrer)



@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/twoje-statystyki')
@login_required
def twoje_statystyki():
    user = current_user
    return render_template('twoje-statystyki.html', user=user)

@app.route('/udostepnione-statystyki/<int:user_id>')
def udostepnione_statystyki(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('udostepnione-statystyki.html', user=user)


if __name__ == '__main__':
    app.run(debug=True)