# Panduan Menjalankan MDB Intelligence (V76)

## Isi folder
| File | Fungsi |
|---|---|
| MDB_INTELLIGENCE_DASHBOARD_V76.html | Dashboard |
| mdb_server.py | Server lokal di http://127.0.0.1:8000 dan penghubung AI Copilot (Gemini) |
| update_market.py | Memperbarui data pasar (kurs, JISDOR, SOFR, EURIBOR) ke market.json |
| jalankan.sh | Peluncur: menguji kunci Gemini, memperbarui data pasar, menyalakan server |

## Menjalankan
```bash
cd ~/Documents/MDB_Intelligence
bash jalankan.sh
```
Tempel kunci Gemini saat diminta (tidak terlihat saat ditempel). Skrip langsung menguji kunci:
1. "Kunci valid" berarti AI Copilot siap.
2. "Ditolak (401)" berarti kunci berawalan AQ.; buat kunci berawalan AIza.
3. "Kunci tidak valid" berarti kunci terpotong, salah salin, atau belum aktif (tunggu 1 sampai 2 menit).
4. Tekan Enter tanpa kunci untuk mode offline; dashboard tetap berfungsi penuh kecuali AI Copilot.

Hentikan server dengan Ctrl + C.

## Membuat kunci berawalan AIza
1. Buka console.cloud.google.com dan pilih proyek.
2. APIs & Services > Library > Generative Language API > Enable.
3. APIs & Services > Credentials > Create credentials > API key. Salin dengan tombol salin.
4. Disarankan: Restrict key hanya untuk Generative Language API.

## Keamanan
1. Jangan simpan kunci di ~/.zshrc, di file, atau di dalam HTML. Masukkan hanya lewat prompt jalankan.sh.
2. Jangan menempelkan kunci ke chat atau dokumen. Bila terlanjur, hapus kunci itu dan buat yang baru.
3. Server hanya terbuka di 127.0.0.1 (komputer sendiri).
4. Jangan memasukkan data internal Kemenkeu yang bersifat rahasia ke AI Copilot; layanan Gemini tier gratis dapat memakai isi percakapan.

## Kendala umum
| Gejala | Penyebab dan solusi |
|---|---|
| {"error": "Tidak ditemukan"} | File HTML tidak berada di folder yang sama dengan mdb_server.py |
| Address already in use | Port 8000 terpakai: bash jalankan.sh --port 8001 |
| Peta kosong | Periksa koneksi internet; ganti tampilan peta lewat tombol lapisan di kanan atas peta |
| Copilot: kuota habis | Tunggu 1 menit, atau cek dengan: python3 mdb_server.py --diagnose |

## Foto sampul (opsional)
Sampul beranda bawaan adalah peta Indonesia dengan titik lokasi proyek MDB. Untuk memakai foto sendiri, simpan foto berformat JPG dengan nama cover.jpg di folder yang sama dengan dashboard (disarankan lebar minimal 1920 piksel, objek utama di sisi kanan). Foto otomatis dipakai saat dashboard dibuka lewat bash jalankan.sh.

