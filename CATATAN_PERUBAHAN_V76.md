# Catatan Perubahan MDB Intelligence V65 sampai V76

Basis: MDB_INTELLIGENCE_DASHBOARD_V64.html. File V64 tidak ditimpa. Seluruh perubahan berada pada lapisan tampilan (`<style id="ui-v65">` dan `<script id="ui-v65-js">`) ditambah pembersihan CSS yang tidak terpakai. Data `DB`, fungsi perhitungan, simulasi, dan endpoint AI Copilot tidak diubah.

## 1. Ringkasan perubahan

**Executive Overview (beranda setelah sampul)**
* Empat KPI utama dengan hierarki yang jelas: proyek tercatat, nilai pembiayaan tercatat, lokasi terpetakan, dan MDB terbesar menurut nilai. Setiap KPI punya konteks (periode, cakupan) dan visual komposisi per MDB.
* Strip cakupan data: proyek dengan nilai pembiayaan (471 dari 1.012) dan skor kualitas data.
* Panel Key Intelligence berisi tiga temuan yang dihitung otomatis dari database (konsentrasi pembiayaan, spesialisasi sektor, sebaran geografis). Setiap temuan menyertakan bukti angka, sumber, dan tanggal data. Kalimat statis lama ("ADB menempati posisi komparatif...") dihapus.
* Distribusi per MDB ditampilkan sebagai batang berpasangan (pangsa proyek dibanding pangsa nilai), ditambah rata rata nilai per proyek.
* Distribusi sektor dalam bentuk batang horizontal berurutan (menggantikan donut 9 irisan yang sulit dibaca).
* Matriks MDB x sektor punya total baris dan kolom, tooltip per sel, skala warna, serta pilihan tampilan "% portofolio MDB" agar MDB berportofolio kecil tetap dapat dibandingkan.
* Kartu baru "Sebaran lokasi per provinsi" (10 provinsi teratas dan komposisi titik per MDB) di samping peta.
* Statistik sampul, KPI, dan bilah atas kini memakai format angka Indonesia yang sama (1.012; US$85,7 miliar).
* Baris MDB, baris sektor, dan chip sektor dapat diklik untuk langsung membuka Project Explorer dengan filter yang sesuai.

**Navigasi**
* Desktop (lebar minimal 1100 px): sidebar tetap tampil, dapat diciutkan menjadi ikon (tombol menu atau tombol di kaki sidebar). Pilihan tersimpan di browser.
* Tablet dan ponsel: sidebar tetap berupa laci.
* Menu dikelompokkan ulang: Ringkasan, Eksplorasi proyek, Analitik, Decision Support, Data governance, Pembelajaran.
* Indikator halaman aktif berwarna emas. Bilah atas menampilkan breadcrumb kelompok dan nama halaman.
* Di beranda, sampul tetap layar penuh; sidebar dan bilah atas baru muncul setelah sampul terlewati.

**Visualisasi dan filter**
* Satu sistem tooltip untuk seluruh grafik baru (nilai, kategori, satuan, persentase).
* Project Explorer: bilah filter lengket dengan ikon pencarian, filter aktif ditandai, chip filter yang dapat dihapus satu per satu, tombol Reset, jumlah hasil dalam bahasa Indonesia, empty state, dan baris tabel yang dapat dibuka dengan keyboard (Enter).
* Peta beranda dan halaman Peta: tombol Reset, jumlah lokasi terformat, overlay "tidak ada lokasi yang cocok", dan pesan error bila pustaka peta tidak dapat dimuat (misalnya tanpa internet).

**Design system dan CSS**
* Token warna, radius, bayangan, ukuran huruf, dan jarak dalam CSS custom properties. Token lama (`--navy`, `--gold`, `--ink`, `--line`, dst.) dipetakan ke token baru sehingga lapisan lama ikut konsisten.
* Fokus keyboard yang terlihat, ukuran tombol dan input yang seragam (minimal 36 sampai 40 px).
* Audit CSS: 1.562 aturan diperiksa di seluruh halaman. 260 aturan yang hanya berlaku untuk kelas `mdb-home-legacy-dark` (tidak pernah dipasang oleh skrip mana pun) dan satu blok yang seluruhnya mati dihapus; ukuran file berkurang sekitar 40 KB.
* Responsif: overflow horizontal pada Simulasi Lanjutan di ponsel (sudah ada sejak V64) diperbaiki.

