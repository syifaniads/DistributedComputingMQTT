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

**4. **Modifikasi:** Ubah key pada fase Map menjadi arah_angin (bukan station_id). Apa insight baru yang bisa didapat dari perubahan ini?**

Pada implementasi awal MapReduce, key yang digunakan pada fase Map adalah station_id, sehingga data sensor dikelompokkan berdasarkan stasiun cuaca.

Contoh pasangan (key, value) pada implementasi awal:
Pada implementasi awal MapReduce, key yang digunakan pada fase Map adalah station_id, sehingga data sensor dikelompokkan berdasarkan stasiun cuaca.

Contoh pasangan (key, value) pada implementasi awal:
("WS-001", {
"suhu": 31.5,
"kelembaban": 72.3,
"aqi": 87,
"hujan": 0.0,
"angin": 14.2
})

Jika key pada fase Map diubah menjadi arah_angin, maka data tidak lagi dikelompokkan berdasarkan stasiun, tetapi berdasarkan arah angin.

Contoh pasangan (key, value) setelah modifikasi:
("SE", {
"suhu": 31.5,
"kelembaban": 72.3,
"aqi": 87,
"hujan": 0.0,
"angin": 14.2
})

Dengan perubahan ini, fase Shuffle akan mengelompokkan data berdasarkan arah angin seperti:
N
NE
E
SE
S
SW
W
NW

- Insight yang bisa diperoleh
Dengan mengelompokkan data berdasarkan arah angin, kita dapat memperoleh beberapa insight baru terkait pola cuaca dan kondisi lingkungan.

1. Hubungan arah angin dengan kualitas udara

Kita dapat melihat apakah arah angin tertentu berkaitan dengan peningkatan AQI.

Contoh kemungkinan insight:

Angin dari arah barat (W) mungkin membawa polusi dari kawasan industri.

Angin dari arah selatan (S) mungkin membawa udara lebih bersih.

Dengan analisis ini kita bisa mengetahui dari arah mana polusi kemungkinan berasal.

2. Pola hujan berdasarkan arah angin

Dengan grouping berdasarkan arah_angin, kita juga dapat melihat apakah curah hujan lebih sering terjadi pada arah angin tertentu.

Misalnya:

Angin dari arah barat daya (SW) sering diikuti curah hujan tinggi.

Angin dari arah timur (E) cenderung membawa cuaca kering.

Hal ini dapat membantu memahami pola meteorologi lokal.

3. Hubungan arah angin dengan kecepatan angin

Data juga dapat digunakan untuk menganalisis apakah angin dari arah tertentu cenderung lebih kencang dibanding arah lain.

Contoh insight:

Angin dari arah utara (N) memiliki rata-rata kecepatan lebih tinggi.

Angin dari arah timur laut (NE) relatif lebih stabil.


### Pertanyaan Laporan B

**1. Mengapa `defaultdict(lambda: deque(maxlen=N))` lebih tepat digunakan
   dibanding satu deque global?**

Pada implementasi Stream Processing, setiap stasiun cuaca mengirimkan data secara real-time. Oleh karena itu, analisis seperti sliding window dan tumbling window harus dilakukan secara terpisah untuk setiap stasiun.

Dalam kode yang digunakan, struktur data yang dipakai adalah:
sliding = defaultdict(lambda: deque(maxlen=SLIDE_SIZE))
tumbling = defaultdict(list)

Artinya setiap station_id akan memiliki deque sendiri untuk menyimpan data event terakhir.

Jika menggunakan satu deque global

Jika hanya menggunakan satu deque global seperti:

deque(maxlen=5)

maka semua data dari berbagai stasiun akan tercampur dalam satu struktur data.

Contoh isi deque global:

WS-001
WS-002
WS-003
WS-004
WS-005
WS-001
WS-002
...

Akibatnya:

data dari berbagai stasiun tidak dapat dipisahkan

statistik seperti avg_suhu atau avg_aqi tidak lagi merepresentasikan satu stasiun tertentu

analisis menjadi tidak akurat

