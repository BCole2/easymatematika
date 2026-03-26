from flask import Flask, render_template, session, request, redirect, url_for

app = Flask(__name__)
app.secret_key = 'tvuj_tajny_klic_ktery_nikomu_nerikej'

# Prototyp databáze
databaze_modulu = {
    "9-trida": {
        "zlomky": [
            {"id": 1, "typ": "teorie", "obsah": "Zlomek se skládá z čitatele a jmenovatele."},
            {"id": 2, "typ": "test", "obsah": "Vypočítej: 1/2 + 1/4"}
        ]
    }
}

# Přesměrování z hlavní stránky rovnou na zlomky (prozatím)
@app.route('/')
def index():
    return redirect('/main/9-trida/zlomky')

# Dynamická adresa pro učivo
@app.route('/main/<rocnik>/<tema>')
def zobraz_tema(rocnik, tema):
    moduly = databaze_modulu.get(rocnik, {}).get(tema, [])
    je_admin = session.get('je_admin', False)
    return render_template('tema.html', rocnik=rocnik, tema=tema, moduly=moduly, je_admin=je_admin)

# Přihlášení (jméno: admin, heslo: matika123)
@app.route('/login', methods=['GET', 'POST'])
def login():
    chyba = None
    if request.method == 'POST':
        if request.form['jmeno'] == 'admin' and request.form['heslo'] == 'matika123':
            session['je_admin'] = True
            return redirect('/main/9-trida/zlomky')
        else:
            chyba = "Špatné jméno nebo heslo!"
    return render_template('login.html', chyba=chyba)

# Odhlášení
@app.route('/logout')
def logout():
    session.pop('je_admin', None)
    return redirect('/main/9-trida/zlomky')

# Zpracování formuláře pro přidání nového modulu (příprava pro DB)
@app.route('/pridat_modul', methods=['POST'])
def pridat_modul():
    # Tady v budoucnu napíšeme kód, který to reálně uloží do databáze
    print(f"Přidávám {request.form['typ_modulu']}: {request.form['obsah']}")
    # Vrátí uživatele zpět na stránku, ze které formulář odeslal
    return redirect(request.referrer)

if __name__ == '__main__':
    app.run(debug=True)