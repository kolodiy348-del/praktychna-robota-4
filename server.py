"""Навчальний Flask-сервер: SQLite, REST API та захищена сторінка повідомлень."""
import os
import re
import sqlite3
import hmac
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from functools import wraps
from flask import Flask, request, jsonify, session, redirect, render_template_string, send_from_directory

BASE = Path(__file__).resolve().parent
DB = BASE / "messages.db"
app = Flask(__name__, static_folder=None)
app.secret_key = os.environ.get("SECRET_KEY", "local-coursework-session-key-change-me")
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
if not app.debug and not app.logger.handlers:
    handler = RotatingFileHandler(BASE / "server_errors.log", maxBytes=250_000, backupCount=2, encoding="utf-8")
    handler.setLevel(logging.ERROR)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    app.logger.addHandler(handler)

@app.errorhandler(500)
def internal_error(error):
    app.logger.exception("Server error: %s", error)
    return jsonify(error="Внутрішня помилка сервера."), 500


def connect():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    with connect() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS messages (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL, email TEXT NOT NULL, message TEXT NOT NULL,
          created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )""")

@app.get("/")
def home():
    return send_from_directory(BASE, "index.html")

@app.get("/<path:filename>")
def assets(filename):
    if filename not in {"styles.css", "script.js", "images/developer.svg"}:
        return "Not found", 404
    return send_from_directory(BASE, filename)

@app.post("/api/messages")
def create_message():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error="Очікується JSON-об'єкт."), 400
    name, email, message = (str(data.get(k, "")).strip() for k in ("name", "email", "message"))
    if not 2 <= len(name) <= 100:
        return jsonify(error="Ім’я: від 2 до 100 символів."), 400
    if len(email) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        return jsonify(error="Некоректна електронна адреса."), 400
    if not 5 <= len(message) <= 3000:
        return jsonify(error="Повідомлення: від 5 до 3000 символів."), 400
    with connect() as db:
        cur = db.execute("INSERT INTO messages (name,email,message) VALUES (?,?,?)", (name,email,message))
        msg_id = cur.lastrowid
    return jsonify(id=msg_id, success=True), 201

def admin_only(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not session.get("admin"):
            return jsonify(error="Потрібна авторизація."), 401
        return fn(*args, **kwargs)
    return wrapped

@app.get("/api/messages")
@admin_only
def list_messages():
    with connect() as db:
        rows = db.execute("SELECT id,name,email,message,created_at FROM messages ORDER BY id DESC LIMIT 200").fetchall()
    return jsonify([dict(row) for row in rows])

@app.delete("/api/messages/<int:message_id>")
@admin_only
def delete_message(message_id):
    with connect() as db:
        cur = db.execute("DELETE FROM messages WHERE id=?", (message_id,))
        found = cur.rowcount
    return (jsonify(success=True) if found else (jsonify(error="Не знайдено."),404))

LOGIN = """<!doctype html><html lang="uk"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Вхід адміністратора</title><link rel="stylesheet" href="/styles.css"><main class="admin-wrap"><h1>Вхід адміністратора</h1><p>Повідомлення доступні лише після входу.</p><form method="post" action="/login"><label>Пароль <input name="password" type="password" required></label><button class="button button-primary">Увійти</button></form><p>{{ error }}</p><a href="/">← На головну</a></main></html>"""
PANEL = """<!doctype html><html lang="uk"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Повідомлення</title><link rel="stylesheet" href="/styles.css"><main class="admin-wrap"><h1>Збережені повідомлення</h1><p><a href="/">← На сайт</a> · <a href="/logout">Вийти</a></p><p id="status" role="status"></p><div id="messages"></div></main><script>
async function load(){const r=await fetch('/api/messages');if(!r.ok){document.querySelector('#status').textContent='Помилка завантаження';return}const items=await r.json();const box=document.querySelector('#messages');box.replaceChildren();document.querySelector('#status').textContent='Кількість повідомлень: '+items.length;for(const m of items){const card=document.createElement('article');card.className='admin-message';const h=document.createElement('h2');h.textContent=m.name+' — '+m.email;const p=document.createElement('p');p.textContent=m.message;const date=document.createElement('small');date.textContent=m.created_at+' UTC · ID '+m.id;const b=document.createElement('button');b.className='button button-primary';b.textContent='Видалити';b.addEventListener('click',async()=>{if(!confirm('Видалити повідомлення?'))return;const r=await fetch('/api/messages/'+m.id,{method:'DELETE'});if(r.ok)load();else alert('Помилка видалення')});card.append(h,p,date,b);box.append(card)}}load();
</script></html>"""

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        password = request.form.get("password", "")
        if ADMIN_PASSWORD and hmac.compare_digest(password, ADMIN_PASSWORD):
            session.clear()
            session["admin"] = True
            return redirect("/messages")
        return render_template_string(LOGIN, error="Невірний пароль або ADMIN_PASSWORD не налаштовано."), 401
    return render_template_string(LOGIN, error="")

@app.get("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.get("/messages")
def messages_page():
    if not session.get("admin"):
        return redirect("/login")
    return render_template_string(PANEL)

if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5000, debug=False)
