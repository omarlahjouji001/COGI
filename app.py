"""
Flask application for Cogi - Mental Health Companion
All user‑facing strings have been translated from French to English.
"""

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify,
)
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import timedelta, datetime, date
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
import os
import re
import uuid
import requests
import psycopg2
from openai import OpenAI
from dotenv import load_dotenv

# ----------------------------- Configuration -----------------------------

load_dotenv()

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.permanent_session_lifetime = timedelta(minutes=10)

# Together AI API
api_key = os.environ.get("TOGETHER_API_KEY", "").strip()
if not api_key:
    raise ValueError("TOGETHER_API_KEY is missing")
client = OpenAI(api_key=api_key, base_url="https://api.together.xyz/v1")

# Mail configuration (Mailtrap sandbox)
app.config.update(
    MAIL_SERVER="sandbox.smtp.mailtrap.io",
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.environ.get("EMAIL_USER"),
    MAIL_PASSWORD=os.environ.get("EMAIL_PASS"),
)
mail = Mail(app)

s = URLSafeTimedSerializer(app.secret_key)
MAX_ATTEMPTS = 5

# ----------------------------- Utility Functions -----------------------------

def is_strong_password(password: str) -> bool:
    """Return True if the password meets minimal complexity requirements."""
    return bool(
        re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?\":{}|<>]).{8,}$", password)
    )


def get_db_connection():
    return psycopg2.connect(
        dbname="cogi_db", user="mac", password="cogi123", host="localhost", port="5432"
    )


def get_user_by_email(email: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT email, password, first_name, last_name, confirmed, attempts FROM users WHERE email = %s",
        (email.lower(),),
    )
    result = cur.fetchone()
    cur.close()
    conn.close()
    if result:
        return {
            "email": result[0],
            "password": result[1],
            "first_name": result[2],
            "last_name": result[3],
            "confirmed": result[4],
            "attempts": result[5],
        }
    return None


def save_user(data: dict) -> bool:
    """Insert a new user. Returns False if email already exists or on error."""

    email = data.get("email", "").lower()
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT 1 FROM users WHERE email = %s", (email,))
    if cur.fetchone():
        cur.close()
        conn.close()
        return False

    try:
        cur.execute(
            """
            INSERT INTO users (email, password, first_name, last_name, gender, dob, confirmed, attempts)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                email,
                generate_password_hash(data.get("password"), method="pbkdf2:sha256"),
                data.get("first_name"),
                data.get("last_name"),
                data.get("gender"),
                data.get("dob") or None,
                False,
                0,
            ),
        )
        conn.commit()
        return True
    except Exception as exc:
        print("❌ Error saving user:", exc)
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()


def save_message(email: str, message: str, sender: str, session_id: str) -> None:
    print(f"[DB] Saving message: {sender} | {message} | Session: {session_id}")
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO conversations (user_email, message, sender, session_id)
        VALUES (%s, %s, %s, %s)
        """,
        (email, message, sender, session_id),
    )
    conn.commit()
    cur.close()
    conn.close()