## 2. Fungsi yang dipertahankan

`DB` dan seluruh datanya, `go()`, semua 14 halaman, Project Explorer (`list()`, `detail()`), Ekspor CSV, peta Leaflet (marker, popup, legenda, cluster, layar penuh, lapisan resmi World Bank), filter MDB, sektor, tahun, dan pencarian, Country Ranking, Prioritas Pinjaman 2026, Sector Intelligence, Profil MDB dan modul saham, Financing & Rate, Simulasi (`sim()`), Simulasi Lanjutan, MDB Academy, Sources & QC, Metodologi, refresh makro, AI Copilot (`/api/ask`, `/api/health`), halaman pembuka "Learn more", tombol layar penuh dan cetak. Tidak ada kredensial di HTML.

## 3. Hasil pengujian

Pengujian otomatis dengan Chromium, V64 dibanding V65, memakai generator acak yang sama:

| Uji | Hasil |
|---|---|
| KPI dan isi database | Identik |
| Explorer: semua, kata kunci, ADB, sektor energi, kombinasi, hasil kosong | Identik |
| Explorer: tahun 2009 | 12 menjadi 13 proyek (perbaikan, lihat bagian 4) |
| Detail proyek dari baris tabel | Identik |
| Jumlah lokasi peta beranda (semua, AIIB, IsDB, kata kunci kosong) | Identik |
| Peta: lapisan semua, ongoing ADB, prioritas 2026 | Identik |
| Simulasi: dua skenario (rekomendasi, skor, biaya per bank) | Identik |
| Simulasi Lanjutan (hash keluaran) | Identik |
| Teks Profil, Financing, Ranking, Sektor, Prioritas, Sumber, Metodologi, Academy | Identik |
| 13 tombol sidebar dan 7 tautan sampul | Semua berfungsi |
| AI Copilot panel, Ekspor CSV | Berfungsi |
| Halaman pembuka, Enter untuk masuk, laci menu di ponsel | Berfungsi |
| Overflow horizontal pada 1440x900, 1280x800, 768x1024, 390x844 | Tidak ada |
| Error JavaScript | Tidak ada |

## 4. Catatan dan masalah yang belum selesai

* **Perbaikan filter tahun.** Sebagian `approval_year` tersimpan sebagai teks "2009.0" sehingga filter tahun menampilkan pilihan ganda dan satu proyek tidak pernah muncul. V65 menyeragamkan tipe nilai tahun (nilainya tidak berubah) dan merapikan daftar pilihan.
* **Warna latar.** Prompt menyarankan #F4F7FA, tetapi sebelumnya Anda memilih latar slate karena putih terlalu terang. V65 memakai #E8EDF2 (sedikit lebih terang dari V64). Untuk menggantinya cukup ubah token `--c-bg`.
* **Belum diuji langsung:** jawaban Gemini melalui server lokal dan pemuatan tile peta dari internet (lingkungan uji tidak punya akses jaringan). Panel Copilot dan pemanggilan endpoint tidak diubah.
* **Ekspor CSV** tetap mengekspor seluruh proyek, bukan hasil filter (perilaku V64). Bisa diubah bila diperlukan.
* **Konsolidasi CSS** dilakukan bertahap: aturan mati dihapus dan lapisan V65 memakai token, tetapi masih ada sekitar 30 blok `<style>` lama. Menggabungkan semuanya menjadi satu stylesheet berisiko regresi tinggi dan sebaiknya dilakukan terpisah.
* Teks beberapa halaman lama (judul tabel, catatan metodologi) masih campuran Indonesia dan Inggris sesuai isi aslinya.

## 5. Revisi V66: tipografi dan warna

**Tipografi**
* Dashboard kini hanya memakai dua keluarga huruf. Plus Jakarta Sans (berat 600 dan 700) dipakai untuk judul, angka utama, dan merek. IBM Plex Sans (400 sampai 700) dipakai untuk teks, label, tombol, dan tabel.
* Inter dihapus dari pemuatan font. Sebelumnya sampul memakai tiga keluarga sekaligus: Inter untuk judul dan teks, Plus Jakarta untuk tombol, dan IBM Plex untuk menu. Seluruh 28 deklarasi Inter di CSS, skrip, dan grafik SVG diganti.
* Berat 800 dan 900 diseragamkan menjadi maksimum 700. Teks 8 sampai 9 px (label MDB Academy, subjudul merek di sampul) dinaikkan menjadi minimal 10 sampai 10,5 px.