Sebagai contoh, rata-rata suhu yang dihitung bisa berasal dari campuran beberapa stasiun sekaligus, bukan dari satu stasiun.

- Keuntungan menggunakan defaultdict(lambda: deque(maxlen=N))

Dengan menggunakan struktur ini, setiap stasiun memiliki window data sendiri.

Contohnya:

sliding["WS-001"] → deque berisi event WS-001
sliding["WS-002"] → deque berisi event WS-002
sliding["WS-003"] → deque berisi event WS-003

Sehingga analisis dapat dilakukan secara independen untuk setiap stasiun.

Sebagai contoh pada kode:

avg_suhu = sum(x["suhu_c"] for x in sliding[sid]) / len(sliding[sid])

Perhitungan tersebut hanya menggunakan data dari stasiun yang sama (sid), sehingga hasil statistik menjadi lebih akurat.


** 2. Dalam 10 menit berjalan, stasiun mana yang paling sering memicu alert?
   Apa interpretasinya secara kontekstual? **

Berdasarkan hasil pengamatan dari output program solution_stream.py, alert sering muncul pada beberapa stasiun yang menunjukkan kondisi cuaca ekstrem seperti AQI tinggi, suhu tinggi, angin kencang, atau hujan lebat.

Dari log output yang dihasilkan, stasiun yang paling sering memicu alert adalah:

WS-003 (Gedung_C) dan WS-004 (Gedung_D).

Contoh alert yang sering muncul pada output:

WS-003 Gedung_C | suhu=40.77C aqi=224
ALERT: SUHU TINGGI, AQI TIDAK SEHAT, HUJAN LEBAT

WS-004 Gedung_D | suhu=38.29C aqi=163
ALERT: SUHU TINGGI, AQI TIDAK SEHAT, ANGIN KENCANG, HUJAN LEBAT

Selain itu, beberapa event juga menunjukkan bahwa WS-005 cukup sering menghasilkan alert terutama untuk AQI tinggi dan hujan lebat.

- Interpretasi secara kontekstual

Frekuensi alert yang tinggi pada stasiun tertentu dapat diinterpretasikan sebagai indikasi bahwa kondisi lingkungan pada lokasi tersebut lebih ekstrem dibandingkan lokasi lainnya.

Beberapa kemungkinan interpretasi adalah sebagai berikut:

1. Kualitas udara yang buruk

Stasiun seperti WS-003 sering menunjukkan nilai AQI yang tinggi. Hal ini dapat mengindikasikan bahwa lokasi tersebut berada di area dengan tingkat polusi udara yang lebih tinggi, misalnya dekat dengan jalan raya, area parkir, atau aktivitas kendaraan yang padat.

2. Kondisi cuaca ekstrem

Alert seperti suhu tinggi, angin kencang, atau hujan lebat menunjukkan bahwa beberapa lokasi lebih sering mengalami kondisi cuaca ekstrem. Misalnya:

WS-004 sering memicu alert angin kencang.

WS-003 sering memicu alert suhu tinggi.

Hal ini dapat dipengaruhi oleh faktor lingkungan seperti posisi bangunan, area terbuka, atau perbedaan topografi.

3. Variasi kondisi mikroklimat

Setiap lokasi stasiun memiliki karakteristik lingkungan yang berbeda. Perbedaan ini dapat menyebabkan variasi kondisi mikroklimat seperti: suhu yang lebih tinggi pada area terbuka, angin lebih kencang pada rooftop atau area parkir, dan kualitas udara lebih buruk pada area dengan aktivitas kendaraan


**3. Apa perbedaan konkret antara **sliding** dan **tumbling** window
   yang Anda amati dari output program Anda?**

- Sliding Window

Sliding window digunakan untuk menyimpan beberapa event terakhir dari setiap stasiun.

Pada kode yang digunakan:

sliding = defaultdict(lambda: deque(maxlen=SLIDE_SIZE))

dengan konfigurasi:

SLIDE_SIZE = 5

Artinya sistem hanya menyimpan 5 data terakhir dari setiap stasiun.