def generate_bot_response(user_message: str) -> str:
    try:
        response = client.chat.completions.create(
            model="mistralai/Mistral-7B-Instruct-v0.1",
            messages=[
                {"role": "system", "content": "You are a helpful mental‑health assistant."},
                {"role": "user", "content": user_message},
            ],
            max_tokens=200,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        print("AI API error:", exc)
        return "⚠️ I couldn't generate a response right now."

# ----------------------------- Routes -----------------------------

@app.route("/")
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT name, message, submitted_at FROM feedback ORDER BY id DESC LIMIT 10")
    feedbacks = [
        {"name": row[0], "message": row[1], "submitted_at": row[2]} for row in cur.fetchall()
    ]
    cur.close()
    conn.close()
    return render_template("index.html", feedbacks=feedbacks)


@app.route("/chat", methods=["GET", "POST"])
def chat():
    if "user" not in session:
        flash("Session expired, please log in again.", "danger")
        return redirect(url_for("login"))

    email = session["user"]
    user_data = get_user_by_email(email)

    # Handle session switching / creation
    if request.args.get("session_id"):
        session["session_id"] = request.args.get("session_id")
    if request.args.get("new") or "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())

    current_session_id = session["session_id"]

    if request.method == "POST":
        user_message = request.form.get("message")
        if user_message:
            bot_reply = generate_bot_response(user_message)
            save_message(email, user_message, "user", current_session_id)
            save_message(email, bot_reply, "bot", current_session_id)

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT session_id, MIN(timestamp) AS timestamp
        FROM conversations
        WHERE user_email = %s
        GROUP BY session_id
        ORDER BY timestamp DESC
        """,
        (email,),
    )
    session_rows = cur.fetchall()

    sessions = []
    for sid, ts in session_rows:
        cur.execute(
            "SELECT title FROM conversations WHERE session_id = %s AND title IS NOT NULL ORDER BY timestamp LIMIT 1",
            (sid,),
        )
        title_row = cur.fetchone()
        title = title_row[0] if title_row else None
        sessions.append({"id": sid, "timestamp": ts, "title": title})

    cur.execute(
        """
        SELECT message, sender, timestamp
        FROM conversations
        WHERE user_email = %s AND session_id = %s
        ORDER BY timestamp ASC
        """,
        (email, current_session_id),
    )
    history = cur.fetchall()
    cur.close()
    conn.close()

    return render_template(
        "chat.html",
        username=email,
        first_name=user_data.get("first_name", ""),
        last_name=user_data.get("last_name", ""),
        history=history,
        sessions=sessions,
        active_id=current_session_id,
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if not username or not password:
            flash("Username and password are required!", "danger")
            return redirect(url_for("login"))

        user_data = get_user_by_email(username)
        if not user_data:
            flash("Unknown user.", "error")
            return redirect(url_for("login"))

        if not user_data.get("confirmed"):
            flash("Please confirm your email before logging in.", "danger")
            return redirect(url_for("login"))

        if user_data["attempts"] >= MAX_ATTEMPTS:
            flash("Too many failed attempts. Try again later.", "error")
            return redirect(url_for("login"))

        if not check_password_hash(user_data["password"], password):
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("UPDATE users SET attempts = attempts + 1 WHERE email = %s", (username,))
            conn.commit()
            cur.close()
            conn.close()
            flash("Incorrect username or password.", "error")
            return redirect(url_for("login"))

        # Reset attempt counter
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE users SET attempts = 0 WHERE email = %s", (username,))
        conn.commit()
        cur.close()
        conn.close()

        session.permanent = True
        session["user"] = username
        return redirect(url_for("chat"))

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Collect form data
        form_data = {k: request.form.get(k) for k in [
            "first_name",
            "last_name",
            "email",
            "password",
            "gender",
            "dob",
        ]}
        recaptcha_response = request.form.get("g-recaptcha-response")

        if not all(form_data.values()) or not recaptcha_response:
            flash("Please fill in all fields and complete the CAPTCHA verification.", "error")
            return redirect(url_for("register"))

        # CAPTCHA verification
        captcha_payload = {
            "secret": os.environ.get("RECAPTCHA_SECRET"),
            "response": recaptcha_response,
        }
        captcha_ok = requests.post(
            "https://www.google.com/recaptcha/api/siteverify", data=captcha_payload
        ).json()
        if not captcha_ok.get("success"):
            flash("CAPTCHA verification failed.", "error")
            return redirect(url_for("register"))

        # DOB validation
        try:
            dob = date.fromisoformat(form_data["dob"])
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if dob > today:
                flash("Date of birth cannot be in the future.", "error")
                return redirect(url_for("register"))
            if age < 13:
                flash("You must be at least 13 years old to register.", "error")
                return redirect(url_for("register"))
            if age > 100:
                flash("Please enter a realistic date of birth (under 100 years old).", "error")
                return redirect(url_for("register"))
        except ValueError:
            flash("Invalid date format for date of birth.", "error")
            return redirect(url_for("register"))

        # Password strength
        if not is_strong_password(form_data["password"]):
            flash("Password is too weak.", "error")
            return redirect(url_for("register"))

        # Save user
        if not save_user(form_data):
            flash("This email is already registered.", "error")
            return redirect(url_for("register"))

        # Send confirmation e‑mail
        token = s.dumps(form_data["email"], salt="email-confirm")
        link = url_for("confirm_email", token=token, _external=True)

        msg = Message(
            "Confirm your email address",
            sender=app.config["MAIL_USERNAME"],
            recipients=[form_data["email"]],
        )
        msg.body = f"Welcome to Cogi! Click here to confirm your address: {link}"
        mail.send(msg)

        flash("Registration successful! Please check your email to activate your account.", "success")
        return redirect(url_for("login"))

    # GET
    return render_template("register.html", current_date=date.today())


@app.route("/confirm/<token>")
def confirm_email(token):
    try:
        email = s.loads(token, salt="email-confirm", max_age=3600)
    except (SignatureExpired, BadSignature):
        flash("Invalid or expired link.", "danger")
        return redirect(url_for("register"))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET confirmed = TRUE WHERE email = %s", (email.lower(),))
    conn.commit()
    cur.close()
    conn.close()

    flash("Email confirmed. You can now log in.", "success")
    return redirect(url_for("login"))


@app.route("/reset_request", methods=["POST"])
def reset_request():
    email = request.form.get("email")
    user = get_user_by_email(email)
    if not user:
        return jsonify({"status": "error", "message": "No account associated with this email."}), 404

    token = s.dumps(email, salt="reset-password")
    reset_link = url_for("reset_token", token=token, _external=True)

    msg = Message("Password reset", sender=app.config["MAIL_USERNAME"], recipients=[email])
    msg.body = f"Click here to reset your password: {reset_link}"

    try:
        mail.send(msg)
        return jsonify({"status": "success", "message": "Link sent to your email address."})
    except Exception as exc:
        print("Error sending email:", exc)
        return jsonify({"status": "error", "message": "Error sending email."}), 500


@app.route("/reset/<token>", methods=["GET", "POST"])
def reset_token(token):
    try:
        email = s.loads(token, salt="reset-password", max_age=3600)
    except (SignatureExpired, BadSignature):
        flash("Invalid or expired link.", "danger")
        return redirect(url_for("login"))

    if request.method == "POST":
        password = request.form.get("password")
        confirm = request.form.get("confirm")

        if password != confirm:
            flash("Passwords do not match.", "error")
            return render_template("reset_token.html", token=token)

        if not is_strong_password(password):
            flash("Password is too weak.", "error")
            return render_template("reset_token.html", token=token)

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "UPDATE users SET password = %s WHERE email = %s",
            (generate_password_hash(password, method="pbkdf2:sha256"), email),
        )
        conn.commit()
        cur.close()
        conn.close()

        flash("Password reset successful. You can now log in.", "success")
        return redirect(url_for("login"))

    return render_template("reset_token.html", token=token)


@app.route("/send_message", methods=["POST"])
def send_message():
    if "user" not in session:
        return jsonify({"reply": "Not authenticated"}), 401

    user_input = request.json.get("message", "")
    session_id = session.get("session_id")

    if not user_input.strip():
        return jsonify({"reply": "❌ Empty message"}), 400

    try:
        response = client.chat.completions.create(
            model="mistralai/Mistral-7B-Instruct-v0.1",
            messages=[
                {"role": "system", "content": "You are a helpful mental‑health assistant."},
                {"role": "user", "content": user_input},
            ],
            max_tokens=200,
            temperature=0.7,
        )
        reply = response.choices[0].message.content.strip()

        save_message(session["user"], user_input, "user", session_id)
        save_message(session["user"], reply, "bot", session_id)

        return jsonify({"reply": reply})
    except Exception as exc:
        print("Server error:", exc)
        return jsonify({"reply": f"⚠️ Server error: {exc}"}), 500


@app.route("/feedback", methods=["GET", "POST"])
def feedback():
    if "user" not in session:
        flash("You must be logged in to send feedback.", "warning")
        return redirect(url_for("login"))

    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == "POST":
        name = request.form.get("name")
        message = request.form.get("message")

        if not name or not message:
            flash("Both name and message are required.", "error")
            return redirect(url_for("index"))

        try:
            cur.execute("INSERT INTO feedback (name, message) VALUES (%s, %s)", (name, message))
            conn.commit()
            flash("✅ Feedback sent successfully!", "success")
        except Exception as exc:
            conn.rollback()
            flash(f"Error submitting feedback: {exc}", "error")

        cur.close()
        conn.close()
        return redirect(url_for("index"))

    # GET – list feedback
    cur.execute("SELECT name, message, submitted_at FROM feedback ORDER BY submitted_at DESC")
    feedbacks = cur.fetchall()
    cur.close()
    conn.close()
    return render_template(
        "feedback.html",
        feedbacks=[{"name": r[0], "message": r[1], "submitted_at": r[2]} for r in feedbacks],
    )


@app.route("/rename_chat", methods=["POST"])
def rename_chat():
    chat_id = request.form.get("chat_id")
    new_title = request.form.get("new_title", "").strip()
    if not new_title:
        flash("Title cannot be empty.", "warning")
        return redirect(url_for("chat", session_id=chat_id))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE conversations SET title = %s WHERE session_id = %s", (new_title, chat_id))
    conn.commit()
    cur.close()
    conn.close()

    flash("✅ Chat renamed successfully.", "success")
    return redirect(url_for("chat", session_id=chat_id))


@app.route("/delete_chat", methods=["POST"])
def delete_chat():
    chat_id = request.form.get("chat_id")
    if not chat_id:
        flash("Invalid delete request.", "danger")
        return redirect(url_for("chat"))

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM conversations WHERE session_id = %s", (chat_id,))
        conn.commit()
    except Exception as exc:
        flash(f"Delete failed: {exc}", "danger")
    finally:
        cur.close()
        conn.close()
    return redirect(url_for("chat"))


# ----------------------------- Context / Filters -----------------------------

@app.context_processor
def inject_user_info():
    if "user" in session:
        user_data = get_user_by_email(session["user"])
        if user_data:
            return {
                "first_name": user_data.get("first_name", ""),
                "last_name": user_data.get("last_name", ""),
            }
    return {"first_name": "", "last_name": ""}


# ----------------------------- Session Management -----------------------------

@app.before_request
def check_session_timeout():
    if "user" in session:
        session.modified = True
        now = datetime.utcnow()
        last_activity = session.get("last_activity")
        if last_activity:
            elapsed = now - datetime.fromisoformat(last_activity)
            if elapsed > app.permanent_session_lifetime:
                print("[DEBUG] Session expired")
                flash("Session expired due to inactivity.", "warning")
                session.clear()
                print("[DEBUG] Redirecting to login after expiration")
                return redirect(url_for("login"))
        session["last_activity"] = now.isoformat()


# ----------------------------- Miscellaneous -----------------------------

@app.route("/mission")
def mission():
    return render_template("mission.html")


@app.route("/subscribe", methods=["POST"])
def subscribe():
    email = request.form.get("email", "").strip().lower()
    if not email or "@" not in email:
        flash("Invalid email address.", "danger")
        return redirect(url_for("index"))

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO subscriber (email) VALUES (%s) ON CONFLICT DO NOTHING",
            (email,),
        )
        conn.commit()
        flash("Thanks for subscribing!", "success")
    except Exception as exc:
        print("❌ Error saving subscription:", exc)
        flash("Something went wrong. Please try again.", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("index"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