**Warna (hasil analisis)**
* **World Bank dan IsDB bertabrakan.** Biru #1F5FA8 dan ungu #6B4C9A hanya berselisih ΔE 24 pada penglihatan normal, 11 pada deuteranopia, dan 4 pada protanopia (praktis sama). IsDB diganti burgundy #8A2E40, sehingga jarak terdekat antar MDB menjadi 48 (normal), 26 (protanopia), dan 29 (deuteranopia). Kontras di atas putih 8,2:1.
* **AIIB tidak konsisten.** Badge di Project Explorer berwarna oranye, sementara di grafik, peta, dan profil AIIB berwarna hijau. Badge keempat MDB kini diturunkan dari warna kategori yang sama.
* **Emas dipakai berlebihan dan bercampur dengan peringatan.** Catatan informasi biasa tampil kuning seperti peringatan. Kini catatan informasi netral (abu kebiruan), dan kuning hanya untuk peringatan. Label kecil di kartu tidak lagi emas; emas disisakan untuk aksen utama (menu aktif, sampul, tombol utama, judul halaman).
* **Status bersaing dengan warna MDB.** Label "Lunas" hijau di kartu AIIB terbaca seolah warna AIIB. Label status kini berteks netral dengan titik warna kecil.
* **Tautan biru menyerupai World Bank.** Tautan kini navy, menjadi emas saat disorot.
* **Warna kartu temuan meminjam warna ADB.** Kartu Key Intelligence ketiga bergaris teal ADB; kini seluruhnya navy.
* **Peta Prioritas 2026.** Empat gradasi emas per lender tidak dapat dibedakan, dan legenda menampilkan satu titik ADB untuk semua MDB. Kini titik prioritas memakai satu emas sesuai legenda, dan legenda menampilkan keempat warna MDB.
* **Palet dirampingkan.** 364 kode warna dari 39 varian yang hampir sama (5 navy, 10 abu, 11 emas, 2 merah) disatukan ke palet token. Teks sekunder digelapkan menjadi #5B6C7E agar memenuhi kontras AA (4,6:1) juga di atas latar slate.

**Pengujian V66:** seluruh uji regresi identik dengan V65 (KPI, filter, peta, simulasi, Simulasi Lanjutan, navigasi, Copilot, CSV). Tidak ada error skrip dan tidak ada overflow pada 1440 px dan 390 px.

## 6. Revisi V67: interaksi dinamis

* **Filter ringkasan global.** Bilah filter di beranda (MDB, sektor, status, periode persetujuan dengan slider dua arah) menghitung ulang seluruh beranda dari database: empat KPI, cakupan data, Key Intelligence, distribusi MDB dan sektor, matriks, sebaran provinsi, serta titik di peta. Jumlah hasil selalu ditampilkan ("Menampilkan 139 dari 1.012 proyek"). Bilah tetap terlihat saat digulir.
* **Grafik sebagai filter.** Klik baris MDB, baris sektor, atau sel matriks untuk memfilter dashboard; klik lagi untuk melepas. Tombol "Buka di Project Explorer" membawa filter ke daftar proyek.
* **Tren persetujuan per tahun (baru).** Kolom bertumpuk per MDB 1968 sampai 2027, dengan pilihan jumlah proyek atau nilai. Seret di grafik untuk memilih periode; tahun di luar periode memudar. Ada ringkasan periode dan tahun puncak.
* **Command palette.** Ctrl K / Cmd K, tombol "Cari" di bilah atas, atau tombol "/" membuka pencarian cepat untuk 13 halaman, perintah (reset filter, ekspor CSV, AI Copilot, layar penuh, filter per MDB atau sektor), dan proyek (nama, ID, lokasi, agency). Navigasi penuh dengan keyboard.
* **Gerak halus.** Angka KPI bergerak ke nilai baru saat filter berubah, panel yang diperbarui berkedip lembut, dan kartu muncul perlahan saat digulir. Semua animasi mati otomatis bila pengguna memilih "kurangi gerakan" di sistem operasi, dan tidak tampil saat dicetak.
* **Peta beranda** mengikuti filter ringkasan. Pilihan MDB dan sektor ganda di kartu peta dihapus agar tidak bertentangan; pencarian lokasi tetap ada.

