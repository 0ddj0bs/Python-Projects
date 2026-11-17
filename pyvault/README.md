# 🔐 Pyvault — Secure Local Secret Manager

**Pyvault** is a lightweight, secure command-line password and API key manager built in Python. Designed with zero cloud dependencies, it keeps your sensitive credentials encrypted locally using industry-standard cryptography, backed by a clean, interactive terminal UI powered by [Rich](https://github.com/Textualize/rich) and automated clipboard integration.

---

## 🚀 Features

* **Military-Grade Encryption:** Protects your secrets using symmetric authenticated encryption (`Fernet` / AES-128-CBC) combined with secure key derivation (`PBKDF2-HMAC-SHA256`).
* **Zero-Knowledge Architecture:** Your master password never leaves your machine. A cryptographically secure random salt is generated per vault instance and stored locally to defend against rainbow table attacks.
* **Instant Clipboard Copying:** Automatically copies retrieved passwords directly to your system clipboard using `pyperclip` for fast, frictionless pasting.
* **Local SQLite Storage:** All encrypted records are persisted safely in a local `vault.db` SQLite database.
* **Rich Terminal Interface:** Clean, color-coded tables, status panels, and intuitive prompt flows.

---

## 🛡️ Cryptographic Design

Pyvault prioritizes security at every layer of data handling:

1. **Key Derivation (PBKDF2):** 
   When you input your Master Password, Pyvault combines it with a cryptographically secure 16-byte random `salt` stored in the database. It derives a 256-bit encryption key using **PBKDF2-HMAC-SHA256** with high iteration counts to mitigate brute-force and dictionary attacks.
2. **Authenticated Encryption (Fernet):** 
   Secrets are encrypted using **Fernet**, which guarantees that a message encrypted cannot be read or tampered with without the master key. It uses 128-bit AES in CBC mode with PKCS7 padding and HMAC-SHA256 for authentication.
3. **Memory Safety:** 
   Master passwords are handled via Python's `getpass` module to ensure they are never echoed back to the terminal or logged in command-line history.

---

## 📁 Project Structure

```text
pyvault/
│
├── src/
│   ├── __init__.py
│   ├── crypto.py      # PBKDF2 key derivation and Fernet encryption logic
│   ├── database.py    # SQLite schema initialization and CRUD operations
│   └── main.py        # CLI interactive loop and Rich dashboard
│
├── requirements.txt   # Project dependencies
└── README.md          # Documentation
