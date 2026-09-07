# PBP UI Task

## Author

- Nama: Rozan Laudzai
- NPM: 2506547544
- Kelas: PBP B

## Overview

This project is a personal portfolio website built with Django.

## Tech Stack

- Django
- Tailwind CSS

## Environments

### Development

- Ubuntu
- VS Code and Prettier
- Python 3.12.3
- Node.js 22.18.0
- npm 11.19.1

### Production

- Pacil Web Service (does not support uv, bruh)

## Local Setup

1. Create and activate a virtual environment:

```bash
python3 -m venv .venv

source .venv/bin/activate
```

2. Install the Python and Node.js dependencies:

```bash
python3 -m pip install -r requirements.txt

npm install
```

3. Create a `.env` file:

```
DB_USER
DB_PASSWORD
DB_HOST
DB_PORT
DB_NAME
MY_DOMAIN
PRODUCTION
SCHEMA
SECRET_KEY
```

Local development uses SQLite by default. PostgreSQL is used when `PRODUCTION=True`. In that case, also configure `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, and `DB_NAME` in `.env`.

4. Run the following commands in separate terminals:

```bash
npx @tailwindcss/cli -i ./static/css/tailwind-input.css -o ./static/css/tailwind-output.css --watch
```

```bash
python3 manage.py runserver
```

## AI Disclosure

Sejauh ini, saya memakai Codex GPT-6 Astra untuk:

- Improve dokumentasi di `README.md` yang telah saya tulis.
- CSS styling untuk experience section: responsive logo size, experience timeline, etc.
- Bertanya apa perbedaan `<section>`, `<article>`, dan `<aside>`.
- Tautan chat Tugas 1: https://chatgpt.com/s/cx_6a9e91d814408191b0ad0bf551234c43