**Pengujian V67:**
* Tanpa filter, seluruh uji regresi identik dengan V66 (KPI, filter Explorer, peta, simulasi, Simulasi Lanjutan, navigasi, Copilot, CSV).
* Skenario filter diperiksa: AIIB dan IsDB saja (97 proyek, 188 lokasi), ditambah sektor energi (9 proyek), sel ADB x keuangan dan tata kelola (139 proyek, sama dengan angka di matriks), dan seret periode 2015 sampai 2026 (215 proyek). Jumlah KPI, keterangan hasil, dan jumlah titik peta selalu konsisten.
* Command palette dapat membuka detail proyek dan halaman.
* Tidak ada error skrip dan tidak ada overflow pada 1440, 768, dan 390 px.

**Catatan:** filter ringkasan hanya berlaku di beranda. Halaman lain (Country Ranking, Profil, Simulasi) memakai data resmi per MDB yang tidak dapat dipecah per proyek.

## 7. Revisi V68: fitur kelas analis

* **Panel detail proyek.** Klik proyek dari Project Explorer, peta, pencarian, atau proyek serupa untuk membuka panel di sisi kanan tanpa meninggalkan halaman. Isinya:
  * status, nilai, tanggal, sektor, instrumen, executing agency, dan lokasi;
  * peta mini titik proyek;
  * konteks portofolio (pangsa sektor dalam MDB, peringkat nilai, proyek di tahun yang sama);
  * lima proyek serupa;
  * sumber resmi dan catatan kualitas data.

  Panah kiri dan kanan berpindah antar proyek hasil filter, dan Esc menutup panel. Halaman detail lama tetap tersedia melalui tombol "Halaman detail lengkap". Nilai "nan" dari sumber tidak lagi ditampilkan.
* **Project Explorer analitis.**
  * Seluruh kolom dapat diurutkan; bawaannya tahun terbaru.
  * Tabel dibagi per halaman (25, 50, 100, atau 250 baris), sehingga seluruh proyek dapat dijelajahi. Sebelumnya tabel berhenti di 250 baris pertama.
  * Ekspor CSV kini mengikuti filter aktif, dengan jumlah proyek tertera di tombol.
  * Di ponsel, tabel berubah menjadi kartu.
* **Brief siap cetak.** Tombol "Ekspor brief" menyusun ringkasan A4 sesuai filter aktif: KPI, temuan utama, distribusi MDB dan sektor, matriks, provinsi teratas, catatan metodologi, dan sumber. Hasilnya bisa dicetak atau disimpan sebagai PDF dari dialog cetak. Contoh terlampir: CONTOH_BRIEF_ADB_ENERGI.pdf.
* **Tautan tampilan.** Filter ringkasan tersimpan di alamat halaman, dan tombol "Salin tautan" menyalinnya. Penerima langsung melihat tampilan yang sama tanpa halaman pembuka.
* **Glosarium.** Istilah teknis di halaman Profil, Financing, Simulasi, Simulasi Lanjutan, Prioritas, dan Metodologi bergaris titik dan menampilkan penjelasan saat disorot. Contohnya SOFR, spread, hak suara, modal disubscribe dan disetor, callable, SCI, Islamic Dinar, konstituensi, DRPPLN, dan MTDS.
* **Penyeragaman teks.** Judul kecil setiap halaman kini mengikuti kelompok menu. Kalimat pembuka halaman yang masih berbahasa campuran disunting, misalnya beranda, Peta, Prioritas, Sektor, Profil, Financing, dan Sources.
* **Lebih ringan.** Gambar sampul lama 345 KB yang tertutup peta SVG dihapus; file turun dari 3,30 MB menjadi 2,99 MB.

**Pengujian V68:**
* Total hasil filter di Explorer tetap sama (1.012; ADB 432; energi 109; tahun 2009: 13); kini ditampilkan 50 per halaman.
* Simulasi, Simulasi Lanjutan, peta, dan KPI identik dengan V67. Jumlah angka di setiap halaman tetap sama; yang berubah hanya kalimat pembuka.
* Panel detail, navigasi antar proyek, urut kolom, pindah halaman, ekspor sesuai filter, tautan bagikan (dibuka ulang dan filter terpasang), dan brief PDF telah diuji.
* Tidak ada error dan tidak ada overflow pada 1440, 1280, 768, dan 390 px.

## 8. Revisi V69: dashboard hidup