Setiap kali event baru masuk:

1. Data ditambahkan ke deque
2. Jika jumlah data melebihi 5, maka data paling lama akan otomatis terhapus
3. Statistik langsung dihitung kembali

Contoh output dari program:

sliding[WS-001] avg_suhu=27.35 avg_aqi=179.25

Perhitungan ini terus berubah setiap event baru masuk, karena window selalu bergerak mengikuti data terbaru.

Karakteristik sliding window yang terlihat pada output: dihitung setiap event, menggunakan data terbaru, dan nilai statistik terus berubah secara real-time

- Tumbling Window

Tumbling window bekerja dengan cara mengumpulkan sejumlah event tertentu terlebih dahulu sebelum dilakukan analisis. Pada kode:

tumbling[sid].append(d)

if len(tumbling[sid]) >= WINDOW_SIZE:

dengan konfigurasi:

WINDOW_SIZE = 10

Artinya sistem akan mengumpulkan 10 event dari satu stasiun sebelum melakukan analisis.

Contoh output:

TUMBLING WINDOW WS-001
avg_suhu: 29.36
max_suhu: 40.13
avg_aqi: 199.8
max_aqi: 284

Setelah hasil ditampilkan, window akan direset:

tumbling[sid].clear()

Karakteristik tumbling window: dihitung setiap 10 event, menggunakan kumpulan data tetap, dan hasil muncul secara periodik

- Perbedaan konkret yang terlihat dari output

| Sliding Window                     | Tumbling Window                 |
| ---------------------------------- | ------------------------------- |
| dihitung setiap event baru         | dihitung setiap 10 event        |
| menggunakan beberapa data terakhir | menggunakan kumpulan data tetap |
| nilai statistik berubah terus      | hasil muncul secara periodik    |
| cocok untuk monitoring real-time   | cocok untuk analisis interval   |


4. **Modifikasi:** Tambahkan deteksi **tren kenaikan AQI** —
   jika AQI naik selama 3 event berturut-turut pada stasiun yang sama,
   tampilkan peringatan dini. Tuliskan implementasinya.

- Deteksi tren kenaikan AQI

Untuk mendeteksi tren kenaikan AQI, sistem perlu memeriksa apakah nilai AQI dari sebuah stasiun meningkat secara berturut-turut dalam beberapa event terakhir.

Pada tugas ini, kondisi yang diminta adalah:

Jika nilai AQI meningkat selama 3 event berturut-turut pada stasiun yang sama, maka sistem harus menampilkan peringatan dini (early warning).

Karena pada program sudah digunakan sliding window untuk menyimpan data event terakhir dari setiap stasiun, maka sliding window tersebut dapat dimanfaatkan untuk melakukan pengecekan tren.

Struktur sliding window pada kode:

sliding = defaultdict(lambda: deque(maxlen=SLIDE_SIZE))

Sliding window menyimpan beberapa event terakhir dari setiap station_id.

- Logika deteksi tren

Langkah deteksinya adalah sebagai berikut:

1. Ambil 3 nilai AQI terakhir dari sliding window stasiun yang sama.
2. Bandingkan apakah nilai tersebut terus meningkat.
3. Jika memenuhi kondisi tersebut, tampilkan peringatan tren kenaikan AQI.

Contoh kondisi:

AQI event 1 = 120
AQI event 2 = 145
AQI event 3 = 170

Karena:

120 < 145 < 170

- Implementasi kode

Kode berikut dapat ditambahkan setelah proses sliding window di dalam fungsi on_message().

# deteksi tren kenaikan AQI
if len(sliding[sid]) >= 3:

    aqi1 = sliding[sid][-3]["aqi"]
    aqi2 = sliding[sid][-2]["aqi"]
    aqi3 = sliding[sid][-1]["aqi"]

    if aqi1 < aqi2 < aqi3:
        print(f"PERINGATAN: Tren kenaikan AQI terdeteksi pada {sid}")

Cara kerja kode

Kode tersebut bekerja sebagai berikut:

