# Petunjuk Mengisi Tabel Hasil (CSV)

Satu tabel = satu file CSV. Unduh templatenya, ganti isinya dengan datamu, lalu daftarkan di `input.json`.

## Template
- `template_perbandingan.csv`: baris = model atau kondisi yang dibandingkan (misalnya akurasi dan F1 tiap model)
- `template_deret_waktu.csv`: baris = periode berurutan (misalnya data aktual dan prediksi per bulan)

## Aturan format
1. Format **CSV UTF-8** dengan **pemisah koma**.
2. Baris 1 adalah judul kolom. Judul harus unik, tidak boleh kosong, tidak ada sel digabung.
3. **Kolom pertama adalah label** (nama model, kondisi, atau periode). Isinya harus unik dan tidak kosong.
4. **Kolom lainnya hanya angka**:
   - pemisah desimal memakai **titik** (84.2, bukan 84,2)
   - tanpa simbol atau satuan (84.2, bukan 84.2% atau 84.2 persen)
   - tanpa pemisah ribuan (1250, bukan 1.250 atau 1,250)
   - tidak ada sel kosong
5. Minimal **2 baris data**. Disarankan tidak lebih dari 50 baris (tabel besar tetap disisipkan utuh, tapi agen hanya menerima ringkasannya).
6. **Satuan dan keterangan tidak ditulis di CSV**, melainkan di `input.json`.

## Cara mendaftarkan di `input.json`
```json
{
  "id": "T1",
  "keterangan": "Perbandingan akurasi dan F1-score pada data uji",
  "satuan": "persen",
  "file": "results/t1.csv",
  "tipe": "perbandingan",
  "kolom_label": "model"
}
```
- `tipe`: `perbandingan` atau `deret_waktu`
- `kolom_label`: opsional; jika tidak diisi, kolom pertama dipakai sebagai label

## Menyimpan dari Excel atau Google Sheets
- Simpan sebagai **CSV UTF-8 (comma delimited)**.
- Excel dengan pengaturan regional Indonesia sering memakai titik koma sebagai pemisah dan koma sebagai desimal. Setelah menyimpan, buka CSV di editor teks (misalnya Notepad) dan pastikan pemisahnya koma dan desimalnya titik.
- Jika format salah, sistem menolak file itu dan menampilkan pesan yang menjelaskan baris dan kolom yang bermasalah.
