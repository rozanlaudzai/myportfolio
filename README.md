# PBP UI Task

## Author

- Nama: Rozan Laudzai
- NPM: 2506547544
- Kelas: PBP B

## Overview

A personal portfolio website built with Django.

## Environments

### Development

- Ubuntu
- VS Code and Prettier
- Python 3.12.3

### Production

- Pacil Web Service (does not support uv, bruh)

## Deployment

https://rozan-laudzai-myportfolio.pws.cs.ui.ac.id/

## Local Setup

1. Create and activate a virtual environment:

```bash
python3 -m venv .venv

source .venv/bin/activate
```

2. Install dependencies:

```bash
python3 -m pip install -r requirements.txt
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

4. Run the following command

```bash
python3 manage.py runserver
```

5. Open `http://127.0.0.1:8000` on your browser.

## Pertanyaan Reflektif

### Tugas 1

1. Saya menggunakan `<section>` untuk membagi halaman menjadi beberapa sections berdasarkan topiknya, misalnya profile dan experience. Sementara `<article>`, saya gunakan untuk wrap content yang bisa dianggap satu kesatuan, misalnya satu experience.

2. Saya sempat sadar ketika tampilan diubah ke mobile, wrapper size dari logo lebih kecil daripada logonya itu sendiri. Solusinya adalah dengan menambah `object-fit: contain` pada setiap `<img>` logo dan membuat `@media` untuk memperkecil logo size ketika di mobile.

3. Batasan yang paling saya rasakan di static web adalah saya harus hard-code semua informasi yang disajikan. Ketika saya ingin mengubah css style pada suatu list, maka saya harus mengubah css style dari semua konten di list tersebut. Kedepannya, saya ingin memasukkan segala informasi (e.g. experience, skills, awards) ke dalam database lalu me-render itu semua melalui Django Template Language.

### Tugas 2

1. User membuat request GET ke certain URL pada web kita, lalu Django akan mencocokkan request URL dengan routes yang sudah ada di project's `urls.py`. Karena terdapat app's `urls.py` yang included di project's `urls.py`, maka routes dari app tersebut juga akan dicocokkan dengan URL di request. Ketika sudah terdapat route yang cocok, maka Django akan menjalankan view function yang terikat dengannya. Di view itulah terdapat logic-logic yang penting seperti ambil data di db menggunakan models, fetch API dari luar, sorting, etc. Setelah semua logic itu selesai, biasanya view functions akan return render html yang biasa disebut template, karena memakai Django template engine/Jinja. Kalau ditanya apa perannya models, models itu berguna sebagai ORM database sehingga mempercepat proses dev. Honestly, saya tidak suka memakai ORM karena menambah hafalan. Kalau ditanya apa perannya template, ya untuk mempermudah dalam perenderan objects dari python.

2. Mengurangi redundansi, contohnya ketika kita membuat list, kita cukup membuat styling-nya sekali saja untuk semua isi list tersebut. Selain itu, agar datanya dapat disalurkan ke templates lain dengan mudah.

3. `makemigrations` untuk mencatat migrations dalam file python (belum applied ke db) di folder `/migrations`. `migrate` membaca files di `/migrations` untuk di-execute di db.

## AI Disclosure

Sejauh ini, saya memakai Codex GPT-6 Astra untuk:

- Improve dokumentasi di `README.md` yang telah saya tulis.
- CSS styling untuk experience section: responsive logo size, experience timeline, etc.
- Bertanya apa perbedaan `<section>`, `<article>`, dan `<aside>`.
- Assignment 1's chat link: https://chatgpt.com/s/cx_6a9e91d814408191b0ad0bf551234c43
- Membuat awards HTML page sesuai dengan the other page patterns serta melakukan CSS styling-nya.
- Add tests for award
- Update tests for current experience model
- Assignment 2's chat link: https://chatgpt.com/s/cx_6aa823ffd7708191affbf11337d3726b
