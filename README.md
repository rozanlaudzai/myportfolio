# PBP UI Task

## Author

- Nama: Rozan Laudzai
- NPM: 2506547544
- Kelas: PBP B

## Overview

A personal portfolio website built with Django as part of the PBP course at Universitas Indonesia.

## Deployment

https://rozan-laudzai-myportfolio.pws.cs.ui.ac.id/

## Environments

### Development

- Ubuntu
- VS Code and Prettier
- Python 3.12.3

### Production

- Pacil Web Service (does not support uv, bruh)

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
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=
DB_NAME=
MY_DOMAIN=
PRODUCTION=
SCHEMA=
SECRET_KEY=
```

Local development uses SQLite by default. PostgreSQL is used when `PRODUCTION=True`. In that case, also configure `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, and `DB_NAME` in `.env`.

4. Apply database migrations

```bash
python3 manage.py migrate
```

5. Start the development server

```bash
python3 manage.py runserver
```

Open `http://127.0.0.1:8000` on your browser.

## Testing

Run the test suite with coverage:

```bash
coverage run --source='.' manage.py test main
```

View the coverage report:

```bash
coverage report
```

## Tutorial 07: Django REST Framework

Tutorial Projects is adapted to this portfolio's existing **Award** model and
`main/templates/main/awards.html`. No new Project model or database is needed.
Experience and the previous HTML forms and JSON endpoints remain available.

The award serializer exposes `id`, `title`, `issuer`, `description`, `awarded_at`,
`star_count`, `is_starred`, and `starred_by_names`. Responses use flat objects,
without the legacy `pk`/`fields` wrapper. Text fields strip HTML and reject empty
values; `awarded_at` must be a valid date. IDs and computed star fields are read-only.

| Method      | Endpoint                      | Access                                 |
| ----------- | ----------------------------- | -------------------------------------- |
| GET / HEAD  | `/api/v1/awards/`             | Public; `?title=...` searches titles   |
| POST        | `/api/v1/awards/`             | Superuser; returns 201                 |
| GET / HEAD  | `/api/v1/awards/<uuid>/`      | Public                                 |
| PUT / PATCH | `/api/v1/awards/<uuid>/`      | Superuser or member of `Editor`        |
| DELETE      | `/api/v1/awards/<uuid>/`      | Superuser; returns empty 204           |
| POST        | `/api/v1/awards/<uuid>/star/` | Logged-in user; toggles their own star |

Awards uses the DRF endpoints for AJAX listing, creation, starring and deletion.
The add and delete confirmation popovers, toast messages, 300 ms search debounce,
stale request cancellation, and HTML escaping are preserved. Edit links still
open the existing prefilled HTML form. API updates are also available through
PUT/PATCH; PATCH only needs the changed fields, while PUT requires all four
editable fields. Search remains active after writes.

SessionAuthentication reuses website login. Every API write from a logged-in
session requires a CSRF token, including star. The Awards page sets the CSRF
cookie for visitors who do not have the add form. Guest star links lead to login.
Permissions are enforced by the API as well as the UI; staff status alone does
not grant write access.

Run the API tests, all Django tests, and frontend regression tests:

```bash
python manage.py check
python manage.py test main.tests_api --verbosity 2
python manage.py test main
node --test tests/awards.test.cjs tests/experience.test.cjs
python manage.py makemigrations --check --dry-run
python manage.py migrate --check
```

There are 13 award API test methods, including real session/CSRF checks and the
Editor role, plus frontend tests for escaping, search cancellation, JSON writes,
CSRF headers, error responses and DELETE 204. The permission regression test was
also checked by temporarily permitting authenticated visitors to write: it failed
as expected, and the original permission was restored.

For PWS deployment, install the committed requirements and use the existing
deployment workflow. Set `MY_DOMAIN` to the deployment hostname (without scheme)
so `CSRF_TRUSTED_ORIGINS` matches its HTTPS origin. After deploying, check public
reading, login, and a write operation on the deployed site. Local tests do not
verify the deployed service. Keep `.env`, the local database, credentials and
virtual environments out of Git.

## Tugas 6: Experience REST API