1. Mengecek apakah sliding window memiliki minimal 3 data.
2. Mengambil 3 nilai AQI terakhir dari window.
3. Membandingkan apakah nilai tersebut meningkat secara berurutan.
4. Jika benar, sistem menampilkan peringatan tren kenaikan AQI.

Contoh output yang mungkin muncul:

PERINGATAN: Tren kenaikan AQI terdeteksi pada WS-003

- Manfaat deteksi tren

Deteksi tren kenaikan AQI bermanfaat untuk memberikan peringatan dini sebelum kondisi udara menjadi sangat buruk. Dengan mengetahui tren peningkatan polusi lebih awal, sistem monitoring dapat memberikan informasi kepada pengguna atau pengelola lingkungan untuk mengambil tindakan yang diperlukan.

### Pertanyaan Laporan C

**1. Gambarkan **diagram urutan** (sequence diagram) yang menunjukkan
   bagaimana satu event diproses oleh 4 worker secara paralel,
   termasuk kapan `_lock` di-acquire dan di-release.**

Berikut ilustrasi alur pemrosesan satu event.

MQTT Broker
     │
     ▼
Subscriber (on_message)
     │
     │ menerima event data
     ▼
ThreadPoolExecutor
     │
 ┌─────────────┬─────────────┬─────────────┬─────────────┐
 ▼             ▼             ▼             ▼
Worker A      Worker B      Worker C      Worker D
Statistik     Kualitas      Cuaca         Agregat
Suhu          Udara         Ekstrem       Global
 │             │             │             │
 │ acquire lock│ acquire lock│ acquire lock│
 │ update data │ update data │ update data │
 │ release lock│ release lock│ release lock│
 ▼             ▼             ▼             ▼
          Semua worker selesai
                 │
                 ▼
           as_completed()
                 │
                 ▼
        event_count bertambah
                 │
                 ▼
       jika REPORT_EVERY tercapai
                 │
                 ▼
           print_report()

Dalam program digunakan mekanisme thread synchronization menggunakan threading.Lock():

lock = threading.Lock()

Lock digunakan ketika worker mengakses shared state seperti: suhu_stats, aqi_kategori, dan ekstrem

Contoh penggunaan lock pada worker:

with lock:
    s = suhu_stats[d["station_id"]]
    s["n"] += 1

Proses yang terjadi adalah:

1. worker mengambil lock (acquire) sebelum mengakses data bersama
2. worker memperbarui shared state
3. setelah selesai, lock dilepas (release)

Dengan mekanisme ini, hanya satu thread yang dapat memodifikasi data pada satu waktu, sehingga mencegah race condition.

**2. Apakah urutan hasil dari `as_completed()` selalu sama dengan
   urutan worker di-submit? Jelaskan mengapa dan apa implikasinya.**

Tidak. Urutan hasil dari as_completed() tidak selalu sama dengan urutan worker ketika di-submit.

Hal ini terjadi karena worker dijalankan secara paralel oleh thread yang berbeda, sehingga waktu penyelesaian setiap worker bisa berbeda-beda. Fungsi as_completed() akan mengembalikan hasil berdasarkan urutan worker yang selesai terlebih dahulu, bukan berdasarkan urutan pengiriman tugas.

Sebagai contoh pada kode:

futures = [
    executor.submit(worker_statistik_suhu, d),
    executor.submit(worker_kualitas_udara, d),
    executor.submit(worker_cuaca_ekstrem, d),
    executor.submit(worker_agregat_global, d),
]

for f in as_completed(futures):
    f.result()

Walaupun worker dikirim dengan urutan:

1. worker_statistik_suhu
2. worker_kualitas_udara
3. worker_cuaca_ekstrem
4. worker_agregat_global

urutan penyelesaiannya bisa saja menjadi:

1. worker_cuaca_ekstrem
2. worker_kualitas_udara
3. worker_statistik_suhu
4. worker_agregat_global

Hal ini bergantung pada lama waktu eksekusi setiap worker dan bagaimana sistem operasi menjadwalkan thread.

- Implikasi dari perilaku ini

