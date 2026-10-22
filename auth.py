# -*- coding: utf-8 -*-
"""
Kullanıcı hesapları ve kullanıcı başına hisse takip listesi.

SQLite (stdlib sqlite3) kullanır — yeni bir bağımlılık gerekmez. Hisse
verisinin kendisi (fiyat/gösterge/haber/AI) hâlâ paylaşımlı `cache.json`'da
tutulur (bkz. data_cache.py); burada sadece "hangi kullanıcı hangi hisseyi
takip ediyor" ilişkisi ve kullanıcı kimlik bilgileri saklanır.
"""

import json
import os
import sqlite3
from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from config import DB_FILE, DEFAULT_TICKERS, TICKERS_FILE


class User(UserMixin):
    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email

    def get_id(self):
        return str(self.id)


def _get_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_tickers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            ticker TEXT NOT NULL,
            UNIQUE(user_id, ticker)
        )
    """)
    conn.commit()
    conn.close()


def _row_to_user(row) -> User:
    return User(row["id"], row["username"], row["email"])


def get_user_by_id(user_id) -> User:
    conn = _get_conn()
    row = conn.execute("SELECT id, username, email FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return _row_to_user(row) if row else None


def get_user_by_username(username: str) -> User:
    conn = _get_conn()
    row = conn.execute("SELECT id, username, email FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return _row_to_user(row) if row else None


def verify_password(username: str, password: str) -> User:
    """Kullanıcı adı/şifre doğruysa User döner, değilse None."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT id, username, email, password_hash FROM users WHERE username = ?", (username,)
    ).fetchone()
    conn.close()
    if not row or not check_password_hash(row["password_hash"], password):
        return None
    return User(row["id"], row["username"], row["email"])


def _seed_tickers_for_new_user() -> list:
    """
    İlk kayıt olan kullanıcı mevcut tickers.json içeriğini (varsa) devralır;
    sonraki her kullanıcı DEFAULT_TICKERS ile boş olmayan bir listeyle başlar.
    """
    conn = _get_conn()
    is_first_user = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0
    conn.close()

    if is_first_user and os.path.exists(TICKERS_FILE):
        try:
            with open(TICKERS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list) and data:
                return data
        except (json.JSONDecodeError, OSError):
            pass

    return list(DEFAULT_TICKERS)


def create_user(username: str, email: str, password: str) -> User:
    """Yeni kullanıcı oluşturur. Kullanıcı adı doluysa None döner."""
    conn = _get_conn()
    existing = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    if existing:
        conn.close()
        return None

    password_hash = generate_password_hash(password)
    seed_tickers = _seed_tickers_for_new_user()

    cur = conn.execute(
        "INSERT INTO users (username, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
        (username, email, password_hash, datetime.now().strftime("%Y-%m-%d %H:%M")),
    )
    user_id = cur.lastrowid
    for ticker in seed_tickers:
        conn.execute(
            "INSERT OR IGNORE INTO user_tickers (user_id, ticker) VALUES (?, ?)",
            (user_id, ticker),
        )
    conn.commit()
    conn.close()
    return User(user_id, username, email)


def get_user_tickers(user_id) -> list:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT ticker FROM user_tickers WHERE user_id = ? ORDER BY id", (user_id,)
    ).fetchall()
    conn.close()
    return [r["ticker"] for r in rows]


def add_user_ticker(user_id, ticker: str) -> bool:
    ticker = ticker.strip().upper()
    if not ticker:
        return False
    conn = _get_conn()
    existing = conn.execute(
        "SELECT id FROM user_tickers WHERE user_id = ? AND ticker = ?", (user_id, ticker)
    ).fetchone()
    if existing:
        conn.close()
        return False
    conn.execute("INSERT INTO user_tickers (user_id, ticker) VALUES (?, ?)", (user_id, ticker))
    conn.commit()
    conn.close()
    return True


def remove_user_ticker(user_id, ticker: str) -> bool:
    ticker = ticker.strip().upper()
    conn = _get_conn()
    cur = conn.execute("DELETE FROM user_tickers WHERE user_id = ? AND ticker = ?", (user_id, ticker))
    conn.commit()
    conn.close()
    return cur.rowcount > 0


def get_all_tracked_tickers() -> list:
    """Tüm kullanıcıların birleşik (union) hisse listesi — günlük pipeline,
    fiyat yenileme ve Telegram bot bunu kullanır."""
    conn = _get_conn()
    rows = conn.execute("SELECT DISTINCT ticker FROM user_tickers ORDER BY ticker").fetchall()
    conn.close()
    return [r["ticker"] for r in rows]