Bagian mandiri adalah **Experience**, sedangkan Award tetap menjadi implementasi
Tutorial 07. Data Experience dan Skill lama digunakan kembali. Migrasi 0009
menambahkan relasi star tanpa menghapus data yang ada.

| Method      | Endpoint                           | Hak akses                                  |
| ----------- | ---------------------------------- | ------------------------------------------ |
| GET / HEAD  | `/api/v1/experiences/`             | Semua peran; pencarian `?title=...`        |
| POST        | `/api/v1/experiences/`             | Superuser (201)                            |
| GET / HEAD  | `/api/v1/experiences/<uuid>/`      | Semua peran                                |
| PUT / PATCH | `/api/v1/experiences/<uuid>/`      | Editor dan superuser                       |
| DELETE      | `/api/v1/experiences/<uuid>/`      | Superuser (204, body kosong)               |
| POST        | `/api/v1/experiences/<uuid>/star/` | Akun login; toggle star milik request.user |

Field respons: `id`, `title`, `company_name`, `company_logo`, `description`,
`started_at`, `ended_at`, `skills` (array nama), `star_count`, dan `is_starred`.
ID dan kedua field star read-only; email/password/daftar akun tidak diekspos.
Kesalahan validasi memakai 400, penolakan akses 403, objek tidak ada 404.
Tanggal akhir boleh null (masih berlangsung), tetapi tidak boleh sebelum tanggal
mulai, termasuk saat PATCH hanya mengubah salah satu tanggal. Nama skill
membersihkan HTML, menghapus duplikat tanpa membedakan kapital, dan memakai
kembali Skill lama. PATCH tanpa `skills` mempertahankan relasi skill.

Contoh payload POST atau PUT:

```json
{
  "title": "Developer",
  "company_name": "Universitas Indonesia",
  "company_logo": "",
  "description": "Mengembangkan aplikasi portofolio",
  "started_at": "2026-01-01",
  "ended_at": null,
  "skills": ["Python", "Django"]
}
```

Contoh PATCH: `{"description": "Deskripsi baru"}`. PUT memerlukan semua field
teks wajib dan `started_at`; field opsional mengikuti default DRF/model.

Halaman `/experience/` memakai fetch untuk seluruh aksi tanpa reload, modal
prefill untuk Editor/pemilik, konfirmasi hapus, loading/empty/error state,
debounce 300 ms, serta pembatalan pencarian lama. Filter aktif dipertahankan
setelah write. Error API ditampilkan sebagai toast dengan teks aman. Semua
write mengirim X-CSRFToken; cookie juga tersedia bagi pengguna biasa dan Editor.
Nilai teks di HTML di-escape dan URL logo dibatasi ke HTTP/HTTPS. View HTML lama
masih tersedia: hanya superuser dapat create/delete dan Editor dapat edit.

Setelah menarik perubahan, jalankan dari virtual environment:

```bash
python manage.py migrate
python manage.py check
python manage.py test main
node --test tests/awards.test.cjs tests/experience.test.cjs
python manage.py makemigrations --check --dry-run
python manage.py runserver
```

Buat akun pemilik dengan `python manage.py createsuperuser`. Buat grup **Editor**
melalui admin, lalu tambahkan akun yang boleh mengedit. Akun terdaftar biasa
hanya dapat membaca dan star. Browsable API tersedia di `/api/v1/experiences/`
dan `/api/v1/awards/`; login tersedia melalui `/api-auth/login/`.

Validasi otomatis: 68 test Django (termasuk 13 test API Award dan 8 test API
Experience), serta regression test JavaScript untuk kedua halaman. Test penolakan
memeriksa database; test CSRF memakai login nyata, menolak write tanpa token,
dan menerima request dengan token. Tidak perlu menjalankan Selenium test lama:
gunakan `test main` sesuai petunjuk tugas.

Smoke test Chromium dengan runserver dan database sementara juga lulus untuk
halaman publik, Browsable API, create/search/star/edit/delete pemilik, PATCH
Editor, dan star pengguna biasa, tanpa error JavaScript. Data asli tidak dipakai
untuk percobaan write. Deployment PWS dan submisi SCELE tetap perlu diverifikasi
terpisah. Riwayat lokal mencatat merge Tutorial 07 pada 4 November 2026 pukul
23:36:58 WIB (`c797539`); waktu push/pengumpulannya tidak dapat disimpulkan dari
waktu commit saja.

