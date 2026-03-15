# Laporan Praktikum Sistem Komputasi Terdistribusi
## Studi Kasus: Sistem Pemantauan Stasiun Cuaca Cerdas

Nama  : Syifani Adillah Salsabila

NIM   : 235150207111052

Mata Kuliah : Sistem Komputasi Terdistribusi-B

---
### Pertanyaan Laporan A

Setelah program berjalan, jawab pertanyaan berikut di laporan:

**1. Berapa lama waktu yang dibutuhkan sebelum batch pertama selesai diproses?
   Mengapa membutuhkan waktu tersebut?**

Batch pertama pada program MapReduce akan diproses setelah 20 pesan data sensor terkumpul di dalam buffer. Pada infrastruktur yang digunakan pada praktikum ini, publisher mengirimkan data sebanyak 5 pesan per detik, yaitu satu pesan dari masing-masing lima stasiun cuaca secara bergantian.
Dengan konfigurasi pada kode:
BATCH_SIZE = 20
maka jumlah pesan yang harus terkumpul sebelum proses MapReduce dijalankan adalah 20 pesan. Perkiraan waktu yang dibutuhkan dapat dihitung sebagai berikut:
20 pesan ÷ 5 pesan per detik = ± 4 detik

Waktu tersebut dibutuhkan karena mekanisme MapReduce pada program ini menggunakan pendekatan batch processing. Dalam pendekatan batch processing:
- Data tidak langsung diproses ketika diterima.
- Data terlebih dahulu dikumpulkan ke dalam buffer.
- Setelah jumlah data mencapai ukuran batch (BATCH_SIZE), barulah proses komputasi dijalankan.
Pada kode yang digunakan, proses ini terlihat pada bagian berikut:
buffer.append(payload)

if len(buffer) >= BATCH_SIZE:
    process_batch(buffer.copy())
    buffer.clear()

Artinya:
- Setiap pesan MQTT yang diterima akan dimasukkan ke dalam buffer.
- Program akan terus menunggu sampai jumlah data dalam buffer mencapai 20 record.
- Setelah buffer penuh, fungsi process_batch() akan dijalankan untuk melakukan proses Map → Shuffle → Reduce.

**2. Apa yang terjadi dengan urutan data dari berbagai stasiun saat masuk ke buffer?
   Bagaimana fase Shuffle menangani hal ini?**

Saat data diterima oleh subscriber MQTT, setiap pesan dari broker akan diproses oleh fungsi on_message() dan kemudian dimasukkan ke dalam buffer. Pada kode yang digunakan:
buffer.append(payload)

Data dari berbagai stasiun cuaca akan masuk ke buffer sesuai dengan urutan kedatangan pesan dari MQTT broker. Karena publisher mengirimkan data secara bergantian dari lima stasiun, maka urutan data yang masuk ke buffer biasanya akan terlihat seperti berikut:

WS-001
WS-002
WS-003
WS-004
WS-005
WS-001
WS-002
WS-003
WS-004
WS-005
...

Dengan kata lain, data dari berbagai stasiun akan bercampur dalam satu buffer tanpa pengelompokan khusus. Hal ini terjadi karena subscriber hanya menerima aliran data (stream) dari broker dan tidak mengurutkan data berdasarkan stasiun pada tahap awal.

Sedangkan, Pada fase Shuffle, pasangan (key, value) yang dihasilkan dari fase Map akan dikelompokkan berdasarkan key, yaitu station_id.

Pada kode program, proses ini dilakukan menggunakan struktur data defaultdict(list):
grouped = defaultdict(list)

for key, value in mapped:
    grouped[key].append(value)

Proses yang terjadi adalah sebagai berikut:
- Hasil dari fase Map menghasilkan pasangan data seperti:
("WS-001", {...})
("WS-002", {...})
("WS-003", {...})
("WS-001", {...})
("WS-002", {...})
- Pada fase Shuffle, data tersebut akan dikelompokkan berdasarkan station_id.
WS-001      4   26.43   41.12  127.25     264      61.48 Tidak Sehat (sensitif)
WS-002      4   30.66   39.25  132.25     264      44.99 Tidak Sehat (sensitif)
WS-003      4   33.11   40.85  167.25     215      23.22 Tidak Sehat
WS-004      4   30.53   39.10  147.75     277      60.85 Tidak Sehat (sensitif)
WS-005      4   23.62   28.47  144.00     253      81.59 Tidak Sehat (sensitif)
- Setelah data dikelompokkan, fase Reduce dapat menghitung statistik untuk setiap stasiun secara terpisah.

 **3. Jika BATCH_SIZE ditingkatkan menjadi 100, apa dampaknya terhadap akurasi statistik dan latensi hasil?**

Pada program MapReduce yang dibuat, nilai BATCH_SIZE menentukan jumlah pesan data yang harus terkumpul di dalam buffer sebelum proses Map → Shuffle → Reduce dijalankan.Pada kode yang digunakan:
BATCH_SIZE = 20

Artinya proses MapReduce akan dijalankan setiap kali 20 pesan berhasil dikumpulkan. Jika nilai tersebut ditingkatkan menjadi:
BATCH_SIZE = 100

maka sistem harus menunggu hingga 100 pesan terkumpul sebelum menjalankan proses MapReduce. Karena publisher mengirim 5 pesan per detik, maka waktu yang dibutuhkan untuk mengumpulkan 100 pesan adalah:

100 pesan ÷ 5 pesan per detik = ± 20 detik

Dengan demikian, hasil analisis baru akan muncul sekitar setiap 20 detik.

- Dampak terhadap akurasi statistik

Jika ukuran batch diperbesar menjadi 100, maka statistik yang dihasilkan cenderung lebih stabil dan akurat. Hal ini terjadi karena: jumlah data yang dianalisis lebih banyak, variasi data sensor yang digunakan dalam perhitungan lebih besar, nilai rata-rata (average) menjadi lebih representatif

Sebagai contoh:

rata-rata suhu (suhu_avg), rata-rata AQI (aqi_avg), total curah hujan (hujan_total)

akan dihitung dari lebih banyak data, sehingga hasilnya lebih mendekati kondisi sebenarnya.

- Dampak terhadap latensi hasil

Namun peningkatan ukuran batch juga menyebabkan latensi hasil menjadi lebih tinggi.m Hal ini terjadi karena sistem harus menunggu lebih lama hingga buffer penuh sebelum menjalankan proses MapReduce.

Perbandingan waktu:
| BATCH_SIZE | Waktu tunggu |
| ---------- | ------------ |
| 20         | ±4 detik     |
| 100        | ±20 detik    |

Artinya, pengguna harus menunggu lebih lama untuk melihat hasil analisis terbaru.
