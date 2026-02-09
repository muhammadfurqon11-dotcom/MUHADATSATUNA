import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import base64
import io
import google.generativeai as genai  # Integrasi dengan Google Gemini API

# Konfigurasi API Key untuk Gemini (ganti dengan API key Anda)
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "YOUR_API_KEY_HERE")  # Gunakan Streamlit secrets untuk produksi
genai.configure(api_key=GEMINI_API_KEY)

# Inisialisasi model Gemini
model = genai.GenerativeModel('gemini-pro')  # Atau model lain seperti 'gemini-1.5-pro'

# Inisialisasi database sederhana menggunakan SQLite (untuk demo, data hilang saat restart app)
conn = sqlite3.connect(':memory:', check_same_thread=False)
cursor = conn.cursor()

# Buat tabel-tabel dasar (sama seperti sebelumnya, tanpa users)
cursor.execute('''CREATE TABLE IF NOT EXISTS cases (id INTEGER PRIMARY KEY, title TEXT, description TEXT, user_id INTEGER)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS discussions (id INTEGER PRIMARY KEY, case_id INTEGER, user_id INTEGER, comment TEXT, timestamp TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS assignments (id INTEGER PRIMARY KEY, title TEXT, description TEXT, due_date TEXT, user_id INTEGER)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS submissions (id INTEGER PRIMARY KEY, assignment_id INTEGER, user_id INTEGER, content TEXT, timestamp TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS learning_logs (id INTEGER PRIMARY KEY, user_id INTEGER, case_id INTEGER, log TEXT, timestamp TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS reports (id INTEGER PRIMARY KEY, user_id INTEGER, content TEXT, timestamp TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS assessments (id INTEGER PRIMARY KEY, title TEXT, questions TEXT)''')  # questions as JSON string for simplicity
cursor.execute('''CREATE TABLE IF NOT EXISTS quizzes (id INTEGER PRIMARY KEY, title TEXT, questions TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS evaluations (id INTEGER PRIMARY KEY, user_id INTEGER, competency TEXT, score INTEGER)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS forums (id INTEGER PRIMARY KEY, topic TEXT, user_id INTEGER)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS forum_posts (id INTEGER PRIMARY KEY, forum_id INTEGER, user_id INTEGER, content TEXT, timestamp TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY, from_user INTEGER, to_user INTEGER, content TEXT, timestamp TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS materials (id INTEGER PRIMARY KEY, title TEXT, type TEXT, content BLOB)''')  # content as BLOB for files
cursor.execute('''CREATE TABLE IF NOT EXISTS progress (id INTEGER PRIMARY KEY, user_id INTEGER, module TEXT, status TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS attendance (id INTEGER PRIMARY KEY, user_id INTEGER, date TEXT, status TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS simulations (id INTEGER PRIMARY KEY, title TEXT, description TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS notifications (id INTEGER PRIMARY KEY, user_id INTEGER, message TEXT, timestamp TEXT)''')
conn.commit()

# Asumsikan user_id default untuk demo (karena login dihapus)
user_id = 1
role = 'admin'  # Default ke admin agar semua fitur accessible untuk demo

# Fungsi untuk integrasi Gemini: Generate saran atau analisis
def generate_gemini_response(prompt):
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

# App utama
st.title("Platform Pembelajaran Interaktif \"MUHADATSATUNA\" mari belajar kalam dengan menyenangkan")

# Sidebar navigasi
st.sidebar.title("Menu")
pages = [
    "Home",
    "1. Pembelajaran Klinis & Kasus",
    "2. Asesmen & Evaluasi",
    "3. Komunikasi & Kolaborasi",
    "4. Manajemen Konten",
    "5. Monitoring & Tracking",
    "6. Laboratorium Virtual/Simulasi",
    "7. Manajemen Pengguna",
    "8. Dukungan Teknis"
]
page = st.sidebar.selectbox("Pilih Kategori", pages)

if page == "Home":
    st.header("Selamat Datang di Platform Pembelajaran Klinis")
    st.write("Ini adalah aplikasi demo untuk platform pendidikan klinis dengan integrasi AI Gemini untuk analisis dan generasi konten. Pilih menu di sidebar untuk mengeksplorasi fitur.")