## Halaman depan (sejak V70)
Setiap kali dashboard dibuka atau dimuat ulang, halaman depan dengan tombol "Learn more" selalu tampil lebih dulu. Klik tombol itu (atau tekan Enter) untuk masuk ke dashboard utama; sampul tidak lagi berada di atas dashboard. Untuk kembali ke halaman depan, klik logo "MDB Intelligence" di menu samping. Bila alamat memuat halaman tertentu (misalnya #projects), halaman itu dibuka setelah "Learn more".

## Tampilan baru (sejak V65)
Pada layar desktop, menu samping tetap tampil dan dapat diciutkan menjadi ikon melalui tombol menu di kiri atas. Pada tablet dan ponsel, menu tetap berupa laci. Rincian perubahan dan hasil pengujian ada di CATATAN_PERUBAHAN_V76.md.

## Fitur interaktif (sejak V67)
* Filter ringkasan di beranda (MDB, sektor, status, periode) memperbarui KPI, temuan utama, grafik, matriks, provinsi, dan peta sekaligus.
* Klik batang MDB, sektor, atau sel matriks untuk memfilter; klik lagi untuk melepas.
* Seret pada grafik tren tahunan untuk memilih periode.
* Tekan Ctrl K (Mac: Cmd K) atau tombol Cari untuk mencari halaman, proyek, dan perintah.

## Fitur analis (sejak V68)
* Klik proyek di mana pun untuk membuka panel detail di sisi kanan (panah kiri dan kanan untuk berpindah proyek, Esc untuk menutup).
* Project Explorer: klik judul kolom untuk mengurutkan; tabel dibagi per halaman; Ekspor CSV mengikuti filter.
* Tombol "Ekspor brief" di filter ringkasan menghasilkan ringkasan A4 siap cetak atau simpan sebagai PDF.
* Tombol "Salin tautan" menyalin alamat tampilan beserta filternya untuk dibagikan.

## Dashboard hidup (sejak V69)
* Bilah atas menampilkan indikator pasar (SOFR, kurs, BI-Rate, dan indikator makro). Status "Live" muncul bila dashboard dibuka lewat `./jalankan.sh` dan market.json berumur kurang dari 36 jam; selain itu tertulis "Tersimpan" dan memakai data bawaan.
* Tombol "Presentasi" (bilah atas atau filter ringkasan) membuka mode presentasi layar penuh sesuai filter aktif. Panah kiri dan kanan atau spasi untuk berpindah slide, P untuk putar otomatis, Esc untuk keluar.
* Semua animasi otomatis nonaktif bila perangkat diatur untuk mengurangi gerakan.

## Peta di Beranda (sejak V73)
Beranda dashboard utama hanya memakai peta Indonesia 3D (ketebalan sama untuk semua provinsi, warna menandai besaran ukuran yang dipilih, mengikuti filter ringkasan). Peta interaktif titik proyek dan panel makroekonomi sudah tidak ditampilkan di Beranda. Peta interaktif titik proyek tetap tersedia di menu Peta Proyek Indonesia dan di panel detail proyek.

## Halaman depan merah putih (sejak V74)
Halaman depan memakai latar putih gading dengan aksen merah, judul "Peta pembiayaan multilateral Indonesia", dan peta 3D Indonesia yang tersusun bertahap lalu menyorot provinsi dengan proyek terbanyak secara bergantian. Klik provinsi di peta untuk menyorotnya langsung.

## Sistem rapi dan dinamis (sejak V75)
* Ukuran huruf hanya lima: 12, 14, 16, 20, dan 32 px. Jarak antarelemen kelipatan 8 px.
* Semua tombol dan kolom isian minimal 44 x 44 px.
* Setiap interaksi memberi umpan balik:
  * Tombol menyala saat disorot dan mengecil sedikit saat ditekan.
  * Salin tautan, ekspor CSV, dan ekspor brief berubah menjadi tanda centang hijau setelah berhasil.
  * Notifikasi muncul perlahan, ada versi sukses dan galat.
  * Kolom simulasi berwarna merah dengan pesan jika isinya tidak valid, misalnya grace lebih panjang dari tenor.
  * Copilot menampilkan kerangka jawaban (skeleton) selama menunggu.
* Jika pengaturan perangkat meminta gerak dikurangi, semua animasi dimatikan.

## Tema Terakota Majapahit (V76)
Warna utama kini terakota, terinspirasi bata merah Trowulan, dengan tinta coklat tua sebagai aksen dan krem hangat sebagai latar. Peta 3D dan matriks memakai skala krem, pasir, sampai terakota tua. Merah murni hanya dipakai untuk pesan galat, sehingga artinya selalu jelas. Warna IsDB digeser menjadi merah keunguan (#7D2550) agar tidak tertukar dengan terakota, termasuk bagi pembaca buta warna. Ikon bendera kecil di halaman depan tetap merah putih asli.