**Gerak dan transisi**
* Setiap halaman masuk dengan transisi halus.
* Grafik tumbuh saat pertama terlihat: batang memanjang, kolom tren naik dari dasar, sel matriks muncul bertahap, dan kartu temuan muncul berurutan.
* Saat filter berubah, grafik tumbuh ulang dan titik peta muncul kembali.
* Kartu KPI dan temuan sedikit terangkat saat disorot.

**Sampul dan peta hidup**
* Titik proyek di sampul muncul bertahap dari barat ke timur.
* Garis koneksi emas tergambar bergantian dari Jakarta ke klaster proyek terpadat, dengan denyut di titik Jakarta.
* Angka statistik sampul berjalan dari nol.
* Titik di peta beranda dan halaman Peta muncul dengan animasi setiap kali filter atau lapisan berubah.

**Indikator pasar live**
* Bilah atas memuat ticker SOFR, USD/IDR, EUR/IDR, JPY/IDR, EURIBOR 6M, BI-Rate, inflasi, pertumbuhan, utang luar negeri, dan ringkasan portofolio. Ticker berhenti saat disorot, tiap indikator punya tooltip sumber dan tanggal, dan klik SOFR membuka Simulasi.
* Status jujur: "Live" (titik hijau berdenyut) hanya bila market.json dari update_market.py terbaca lewat server dan berumur kurang dari 36 jam. Data diperiksa ulang tiap 10 menit, dan waktu pembaruan ditampilkan.
* Bila dibuka langsung sebagai file, status menjadi "Tersimpan" dan memakai data bawaan dashboard.

**Mode presentasi**
* Tombol "Presentasi" membuka 9 slide layar penuh yang disusun otomatis dari filter aktif: sampul, gambaran portofolio, tren, temuan utama, siapa membiayai, sektor, matriks, sebaran geografis, dan penutup dengan catatan metodologi.
* Setiap slide punya judul dan satu kalimat narasi yang dihitung dari data.
* Navigasi dengan panah atau spasi, putar otomatis setiap 9 detik (tombol P), bilah kemajuan, dan Esc untuk keluar. Konten otomatis diskalakan agar pas di layar proyektor mana pun.

**Pengujian V69:**
* Uji regresi identik dengan V68 (KPI, filter, peta, simulasi, Simulasi Lanjutan, navigasi, Copilot, CSV).
* Ticker diuji pada dua kondisi: lewat server dengan market.json uji (status Live) dan sebagai file (status Tersimpan).
* Kesembilan slide presentasi telah diperiksa.
* Tidak ada error dan tidak ada overflow pada 1440, 1280, 768, dan 390 px.

## 9. Revisi V70: halaman depan sebelum dashboard utama