elif page == "1. Pembelajaran Klinis & Kasus":
    st.header("Fitur Pembelajaran Klinis & Kasus")
    subpage = st.selectbox("Pilih Sub Fitur", ["Diskusi Kasus", "Manajemen Tugas", "Dokumentasi Pembelajaran", "Pelaporan Klinis Digital"])
    
    if subpage == "Diskusi Kasus":
        st.subheader("Diskusi Kasus")
        case_title = st.text_input("Judul Kasus")
        case_desc = st.text_area("Deskripsi Kasus")
        if st.button("Buat Kasus Baru"):
            cursor.execute("INSERT INTO cases (title, description, user_id) VALUES (?, ?, ?)", (case_title, case_desc, user_id))
            conn.commit()
            st.success("Kasus dibuat!")
        
        st.write("Daftar Kasus:")
        cases = pd.read_sql("SELECT * FROM cases", conn)
        st.dataframe(cases)
        
        selected_case = st.selectbox("Pilih Kasus untuk Diskusi", cases['id'] if not cases.empty else [])
        if selected_case:
            comment = st.text_area("Tambah Komentar")
            if st.button("Kirim Komentar"):
                timestamp = datetime.now().isoformat()
                cursor.execute("INSERT INTO discussions (case_id, user_id, comment, timestamp) VALUES (?, ?, ?, ?)", (selected_case, user_id, comment, timestamp))
                conn.commit()
                st.success("Komentar dikirim!")
            
            discussions = pd.read_sql("SELECT * FROM discussions WHERE case_id=?", conn, params=(selected_case,))
            st.write("Diskusi:")
            st.dataframe(discussions)
            
            # Integrasi Gemini: Analisis kasus dengan AI
            if st.button("Analisis Kasus dengan Gemini AI"):
                cursor.execute("SELECT description FROM cases WHERE id=?", (selected_case,))
                desc = cursor.fetchone()[0]
                prompt = f"Analisis kasus klinis berikut: {desc}. Berikan saran diagnosis dan treatment."
                ai_response = generate_gemini_response(prompt)
                st.write("Analisis AI (Gemini):")
                st.write(ai_response)
    
    elif subpage == "Manajemen Tugas":
        st.subheader("Manajemen Tugas")
        ass_title = st.text_input("Judul Tugas")
        ass_desc = st.text_area("Deskripsi Tugas")
        due_date = st.date_input("Batas Waktu")
        if st.button("Buat Tugas Baru"):
            cursor.execute("INSERT INTO assignments (title, description, due_date, user_id) VALUES (?, ?, ?, ?)", (ass_title, ass_desc, str(due_date), user_id))
            conn.commit()
            st.success("Tugas dibuat!")
        
        assignments = pd.read_sql("SELECT * FROM assignments", conn)
        st.write("Daftar Tugas:")
        st.dataframe(assignments)
        
        selected_ass = st.selectbox("Pilih Tugas untuk Submit", assignments['id'] if not assignments.empty else [])
        if selected_ass:
            content = st.text_area("Isi Submission")
            if st.button("Submit Tugas"):
                timestamp = datetime.now().isoformat()
                cursor.execute("INSERT INTO submissions (assignment_id, user_id, content, timestamp) VALUES (?, ?, ?, ?)", (selected_ass, user_id, content, timestamp))
                conn.commit()
                st.success("Submission dikirim!")
            
            subs = pd.read_sql("SELECT * FROM submissions WHERE assignment_id=?", conn, params=(selected_ass,))
            st.write("Submissions:")
            st.dataframe(subs)
    
    elif subpage == "Dokumentasi Pembelajaran":
        st.subheader("Dokumentasi Pembelajaran")
        selected_case = st.selectbox("Pilih Kasus", pd.read_sql("SELECT id FROM cases", conn)['id'])
        log = st.text_area("Catatan Pembelajaran")
        if st.button("Simpan Log"):
            timestamp = datetime.now().isoformat()
            cursor.execute("INSERT INTO learning_logs (user_id, case_id, log, timestamp) VALUES (?, ?, ?, ?)", (user_id, selected_case, log, timestamp))
            conn.commit()
            st.success("Log disimpan!")
        
        logs = pd.read_sql("SELECT * FROM learning_logs WHERE user_id=?", conn, params=(user_id,))
        st.write("Log Pembelajaran:")
        st.dataframe(logs)
    
    elif subpage == "Pelaporan Klinis Digital":
        st.subheader("Pelaporan Klinis Digital")
        report_content = st.text_area("Isi Laporan")
        if st.button("Kirim Laporan"):
            timestamp = datetime.now().isoformat()
            cursor.execute("INSERT INTO reports (user_id, content, timestamp) VALUES (?, ?, ?)", (user_id, report_content, timestamp))
            conn.commit()
            st.success("Laporan dikirim!")
        
        reports = pd.read_sql("SELECT * FROM reports", conn)
        st.write("Daftar Laporan:")
        st.dataframe(reports)

