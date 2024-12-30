kunci untuk login admin adalah credentials.json
kunci untuk login user tersimpan dalam .streamlit/secrets.toml
kunci akses spreadsheet tersimpan dalam .streamlit/secrets.toml

Menambah admin, hanya perlu menambahkan di spreadsheet

Menambah users, selain menambahkan di preadsheet, jangan lupa juga untuk menambah service account. Otomatis, data service account di secrets.toml harus ditambahkan. Ingat juga untuk menyesuaikan kode di User_Operation.py

tombol refresh akan otomatis mereset segala aktivitas

Ketika upload ke server, credentials.json harus disertakan

folder ini belum di-git btw, karena ini copasan

Hal-hal yang masih harus dikerjakan:
- tombol reset cache
- belum semua activity penting punya system update logs (cek lagi aja)
- UI/UX masih bisa ditingkatkan


FILE BERIKUT BERISI INFORMASI RAHASIA, PASTIKAN TIDAK TERSEBAR
- client_secrets
- credentials
- service-account-for-user
- spreadsheet-connector
- spreadsheet: https://docs.google.com/spreadsheets/d/1fMFu-6pcs8Fvi9vLrsaVEt3-EXWDpLIvFUt0aNV0TfI/edit?pli=1&gid=0#gid=0