* **Halaman depan selalu tampil lebih dulu.** Halaman depan dengan tombol "Learn more" kini muncul setiap kali dashboard dibuka atau dimuat ulang. Sebelumnya halaman depan hanya muncul sekali per sesi browser dan terlewati bila alamat memuat tanda #.
* **Dashboard utama terpisah dari sampul.** Setelah "Learn more" diklik (atau Enter ditekan), sampul memudar dan dashboard utama tampil dari atas dengan menu samping dan bilah atas langsung terlihat. Sampul tidak lagi berada di atas dashboard saat menggulir.
* **Tujuan dari alamat tetap dihormati.** Bila alamat memuat halaman tertentu (misalnya #projects) atau tautan filter yang dibagikan, halaman atau filter itu langsung terbuka setelah "Learn more".
* **Kembali ke halaman depan.** Klik logo "MDB Intelligence" di menu samping.
* Selama halaman depan tampil, halaman tidak dapat digulir dan menu disembunyikan. Petunjuk "Tekan Enter untuk masuk" tampil di layar desktop dan disembunyikan di ponsel.

**Pengujian V70:**
* Halaman depan muncul saat dibuka pertama kali, setelah dimuat ulang, dan saat alamat memuat #projects.
* Masuk lewat tombol, lewat Enter, dan kembali lewat logo semuanya berfungsi.
* Seluruh uji regresi identik dengan V69. Tidak ada error dan tidak ada overflow pada 1440, 768, dan 390 px.

## 10. Revisi V71: peta 3D portofolio per provinsi

* **Peta Indonesia 3D di dashboard utama.** Kartu baru ditempatkan di atas peta proyek. Setiap provinsi diekstrusi; tingginya sebanding dengan ukuran yang dipilih (jumlah proyek, titik lokasi, atau nilai tercatat), dan warna makin gelap untuk nilai lebih besar. Provinsi teratas diberi nomor peringkat, dan provinsi terpilih disorot emas dengan label nilai.
* **Interaksi.**
  * Arahkan kursor untuk melihat nilai dan peringkat; klik provinsi atau kartu lima besar untuk memilih.
  * Panel "Provinsi terpilih" menampilkan peringkat, pangsa, jumlah proyek, titik lokasi, nilai, komposisi per MDB, sektor terbanyak, dan tiga proyek bernilai terbesar (klik untuk membuka panel detail proyek).
* **Dinamis.** Bangunan provinsi tumbuh saat kartu pertama terlihat dan beranimasi ulang saat ukuran atau filter ringkasan berubah. Contohnya, dengan filter AIIB saja urutan berubah menjadi Jawa Timur, Nusa Tenggara Barat, dan Jawa Tengah.
* **Masuk ke mode presentasi.** Peta 3D menjadi satu slide tersendiri.
* **Andal tanpa internet.** Peta digambar dengan SVG langsung oleh browser, tanpa WebGL atau pustaka eksternal. Peta 3D versi lama (V55) tidak dapat dibuka di beberapa perangkat karena bergantung pada pustaka 3D; masalah itu tidak terjadi lagi di versi ini.
* **Catatan data.** Batas mengikuti peta dasar 32 provinsi: Kepulauan Riau digabung dengan Riau, Kalimantan Utara dengan Kalimantan Timur, Sulawesi Barat dengan Sulawesi Selatan, dan provinsi pemekaran Papua mengikuti induknya. Proyek yang berlokasi di beberapa provinsi dihitung di setiap provinsinya, sehingga nilai per provinsi tidak dijumlahkan.

**Pengujian V71:**
* Ketiga ukuran, sorotan dan tooltip, pemilihan provinsi, integrasi filter ringkasan, dan slide presentasi telah diuji.
* Uji regresi identik dengan V70. Tidak ada error dan tidak ada overflow pada 1440, 768, dan 390 px.

## 11. Revisi V72: peta 3D bertinggi seragam

* Semua provinsi kini digambar dengan ketebalan yang sama. Tidak ada lagi provinsi yang menjulang karena peringkat atau besar nilainya.
* Besaran ukuran (jumlah proyek, titik lokasi, atau nilai) ditunjukkan melalui gradasi warna, dilengkapi legenda "Lebih kecil sampai Lebih besar" dan penanda provinsi tanpa lokasi proyek.
* Nomor peringkat lima besar, provinsi terpilih berwarna emas, panel rincian, dan integrasi filter ringkasan tetap berfungsi.
* Peta 3D hanya ada di Beranda dashboard utama (dan slide presentasi). Halaman Peta Proyek, kartu peta proyek di Beranda, dan peta mini di panel detail proyek tetap memakai peta interaktif yang lama.

**Pengujian V72:** uji regresi identik dengan V71. Peta interaktif lama terverifikasi tetap aktif di halaman Peta, di Beranda, dan di panel detail proyek. Tidak ada error dan tidak ada overflow pada 1440 dan 390 px.

## 12. Revisi V73: Beranda lebih ringkas

* Kartu "Peta proyek Indonesia" (peta interaktif titik proyek) dihapus dari Beranda. Peta 3D kini menjadi satu satunya peta di Beranda.
* Panel "Makroekonomi Indonesia terkini" dihapus dari Beranda. Indikator utama (SOFR, kurs, BI-Rate, inflasi, pertumbuhan) tetap tampil di ticker bilah atas.
* Kartu "Sebaran lokasi per provinsi" dipindah ke samping kartu Dimensi Komparatif agar susunan tetap rapi.
* Peta interaktif titik proyek tetap tersedia di menu Peta Proyek Indonesia dan di panel detail proyek. Tautan "Buka peta proyek" pada temuan geografis mengarah ke halaman tersebut.
* Elemen lama disimpan tersembunyi, bukan dihapus dari kode, agar fungsi yang merujuknya (pencarian Copilot, uji filter) tetap aman.

**Pengujian V73:** uji regresi identik dengan V72. Urutan Beranda: filter ringkasan, KPI, cakupan data, tren, temuan utama, distribusi MDB dan sektor, matriks, peta 3D, peringkat negara dan posisi Indonesia, dimensi komparatif dan sebaran provinsi, serta klasifikasi sektor. Tidak ada error.

## 13. Revisi V74: halaman depan merah putih yang dinamis

* **Warna.** Latar navy gelap dengan titik bercahaya emas, yang terkesan generik, diganti latar putih gading dengan aksen merah (#C8102E). Ada garis bendera merah putih di tepi atas dan ikon bendera kecil di samping label. Teks utama memakai warna tinta gelap yang netral.
* **Judul baru.** "Peta pembiayaan multilateral Indonesia" (dua kata terakhir berwarna merah), menggantikan "Bersama, Membangun Dampak Nyata" yang terlalu umum. Paragraf pembuka menyebut jumlah proyek secara otomatis dan menjelaskan fungsi dashboard.
* **Peta 3D di halaman depan.** Provinsi dengan proyek diberi gradasi putih ke merah sesuai jumlah proyek; provinsi tanpa lokasi proyek tetap putih.
* **Dinamis.**
  * Garis bendera tergambar dari kiri, provinsi muncul bertahap dari barat ke timur, dan judul serta tombol muncul berurutan.
  * Delapan provinsi teratas disorot bergantian setiap 3,2 detik: provinsi terangkat, berwarna merah tua dengan penanda berdenyut, dan kartu "Sorotan provinsi" menampilkan jumlah proyek, nilai, serta komposisi per MDB.
  * Klik provinsi di peta untuk menyorotnya langsung.
  * Animasi berhenti otomatis setelah masuk ke dashboard.
* **Tombol "Learn more"** berwarna merah. Statistik ditampilkan dengan garis atas bergaya editorial.
* **Dashboard utama tetap navy dan emas** agar konsisten dengan identitas Kementerian Keuangan dan tidak bertabrakan dengan warna kategori MDB.

**Pengujian V74:** alur halaman depan (masuk, muat ulang, kembali lewat logo) dan uji regresi identik dengan V73. Tampilan dicek pada 1440, 1024, dan 390 px. Tidak ada error.


## 14. Revisi V75: seluruh dashboard merah putih

* **Navy dan emas dihapus dari seluruh dashboard.**
  * Warna navy diubah menjadi tinta arang.
  * Abu kebiruan diubah menjadi abu hangat.
  * Emas diubah menjadi merah. Ada 1.025 kode warna yang dikonversi otomatis saat build.
  * Data proyek tidak disentuh.
  * Pemindaian warna terhitung di 13 halaman tidak menemukan sisa navy atau emas.
* **Bilah atas dan menu samping** berlatar putih dengan garis merah di tepi atas. Menu aktif ditandai teks merah, latar merah muda, dan garis merah di kiri. Logo "MI" berupa kotak merah.
* **Grafik.**
  * Batang tunggal memakai tinta arang.
  * Matriks MDB x sektor dan peta 3D memakai gradasi putih ke merah.
  * Provinsi terpilih di peta 3D berwarna arang agar menonjol dari gradasi merah.
  * Warna kategori MDB dipertahankan. Merah tidak dipakai untuk seri data MDB agar tidak tertukar dengan aksen antarmuka.
* **Permukaan yang dulu navy** kini merah datar: kepala Posisi Indonesia, banner rekomendasi simulasi, sampul MDB Academy, serta slide pembuka dan penutup mode presentasi.

## 15. Revisi V75: sistem antarmuka rapi dan dinamis

* **Skala huruf.**
  * Sebelumnya ada 29 ukuran berbeda (9 sampai 48 px). Kini hanya lima: 12, 14, 16, 20, dan 32 px.
  * Judul halaman di landing tetap memakai ukuran display.
  * Font tetap dua: Plus Jakarta Sans untuk judul dan IBM Plex Sans untuk isi.
  * Label grafik SVG minimal 12 px.
* **Jarak.** Padding, margin, dan gap dibulatkan ke kelipatan 8 px (4 px untuk jarak rapat di dalam komponen). Ada 711 deklarasi yang disesuaikan.
* **Token.** Warna, ukuran huruf, jarak, durasi, dan easing disimpan sebagai variabel CSS (`--c-*`, `--fs-1` sampai `--fs-5`, `--s-1` sampai `--s-6`, `--dur-1` sampai `--dur-3`, `--ease`).
* **Gerak.**
  * Semua transisi 150 sampai 300 ms. Ada 41 animasi lebih lambat dari 300 ms yang dipercepat.
  * Animasi peta di halaman depan dipercepat dari 650 menjadi 300 ms.
  * Gradasi mencolok diganti warna datar, dan bayangan dibuat lebih tipis.
* **Umpan balik.**
  * Hover dan tekan: tombol mengecil 3% saat ditekan.
  * Fokus keyboard: garis merah.
  * Disabled: transparan 50%.
  * Loading: spinner pada tombol kirim Copilot dan skeleton pada jawaban Copilot.
  * Sukses: tombol berubah hijau dengan tanda centang, dan notifikasi bertanda centang.
  * Galat: kolom merah dengan pesan di bawahnya. Notifikasi galat berwarna merah tua.
  * Saat berpindah halaman lewat menu, fokus pindah ke judul halaman.
* **Aksesibilitas.**
  * Area klik tombol, pilihan, dan kolom isian minimal 44 x 44 px.
  * Audit kontras otomatis menurunkan pelanggaran nyata hampir ke nol. Perbaikan utama:
    * Label grup menu dan teks pudar menjadi #6F6A64.
    * Warna teks sel matriks dipilih otomatis berdasarkan kontras.
    * Hijau AIIB digelapkan sedikit (#4E7A26) agar teks putih lolos 4,5:1.
  * Pengaturan reduce motion mematikan seluruh animasi.
* **Responsif.** Diuji pada 1440, 1280, 768, dan 390 px tanpa gulir horizontal. Di ponsel, tombol filter tersusun ulang dalam dua baris, statistik halaman depan menjadi 2 x 2, dan tombol layar penuh disembunyikan.

**Pengujian V75:**
* Uji regresi (23 pemeriksaan fungsi dan angka) identik dengan V74.
* Semua skrip lolos pemeriksaan sintaks. Tidak ada error konsol.
* Uji interaksi: salin tautan menampilkan centang dan notifikasi sukses; grace 30 tahun memunculkan pesan galat; skeleton Copilot muncul selama menunggu.
* Reduce motion menghasilkan durasi animasi 0 detik.

**Catatan jujur:**
* Kode lama ditulis dengan pendekatan desktop first. Lapisan V75 merapikan semua ukuran tetapi tidak menulis ulang struktur menjadi mobile first.
* Tautan di dalam paragraf dan slider rentang tahun masih di bawah 44 px. Tautan dalam teks dikecualikan oleh WCAG, dan slider tetap bisa digeser lewat jalurnya.


## 16. Revisi V76: tema Terakota Majapahit

* **Alasan.**
  * Dalam konteks keuangan, merah dibaca sebagai rugi atau bahaya. Akibatnya, provinsi dengan proyek terbanyak tampil seperti zona rawan.
  * Terakota masih satu keluarga dengan merah putih dan punya akar Indonesia (bata Trowulan), tetapi tidak membawa makna negatif.
* **Palet.**
  * Utama terakota #A84A26, gelap #8A3A1C.
  * Aksen tinta coklat tua #2B211C.
  * Netral krem #F7F2EA dan abu coklat #6E625A.
  * Semua disimpan sebagai token.
  * Kontras: terakota di atas putih 5,7:1, teks pudar di atas krem 5,3:1. Keduanya lolos WCAG AA.
* **Skala peta dan matriks.** Krem, pasir oranye, terakota tua, dengan tiga titik warna agar nada tengah tidak kusam.
* **Warna MDB.** IsDB digeser dari marun #8A2E40 ke merah keunguan #7D2550. Jarak warnanya terhadap terakota dan tiga MDB lain diuji pada simulasi deuteranopia, protanopia, dan tritanopia. Hasilnya adalah kandidat dengan jarak minimum terbesar di antara tujuh yang diuji.
* **Merah murni** kini khusus untuk galat (kolom isian dan notifikasi galat). Ikon bendera di halaman depan tetap merah putih asli.
* **Konversi.** 262 kode warna dikonversi otomatis. Pemindaian warna terhitung di 13 halaman tidak menemukan sisa merah tema lama.

**Pengujian V76:** uji regresi identik dengan V74 dan V75. Audit tipografi (lima ukuran) dan kontras tetap lolos. Tidak ada gulir horizontal di 1280 dan 390 px. Tidak ada error konsol.