elif page == "2. Asesmen & Evaluasi":
    st.header("Fitur Asesmen & Evaluasi")
    subpage = st.selectbox("Pilih Sub Fitur", ["Asesmen Daring", "Kuis Interaktif", "Evaluasi Kompetensi"])
    
    if subpage == "Asesmen Daring":
        st.subheader("Asesmen Daring")
        ass_title = st.text_input("Judul Asesmen")
        questions = st.text_area("Pertanyaan (JSON format: [{'q':'pertanyaan', 'a':'jawaban'}]")  # Sederhana
        if st.button("Buat Asesmen"):
            cursor.execute("INSERT INTO assessments (title, questions) VALUES (?, ?)", (ass_title, questions))
            conn.commit()
            st.success("Asesmen dibuat!")
        
        assessments = pd.read_sql("SELECT * FROM assessments", conn)
        st.write("Daftar Asesmen:")
        st.dataframe(assessments)
    
    elif subpage == "Kuis Interaktif":
        st.subheader("Kuis Interaktif")
        quiz_title = st.text_input("Judul Kuis")
        topic = st.text_input("Topik untuk Generasi Kuis dengan Gemini")
        if st.button("Generate Kuis dengan Gemini"):
            prompt = f"Generate 5 soal kuis tentang {topic} dalam format JSON: [{'q':'pertanyaan', 'a':'jawaban'}]"
            questions = generate_gemini_response(prompt)
            st.write("Kuis Generated:")
            st.write(questions)
        
        questions_input = st.text_area("Pertanyaan (JSON format)", value=questions if 'questions' in locals() else "")
        if st.button("Buat Kuis"):
            cursor.execute("INSERT INTO quizzes (title, questions) VALUES (?, ?)", (quiz_title, questions_input))
            conn.commit()
            st.success("Kuis dibuat!")
        
        quizzes = pd.read_sql("SELECT * FROM quizzes", conn)
        st.write("Daftar Kuis:")
        st.dataframe(quizzes)
    
    elif subpage == "Evaluasi Kompetensi":
        st.subheader("Evaluasi Kompetensi")
        competency = st.text_input("Kompetensi")
        score = st.number_input("Skor", 0, 100)
        if st.button("Simpan Evaluasi"):
            cursor.execute("INSERT INTO evaluations (user_id, competency, score) VALUES (?, ?, ?)", (user_id, competency, score))
            conn.commit()
            st.success("Evaluasi disimpan!")
        
        evals = pd.read_sql("SELECT * FROM evaluations", conn)
        st.write("Daftar Evaluasi:")
        st.dataframe(evals)