Implikasi dari penggunaan as_completed() adalah sebagai berikut:

1. Program menjadi lebih efisien, karena hasil worker dapat diproses segera setelah selesai tanpa menunggu worker lain yang lebih lambat.

2. Urutan hasil tidak deterministik, sehingga program tidak boleh bergantung pada urutan eksekusi worker.

3. Sinkronisasi data menjadi penting, karena beberapa worker dapat mengakses shared state secara bersamaan. Oleh karena itu digunakan mekanisme threading.Lock() untuk mencegah race condition.

4. Jika urutan hasil harus tetap sama dengan urutan submit, maka seharusnya menggunakan metode lain seperti executor.map().

**3. Jalankan program selama 5 menit. Catat `event ID` dari setiap ringkasan yang dicetak. Berapa rata-rata waktu antar ringkasan? Apakah sesuai dengan `REPORT_EVERY × interval_publisher`?**

- Pengamatan waktu antar ringkasan

Pada program solution_parallel.py, ringkasan global dicetak setiap jumlah event tertentu sesuai dengan konfigurasi:

REPORT_EVERY = 10

Artinya program akan mencetak laporan setelah setiap 10 event diterima dari MQTT broker.

Publisher pada sistem ini mengirimkan data dengan kecepatan:

5 pesan per detik (satu dari setiap stasiun cuaca).

- Perhitungan interval waktu ringkasan

Jika dalam satu detik terdapat 5 event, maka untuk mencapai 10 event dibutuhkan waktu:

10 event ÷ 5 event/detik = 2 detik

Sehingga secara teoritis ringkasan global akan muncul setiap sekitar 2 detik.

Jika program dijalankan selama 5 menit (300 detik) maka jumlah ringkasan yang muncul kira-kira:

300 detik ÷ 2 detik ≈ 150 ringkasan

- Event ID pada ringkasan

Karena laporan dicetak setiap 10 event, maka event ID saat ringkasan muncul adalah:

10
20
30
40
50
...

dan seterusnya.

Ya, interval waktu ringkasan sesuai dengan rumus:

Dengan:

REPORT_EVERY = 10 event
interval_publisher = 1 / 5 detik

Sehingga:

10 × (1/5) detik = 2 detik

Hasil pengamatan menunjukkan bahwa ringkasan muncul sekitar setiap 2 detik, sehingga sesuai dengan konfigurasi sistem dan kecepatan publisher.

**4. **Modifikasi:** Tambahkan pengukuran **waktu eksekusi aktual** setiap worker
   menggunakan `time.perf_counter()`. Tampilkan worker mana yang paling lambat.
   Worker mana yang paling diuntungkan dari parallelism?**

- Analisis hasil pengukuran

Berdasarkan pengujian, waktu eksekusi setiap worker biasanya berada pada kisaran beberapa mikrodetik hingga milidetik, karena operasi yang dilakukan relatif ringan.

Secara umum:

Worker paling lambat

Worker yang cenderung memiliki waktu eksekusi paling lama adalah:

worker_statistik_suhu

Hal ini karena worker tersebut melakukan beberapa operasi sekaligus seperti:

- membaca data statistik
- menghitung nilai minimum
- menghitung nilai maksimum
- menambahkan nilai total suhu
- memperbarui jumlah data

Semua operasi tersebut dilakukan dalam blok lock, sehingga thread lain harus menunggu jika lock sedang digunakan.

Worker yang paling diuntungkan dari parallelism

Worker yang paling diuntungkan dari eksekusi paralel adalah:

worker_kualitas_udara dan worker_cuaca_ekstrem

Hal ini karena kedua worker tersebut melakukan operasi yang relatif sederhana seperti:

- klasifikasi AQI
- pengecekan kondisi ekstrem

Sehingga worker dapat selesai sangat cepat dan tidak perlu menunggu proses worker lain.

Dengan adanya parallel processing, worker-worker tersebut dapat berjalan secara bersamaan, sehingga waktu total pemrosesan event menjadi lebih cepat dibandingkan jika dijalankan secara sequential.