## Pertanyaan Reflektif

### Tugas 1

1. Saya menggunakan `<section>` untuk membagi halaman menjadi beberapa sections berdasarkan topiknya, misalnya profile dan experience. Sementara `<article>`, saya gunakan untuk wrap content yang bisa dianggap satu kesatuan, misalnya satu experience.

2. Saya sempat sadar ketika tampilan diubah ke mobile, wrapper size dari logo lebih kecil daripada logonya itu sendiri. Solusinya adalah dengan menambah `object-fit: contain` pada setiap `<img>` logo dan membuat `@media` untuk memperkecil logo size ketika di mobile.

3. Batasan yang paling saya rasakan di static web adalah saya harus hard-code semua informasi yang disajikan. Ketika saya ingin mengubah css style pada suatu list, maka saya harus mengubah css style dari semua konten di list tersebut. Kedepannya, saya ingin memasukkan segala informasi (e.g. experience, skills, awards) ke dalam database lalu me-render itu semua melalui Django Template Language.

### Tugas 2

1. User membuat request GET ke certain URL pada web kita, lalu Django akan mencocokkan request URL dengan routes yang sudah ada di project's `urls.py`. Karena terdapat app's `urls.py` yang included di project's `urls.py`, maka routes dari app tersebut juga akan dicocokkan dengan URL di request. Ketika sudah terdapat route yang cocok, maka Django akan menjalankan view function yang terikat dengannya. Di view itulah terdapat logic-logic yang penting seperti ambil data di db menggunakan models, fetch API dari luar, sorting, etc. Setelah semua logic itu selesai, biasanya view functions akan return render html yang biasa disebut template, karena memakai Django template engine/Jinja. Kalau ditanya apa perannya models, models itu berguna sebagai ORM database sehingga mempercepat proses dev. Honestly, saya tidak suka memakai ORM karena menambah hafalan. Kalau ditanya apa perannya template, ya untuk mempermudah dalam perenderan objects dari python.

2. Mengurangi redundansi, contohnya ketika kita membuat list, kita cukup membuat styling-nya sekali saja untuk semua isi list tersebut. Selain itu, agar datanya dapat disalurkan ke templates lain dengan mudah.

3. `makemigrations` untuk mencatat migrations dalam file python (belum applied ke db) di folder `/migrations`. `migrate` membaca files di `/migrations` untuk di-execute di db.

### Tugas 3

1. Dengan `ModelForm`, fields pada form dapat dibuat secara otomatis berdasarkan field yang terdapat pada model. Selain itu, `ModelForm` juga menyediakan validasi data berdasarkan tipe dan aturan field pada model. `{% csrf_token %}` digunakan untuk melindungi form dari cross-site request forgery (CSRF) attack. CSRF attack terjadi ketika pengguna yang sudah authenticated dibuat mengirimkan request ke suatu website tanpa sepengetahuannya. `{% csrf_token %}` menghasilkan token unik yang kemudian dikirim bersama form. Ketika form dikirim, Django akan memeriksa token tersebut untuk memastikan bahwa request berasal dari form yang sah.

2. JSON formatnya lebih compact daripada XML. Selain itu, JSON lebih human-readable karena menggunakan struktur key-value dan array.

3. Client kirim request $\to$ Django ambil model object sesuai yang diinginkan request $\to$ Django kirim response dalam bentuk JSON string (menggunakan `serializers.serialize("json", data)`) agar frontend mudah untuk consume API tersebut.

### Tugas 6

1. REST (Representational State Transfer) basically adalah API style dengan constraints client-server, stateless, cache, uniform interface, layered system, dan optional code-on-demand. URIs di RESTful API indentify a certain resource. JSON hanya format. `PUT` mengganti seluruh fields di suatu resource. `PATCH` memperbarui sebagian fields. Contohnya, `PUT` untuk memperbarui seluruh data Experience dan `PATCH` untuk mengubah deskripsinya saja.