elif page == "3. Komunikasi & Kolaborasi":
    st.header("Fitur Komunikasi & Kolaborasi")
    subpage = st.selectbox("Pilih Sub Fitur", ["Forum Diskusi", "Chat/Pesan Langsung", "Video Conference Integration"])
    
    if subpage == "Forum Diskusi":
        st.subheader("Forum Diskusi")
        topic = st.text_input("Topik Forum")
        if st.button("Buat Forum Baru"):
            cursor.execute("INSERT INTO forums (topic, user_id) VALUES (?, ?)", (topic, user_id))
            conn.commit()
            st.success("Forum dibuat!")
        
        forums = pd.read_sql("SELECT * FROM forums", conn)
        st.write("Daftar Forum:")
        st.dataframe(forums)
        
        selected_forum = st.selectbox("Pilih Forum", forums['id'] if not forums.empty else [])
        if selected_forum:
            post_content = st.text_area("Tambah Post")
            if st.button("Kirim Post"):
                timestamp = datetime.now().isoformat()
                cursor.execute("INSERT INTO forum_posts (forum_id, user_id, content, timestamp) VALUES (?, ?, ?, ?)", (selected_forum, user_id, post_content, timestamp))
                conn.commit()
                st.success("Post dikirim!")
            
            posts = pd.read_sql("SELECT * FROM forum_posts WHERE forum_id=?", conn, params=(selected_forum,))
            st.write("Posts:")
            st.dataframe(posts)
    
    elif subpage == "Chat/Pesan Langsung":
        st.subheader("Chat/Pesan Langsung")
        to_user_id = st.number_input("Kirim ke User ID", min_value=1)
        message = st.text_area("Pesan")
        if st.button("Kirim Pesan"):
            timestamp = datetime.now().isoformat()
            cursor.execute("INSERT INTO messages (from_user, to_user, content, timestamp) VALUES (?, ?, ?, ?)", (user_id, to_user_id, message, timestamp))
            conn.commit()
            st.success("Pesan dikirim!")
        
        messages = pd.read_sql("SELECT * FROM messages WHERE to_user=? OR from_user=?", conn, params=(user_id, user_id))
        st.write("Pesan:")
        st.dataframe(messages)
    
    elif subpage == "Video Conference Integration":
        st.subheader("Video Conference Integration")
        st.write("Integrasi dengan Zoom atau Google Meet. Masukkan link meeting:")
        link = st.text_input("Link Video Conference")
        if link:
            st.write(f"Link: {link} (Integrasi placeholder - gunakan API eksternal untuk real implementasi)")

elif page == "4. Manajemen Konten":
    st.header("Fitur Manajemen Konten")
    subpage = st.selectbox("Pilih Sub Fitur", ["Library Materi", "Upload Dokumen", "Multimedia Integration", "E-book/BSE"])
    
    if subpage == "Library Materi":
        st.subheader("Library Materi")
        materials = pd.read_sql("SELECT id, title, type FROM materials", conn)
        st.write("Daftar Materi:")
        st.dataframe(materials)
    
    elif subpage == "Upload Dokumen":
        st.subheader("Upload Dokumen")
        title = st.text_input("Judul Dokumen")
        uploaded_file = st.file_uploader("Upload File")
        if uploaded_file and st.button("Upload"):
            content = uploaded_file.read()
            file_type = uploaded_file.type
            cursor.execute("INSERT INTO materials (title, type, content) VALUES (?, ?, ?)", (title, file_type, content))
            conn.commit()
            st.success("Dokumen diupload!")
    
    elif subpage == "Multimedia Integration":
        st.subheader("Multimedia Integration")
        st.write("Dukungan untuk video, audio, gambar. Upload di atas dan tampilkan di sini (placeholder).")
        selected_material = st.selectbox("Pilih Materi", pd.read_sql("SELECT id FROM materials", conn)['id'])
        if selected_material:
            cursor.execute("SELECT type, content FROM materials WHERE id=?", (selected_material,))
            mat_type, content = cursor.fetchone()
            if 'image' in mat_type:
                st.image(io.BytesIO(content))
            elif 'video' in mat_type:
                st.video(io.BytesIO(content))
            elif 'audio' in mat_type:
                st.audio(io.BytesIO(content))
            else:
                st.download_button("Download", content, file_name="file")
    
    elif subpage == "E-book/BSE":
        st.subheader("E-book/BSE")
        st.write("Akses ke e-book (placeholder - integrasi dengan library eksternal).")

elif page == "5. Monitoring & Tracking":
    st.header("Fitur Monitoring & Tracking")
    subpage = st.selectbox("Pilih Sub Fitur", ["Progress Tracking", "Dashboard Analytics", "Attendance Tracking", "Learning Analytics"])
    
    if subpage == "Progress Tracking":
        st.subheader("Progress Tracking")
        module = st.text_input("Modul")
        status = st.selectbox("Status", ["In Progress", "Completed"])
        if st.button("Update Progress"):
            cursor.execute("INSERT INTO progress (user_id, module, status) VALUES (?, ?, ?)", (user_id, module, status))
            conn.commit()
            st.success("Progress diupdate!")
        
        progress = pd.read_sql("SELECT * FROM progress WHERE user_id=?", conn, params=(user_id,))
        st.dataframe(progress)
    
    elif subpage == "Dashboard Analytics":
        st.subheader("Dashboard Analytics")
        st.write("Analisis placeholder:")
        if not progress.empty:
            st.bar_chart(progress['status'].value_counts())
    
    elif subpage == "Attendance Tracking":
        st.subheader("Attendance Tracking")
        date = st.date_input("Tanggal")
        status = st.selectbox("Status", ["Hadir", "Absen"])
        if st.button("Catat Kehadiran"):
            cursor.execute("INSERT INTO attendance (user_id, date, status) VALUES (?, ?, ?)", (user_id, str(date), status))
            conn.commit()
            st.success("Kehadiran dicatat!")
        
        attendance = pd.read_sql("SELECT * FROM attendance", conn)
        st.dataframe(attendance)
    
    elif subpage == "Learning Analytics":
        st.subheader("Learning Analytics")
        st.write("Data placeholder dari log dan progress.")

