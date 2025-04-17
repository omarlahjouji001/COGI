from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import timedelta
import json
import os
import requests
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()
client = OpenAI(
    api_key=os.environ["TOGETHER_API_KEY"],
    base_url="https://api.together.xyz/v1"
)

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.permanent_session_lifetime = timedelta(minutes=30)  # Expire après 30 min d'inactivité

USERS_FILE = 'users.json'
MAX_ATTEMPTS = 5

# Fonction utilitaire : Charger les utilisateurs depuis le fichier JSON
def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

# Fonction utilitaire : Sauvegarder les utilisateurs dans le fichier JSON
def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

# Fonction utilitaire pour sauvegarder un nouvel utilisateur
def save_user(data):
    users = load_users()

    # Vérification si l'email est déjà utilisé
    email = data.get("email")
    if email in users:
        return False  # Email déjà utilisé

    # Ajout du nouvel utilisateur
    users[email] = {
        "first_name": data.get("first_name"),
        "last_name": data.get("last_name"),
        "email": email,
        "password": generate_password_hash(data.get("password")),
        "gender": data.get("gender"),
        "dob": data.get("dob"),
        "attempts": 0
    }

    try:
        save_users(users)  # Sauvegarde les utilisateurs dans le fichier
        return True
    except Exception as e:
        print(f"Erreur lors de la sauvegarde : {e}")
        return False

def generate_response(prompt, system_message="Tu es un assistant de soutien psychologique. Reste calme, humain et à l'écoute."):
    try:
        response = client.chat.completions.create(
            model="mistralai/Mistral-7B-Instruct-v0.1",  # ✅ modèle GRATUIT et SERVERLESS
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=200,
            top_p=0.9
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Erreur lors de la génération: {e}")
        return f"Erreur: {str(e)}"

# Route Accueil
@app.route('/')
def index():
    return render_template('index.html')

# API endpoint for chat
@app.route('/send_message', methods=["POST"])
def send_message():
    if "user" not in session:
        return jsonify({"error": "Non authentifié"}), 401
    
    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"error": "Message requis"}), 400
    
    user_message = data["message"]
    system_message = data.get("system_message", "Tu es un assistant de soutien psychologique. Reste calme, humain et à l'écoute.")
    
    try:
        response_text = generate_response(user_message, system_message)
        return jsonify({
            "status": "success",
            "response": response_text
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

# Route Login sécurisée
@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            flash('Nom d\'utilisateur et mot de passe sont requis !', 'error')
            return redirect(url_for("login"))

        users = load_users()

        user_data = users.get(username)
        if not user_data:
            flash("Utilisateur inconnu.", "error")
            return redirect(url_for("login"))

        # Vérification du nombre d'essais
        if user_data.get("attempts", 0) >= MAX_ATTEMPTS:
            flash("Trop de tentatives échouées. Veuillez réessayer plus tard.", "error")
            return redirect(url_for("login"))

        # Vérification du mot de passe
        if not check_password_hash(user_data["password"], password):
            users[username]["attempts"] = user_data.get("attempts", 0) + 1
            save_users(users)
            flash("Nom d'utilisateur ou mot de passe incorrect.", "error")
            return redirect(url_for("login"))

        # Réinitialisation des tentatives en cas de succès
        users[username]["attempts"] = 0
        save_users(users)

        session.permanent = True
        session["user"] = username
        return redirect(url_for("chat"))

    return render_template("login.html")

# Route réinitialisation du mot de passe
@app.route('/reset-password', methods=["POST"])
def reset_password():
    email = request.form.get("email")
    # Logique pour vérifier l'email et envoyer un lien de réinitialisation (par exemple, via un service comme Flask-Mail)
    flash("Un lien de réinitialisation a été envoyé à votre adresse e-mail.", "success")
    return redirect(url_for('login'))


# Route Chat
@app.route('/chat')
def chat():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template('chat.html', username=session["user"])

# Route Déconnexion
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# Route Mission
@app.route('/mission')
def mission():
    return render_template('mission.html')

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        email = request.form.get("email")
        password = request.form.get("password")
        gender = request.form.get("gender")
        dob = request.form.get("dob")
        recaptcha_response = request.form.get('g-recaptcha-response')

        if not first_name or not last_name or not email or not password or not gender or not dob or not recaptcha_response:
            flash("Veuillez remplir tous les champs et valider le CAPTCHA.", "error")
            return redirect(url_for("register"))

        # Vérification du CAPTCHA
        secret_key = "6LfDGRYrAAAAAIE7919oR20thqiKM91YlWvbXMpD"  # Clé secrète de ton reCAPTCHA
        payload = {'secret': secret_key, 'response': recaptcha_response}
        response = requests.post("https://www.google.com/recaptcha/api/siteverify", data=payload)
        result = response.json()

        if not result.get('success'):
            flash("La vérification CAPTCHA a échoué.", "error")
            return redirect(url_for("register"))

        # Tentative d'enregistrement
        success = save_user({
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "password": password,
            "gender": gender,
            "dob": dob
        })

        if not success:
            flash("Cet email est déjà utilisé.", "error")
            return redirect(url_for("register"))

        flash("Inscription réussie ! Vous pouvez maintenant vous connecter.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


# Démarrage
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)