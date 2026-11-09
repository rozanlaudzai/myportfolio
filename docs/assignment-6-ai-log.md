# Tugas 6 — log bantuan AI

Tanggal: 9 November 2026. Tool: Codex melalui aplikasi ChatGPT Work.

## Prompt pengguna (ringkasan)

Pengguna meminta penyelesaian Individual Assignment 6 PBP: menerapkan pola
Tutorial 07 pada bagian mandiri, menjaga akses empat peran, menulis test dan
jawaban reflektif, serta membuat commit rutin. Pengguna menyertakan instruksi
dan rubrik lengkap. Bagian mandiri diidentifikasi dari kode dan README sebagai
Experience; Award adalah adaptasi Tutorial 07.

## Langkah dan hasil bantuan

1. Memeriksa model, form, API Award, halaman Experience, permission, dan test lama.
2. Menambahkan relasi star Experience dan migrasi, serializer dengan field eksplisit,
   validasi teks/tanggal/skill, function-based API dan URL dengan SessionAuthentication.
3. Menghubungkan halaman Experience ke API untuk pencarian, create, PATCH,
   star dan DELETE. Menambahkan modal edit, konfirmasi hapus, CSRF dan toast.
4. Menulis APITestCase untuk empat peran, perubahan database, validasi, star,
   field read-only, 404/405, serta login session dengan pemeriksaan CSRF nyata.
5. Memperbarui regression test JavaScript dan ekspektasi modal Editor di test lama.
6. Menulis dokumentasi API, jawaban reflektif dengan sumber primer, dan log ini.

## Evaluasi kritis dan batasan

- Penggantian nama otomatis sempat menghasilkan nama field ordering yang salah
  (`experienceed_at`). Pemeriksaan kode dan test menemukan kesalahan tersebut;
  field diperbaiki menjadi `started_at` sebelum commit implementasi API.
- Test lama menganggap modal hanya tersedia bagi pemilik. Ekspektasi diperbarui
  karena Editor sekarang memerlukan modal yang sama untuk PATCH; API tetap
  menolak POST dan DELETE Editor.
- force_authenticate hanya dipakai untuk isolasi test permission. Test login
  dan CSRF memakai APIClient(enforce_csrf_checks=True) secara terpisah.
- Kode, pengujian, dan jawaban dihasilkan dengan bantuan AI dalam sesi ini.
  Tidak ada klaim bahwa pengguna sudah melakukan pemeriksaan manual sendiri.
  Pemilik repo perlu memahami implementasi dan meninjau jawaban sebelum submisi.
- Pemeriksaan lokal tidak membuktikan status deployment PWS, visibilitas publik
  GitHub, pengumpulan SCELE, atau pemenuhan tenggat Tutorial 07.

Log ini merupakan ringkasan prompt dan hasil kerja, bukan transkrip verbatim.

## Hasil verifikasi lokal

- `python manage.py test main`: 68 test lulus, termasuk test Tutorial 07.
- `node --test tests/awards.test.cjs tests/experience.test.cjs`: lulus.
- `check`, migrasi lokal, dan pemeriksaan migrasi yang belum dibuat: lulus.
- Runserver dan Chromium: halaman publik Experience/Award dan Browsable API
  berhasil dibuka. Pemilik berhasil create, search, toggle star, PATCH, dan DELETE;
  Editor berhasil PATCH tanpa tombol create/delete; pengguna biasa berhasil star.
  Tidak ada pageerror JavaScript. Pengujian ini memakai database terpisah di /tmp.
- Riwayat lokal menunjukkan merge Tutorial 07 `c797539` bertanggal
  4 November 2026, 23:36:58 WIB. Timestamp commit lokal tidak membuktikan waktu
  push atau status pengumpulan Tutorial 07 di SCELE.