2. Serializer pada DRF mengubah data model menjadi format yang dapat dirender sebagai JSON, memvalidasi input, serta menangani create/update. Dibandingkan dictionary manual dengan JsonResponse, serializer menyediakan validasi otomatis, penanganan error yang konsisten, dan kode yang lebih mudah digunakan kembali.

3. Autentikasi memverifikasi identitas pengguna, sedangkan otorisasi menentukan hak aksesnya. Pada DRF, autentikasi dapat menggunakan `SessionAuthentication`, sementara otorisasi menggunakan permission class. Pemeriksaan harus dilakukan di server karena menyembunyikan tombol di template tidak mencegah pengguna mengirim request langsung melalui HTTP client.

4. `SessionAuthentication` menggunakan cookie session yang dikirim otomatis oleh browser sehingga rentan terhadap serangan CSRF. Oleh karena itu, request yang mengubah data memerlukan token CSRF, misalnya melalui header `X-CSRFToken`. `force_authenticate` melewati autentikasi session sehingga tidak menguji perlindungan CSRF. Pengujian yang tepat menggunakan `APIClient(enforce_csrf_checks=True)` dengan `.login()` untuk memastikan request tanpa token ditolak (403) dan request dengan token diterima.

## AI Disclosure

AI Model: Codex GPT-6 Astra.

### Tugas 1

- Chat link: https://chatgpt.com/s/cx_6a9e91d814408191b0ad0bf551234c43
- Improve dokumentasi di `README.md` yang telah saya tulis.
- CSS styling untuk experience section: responsive logo size, experience timeline, etc.
- Bertanya apa perbedaan `<section>`, `<article>`, dan `<aside>`.

### Tugas 2

- Chat link: https://chatgpt.com/s/cx_6aa823ffd7708191affbf11337d3726b
- Membuat awards HTML page sesuai dengan the other page patterns serta melakukan CSS styling-nya.
- Add tests for award
- Update tests for current experience model

### Tugas 3

- Chat link: https://chatgpt.com/s/cx_6aafa4691e348191866162f85d729112
- Added award editing. Each award now has an Edit button opening a prefilled form with Save Changes and Cancel.
- Added CRUD for Experience and Skill, includes create, search, edit, and delete confirmation pages.

### Tugas 4

I did not use AI at all.

### Tugas 5

- Chat link: https://chatgpt.com/s/cx_6ac3bdcbae4c8191a58bb1fd3c9b0528
- Refactored the Experience page from Django template list rendering to asynchronous Fetch API rendering.
- Implemented 300 ms search debouncing, request cancellation, and loading, empty, and error states.
- Updated the JSON endpoint to include skill names and implemented safe rendering while preserving existing display details and access controls.
- Updated Django tests, added JavaScript regression tests, ran coverage and browser checks, and committed the changes.
- Made the Experience creation page as a modal.

### Tugas 6

- I stopped using ChatGPT Desktop because I encountered the "ChatGPT hit a snag" error. Instead, I used Codex CLI. Unfortunately, I was unable to share the chat link.
- Prompt strategy: Applied the Tutorial 07 pattern to the independent assignment,
  maintained access control for four user roles, wrote tests, and made regular commits. I provided the complete
  instructions and grading rubric. Based on the existing code and README, the independent assignment was identified
  as the Experience feature, while the Award feature was the adaptation of Tutorial 07.
- Reviewed the existing models, forms, Award API, Experience page, permissions, and tests.
- Added the Experience star relationship and database migration, serializers with explicitly defined fields,
  text/date/skill validation, function-based API endpoints, and URL routes with SessionAuthentication.
- Integrated the Experience page with the API to support searching, creating, updating (PATCH), starring,
  and deleting (DELETE) experiences. Added an edit modal, deletion confirmation, CSRF protection, and toast notifications.
- Wrote APITestCase tests covering four user roles, database modifications, validation, starring functionality,
  read-only fields, HTTP 404/405 responses, and session-based authentication with actual CSRF enforcement.
- Updated the JavaScript regression tests and adjusted the Editor modal expectations in the existing tests.
- Wrote API documentation.