elif page == "6. Laboratorium Virtual/Simulasi":
    st.header("Fitur Laboratorium Virtual/Simulasi")
    subpage = st.selectbox("Pilih Sub Fitur", ["Virtual Lab", "Interactive Simulation", "3D Visualization", "Real-time Feedback"])
    
    if subpage == "Virtual Lab":
        st.subheader("Virtual Lab")
        sim_title = st.text_input("Judul Simulasi")
        sim_desc = st.text_area("Deskripsi")
        if st.button("Buat Simulasi"):
            cursor.execute("INSERT INTO simulations (title, description) VALUES (?, ?)", (sim_title, sim_desc))
            conn.commit()
            st.success("Simulasi dibuat!")
        
        sims = pd.read_sql("SELECT * FROM simulations", conn)
        st.dataframe(sims)
    
    elif subpage == "Interactive Simulation":
        st.subheader("Interactive Simulation")
        st.write("Placeholder untuk simulasi interaktif (gunakan library seperti pygame jika diintegrasikan).")
    
    elif subpage == "3D Visualization":
        st.subheader("3D Visualization")
        st.write("Placeholder untuk 3D (gunakan library seperti plotly atau three.js via components).")
    
    elif subpage == "Real-time Feedback":
        st.subheader("Real-time Feedback")
        st.write("Umpan balik placeholder berdasarkan input.")
        input_sim = st.text_input("Input Simulasi")
        if input_sim:
            st.write("Feedback: Input diterima!")

elif page == "7. Manajemen Pengguna":
    st.header("Fitur Manajemen Pengguna")
    subpage = st.selectbox("Pilih Sub Fitur", ["Role-Based Access", "User Management", "Notification System"])
    
    if subpage == "Role-Based Access":
        st.subheader("Role-Based Access")
        st.write("Sudah diimplementasikan via role check (placeholder untuk demo).")
    
    elif subpage == "User Management":
        st.subheader("User Management")
        st.write("Fitur manajemen pengguna (placeholder, karena login dihapus).")
    
    elif subpage == "Notification System":
        st.subheader("Notification System")
        message = st.text_input("Pesan Notifikasi")
        if st.button("Kirim Notifikasi"):
            timestamp = datetime.now().isoformat()
            cursor.execute("INSERT INTO notifications (user_id, message, timestamp) VALUES (?, ?, ?)", (user_id, message, timestamp))
            conn.commit()
            st.success("Notifikasi dikirim!")
        
        notifs = pd.read_sql("SELECT * FROM notifications WHERE user_id=?", conn, params=(user_id,))
        st.write("Notifikasi:")
        st.dataframe(notifs)

elif page == "8. Dukungan Teknis":
    st.header("Fitur Dukungan Teknis")
    subpage = st.selectbox("Pilih Sub Fitur", ["Technical Support", "Troubleshooting Guide", "Training & Tutorial"])
    
    if subpage == "Technical Support":
        st.subheader("Technical Support")
        issue = st.text_area("Deskripsikan Masalah")
        if st.button("Kirim ke Support"):
            st.success("Tikett support dibuat (placeholder).")
    
    elif subpage == "Troubleshooting Guide":
        st.subheader("Troubleshooting Guide")
        st.write("Panduan umum: Restart app, check login, dll.")
    
    elif subpage == "Training & Tutorial":
        st.subheader("Training & Tutorial")
        st.write("Tutorial penggunaan: Pilih menu di sidebar.")
