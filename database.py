import sqlite3
import re
import os
import json
from config import DB_PATH, DATA_ID6_2025, DANH_MUC_DANG, CHAPTER_NAMES

# =============================================================================
# DATABASE BACKEND
# =============================================================================

class Backend:
    def __init__(self):
        # check_same_thread=False là bắt buộc
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

        # [FIX] Bật chế độ WAL để tăng tốc và tránh lỗi I/O khi ghi nhiều
        try:
            self.conn.execute("PRAGMA journal_mode=WAL;")
            self.conn.execute("PRAGMA synchronous=NORMAL;")
        except:
            pass

        self._init_db()

    def _init_db(self):
        self.conn.execute("CREATE TABLE IF NOT EXISTS questions (id INTEGER PRIMARY KEY AUTOINCREMENT, grade INTEGER, subject TEXT, chapter INTEGER, level TEXT, content_tex TEXT, raw_data TEXT, dang INTEGER DEFAULT 4, id6 TEXT, bai INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        self.conn.commit()
        self._migrate_db()
        # [MỚI] Bảng lưu kết quả thi
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS exam_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_name TEXT,
                exam_title TEXT,
                score REAL,
                detail TEXT, -- Lưu JSON chi tiết đúng sai
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()
        self._migrate_db()

    def _migrate_db(self):
        try:
            cur = self.conn.execute("PRAGMA table_info(questions)")
            cols = [r[1] for r in cur.fetchall()]
            if 'dang' not in cols: self.conn.execute("ALTER TABLE questions ADD COLUMN dang INTEGER DEFAULT 4")
            if 'id6' not in cols: self.conn.execute("ALTER TABLE questions ADD COLUMN id6 TEXT")
            if 'bai' not in cols: self.conn.execute("ALTER TABLE questions ADD COLUMN bai INTEGER")
            self.conn.commit()
        except: pass

    def get_dashboard_stats(self):
        """Lấy số liệu thống kê chi tiết cho Dashboard"""
        # 1. Tổng số câu toàn ngân hàng
        total = self.conn.execute("SELECT COUNT(*) FROM questions").fetchone()[0]

        # 2. Thống kê theo mức độ (Toàn bộ)
        levels = self.conn.execute("SELECT level, COUNT(*) FROM questions GROUP BY level").fetchall()
        level_map = {row[0]: row[1] for row in levels}

        # 3. Thống kê chi tiết Group theo: Lớp -> Môn -> Chương
        # Query này sẽ nhóm dữ liệu để ta dựng cây thư mục
        query = """
            SELECT grade, subject, chapter, level, COUNT(*)
            FROM questions
            GROUP BY grade, subject, chapter, level
            ORDER BY grade, subject, chapter
        """
        rows = self.conn.execute(query).fetchall()

        return total, level_map, rows

    def analyze_tex_file(self, path):
        """
        Phiên bản nâng cấp: Quét ID6 mọi vị trí + Tự động bóc tách Chương/Bài/Dạng chuẩn xác
        """
        questions = []
        detected_images = {}

        try:
            with open(path, 'r', encoding='utf-8') as f: content = f.read()
        except:
            try:
                with open(path, 'r', encoding='utf-16') as f: content = f.read()
            except: return [], {}

        # Regex tìm khối câu hỏi (ex hoặc bt)
        matches = re.finditer(r"\\begin\s*\{(?:ex|bt)\}(.*?)\\end\s*\{(?:ex|bt)\}", content, re.DOTALL)

        for m in matches:
            raw = m.group(0) # Toàn bộ khối \begin...\end
            block = m.group(1) # Nội dung bên trong

            # --- 1. QUÉT TÌM ID6 Ở BẤT KỲ VỊ TRÍ NÀO ---
            id_pattern = r"\[([0-2])([DHC])(\d+)([NHVC])(\d+)-(\d+)\]"
            id_match = re.search(id_pattern, raw)

            # Giá trị mặc định nếu không tìm thấy ID
            id6 = None
            g, s, ch, l, bai, dang_id = 12, "D", 1, "N", 0, 0

            if id_match:
                full_tag = id_match.group(0)
                id6 = full_tag.replace("[", "").replace("]", "")
                gc, sc, chc, lc, bc, dc = id_match.groups()

                g = {'0':10, '1':11, '2':12}.get(gc, 12)
                s = sc
                ch = int(chc)
                l = lc
                bai = int(bc)
                dang_id = int(dc)
            else:
                # Fallback: Thử tìm ID kiểu cũ
                short_match = re.search(r"\[([0-2])([DHC])(\d+)([NHVCTYBKG])\]", raw)
                if short_match:
                    full_tag = short_match.group(0)
                    id6 = full_tag.replace("[", "").replace("]", "")
                    gc, sc, chc, lc = short_match.groups()
                    g = {'0':10, '1':11, '2':12}.get(gc, 12)
                    s = sc
                    ch = int(chc)
                    l_map = {'Y':'N', 'B':'H', 'K':'V', 'G':'C'}
                    l = l_map.get(lc, lc)

            # --- 2. XÁC ĐỊNH LOẠI CÂU HỎI ---
            dang = 4 # Mặc định Tự luận

            if r"\choiceTF" in block:
                dang = 2 # Đúng/Sai
            elif r"\choice" in block:
                dang = 1 # Trắc nghiệm
            elif r"\shortans" in block:
                dang = 3 # Trả lời ngắn

            # --- 3. QUÉT ẢNH ---
            img_matches = re.findall(r"\\includegraphics(?:\[.*?\])?\{(.*?)\}", raw)
            tex_dir = os.path.dirname(path)
            for img in img_matches:
                candidate_path = os.path.join(tex_dir, img.strip())
                if os.path.exists(candidate_path):
                    detected_images[img.strip()] = candidate_path.replace("\\", "/")

            q_obj = {
                'grade': g, 'subject': s, 'chapter': ch, 'level': l,
                'content_tex': raw, 'raw_data': raw, 'dang': dang,
                'id6': id6, 'bai': bai
            }
            questions.append(q_obj)

        return questions, detected_images

    def insert_questions_list(self, q_list):
        """Lưu danh sách câu hỏi đã xử lý vào Database"""
        added = 0
        skipped = 0

        # Bắt đầu transaction để lưu nhanh
        self.conn.execute("BEGIN TRANSACTION")
        try:
            for q in q_list:
                # Check trùng
                exists = self.conn.execute("SELECT 1 FROM questions WHERE content_tex = ?", (q['content_tex'],)).fetchone()
                if exists:
                    skipped += 1
                    continue

                self.conn.execute(
                    "INSERT INTO questions (grade, subject, chapter, level, content_tex, raw_data, dang, id6, bai) VALUES (?,?,?,?,?,?,?,?,?)",
                    (q['grade'], q['subject'], q['chapter'], q['level'], q['content_tex'], q['raw_data'], q['dang'], q['id6'], q['bai'])
                )
                added += 1
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e

        return added, skipped

    def get_all_filtered(self, g, s, c, b, l, dang, limit=None):
        q = "SELECT * FROM questions WHERE 1=1"
        p = []
        if g: q+=" AND grade=?"; p.append(g)
        if s: q+=" AND subject=?"; p.append(s)
        if c: q+=" AND chapter=?"; p.append(c)
        if b and b!=0: q+=" AND bai=?"; p.append(b)
        if l: q+=" AND level=?"; p.append(l)
        if dang and dang!=0: q+=" AND dang=?"; p.append(dang)
        q += " ORDER BY id"
        if limit: q += f" LIMIT {limit}"
        return [dict(r) for r in self.conn.execute(q, tuple(p)).fetchall()]

    def get_rnd(self, g, s, ch, bai, l, dang=None, exc=None):
        q = "SELECT * FROM questions WHERE grade=? AND subject=? AND chapter=? AND level=?"
        p = [g, s, ch, l]
        if bai and bai != 0: q+=" AND bai=?"; p.append(bai)
        if dang and dang!=0: q+=" AND dang=?"; p.append(dang)
        if exc: q+=" AND id != ?"; p.append(exc)
        res = self.conn.execute(q+" ORDER BY RANDOM() LIMIT 1", tuple(p)).fetchone()
        return dict(res) if res else None

    def get_stats(self):
        stats = {}
        for g in [10,11,12]:
            stats[g] = {}
            for s in ['D','H']:
                res = self.conn.execute("SELECT chapter, level, COUNT(*) FROM questions WHERE grade=? AND subject=? GROUP BY chapter, level", (g,s)).fetchall()
                stats[g][s] = {}
                for r in res:
                    if r[0] not in stats[g][s]: stats[g][s][r[0]] = {}
                    stats[g][s][r[0]][r[1]] = r[2]
        return stats

    def get_unassigned(self, limit=100):
        return [dict(r) for r in self.conn.execute("SELECT * FROM questions WHERE id6 IS NULL OR id6 = '' LIMIT ?", (limit,)).fetchall()]

    def get_exam_results(self):
        """Lấy toàn bộ lịch sử thi"""
        return self.conn.execute("SELECT * FROM exam_results ORDER BY submitted_at DESC").fetchall()

    def update_id6(self, qid, id6, g, s, c, l, b, d, new_content):
        """Cập nhật ID6 và Nội dung LaTeX mới vào Database"""
        query = """
            UPDATE questions
            SET id6=?, grade=?, subject=?, chapter=?, level=?, bai=?, dang=?, content_tex=?
            WHERE id=?
        """
        self.conn.execute(query, (id6, g, s, c, l, b, d, new_content, qid))
        self.conn.commit()

class DatabaseManager:
    @staticmethod
    def migrate_db(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(questions)")
        columns = [info[1] for info in cursor.fetchall()]

        # Đảm bảo có đủ các cột chuẩn
        required = {
            "subject": "TEXT", "chapter": "INTEGER", "bai": "INTEGER",
            "level": "TEXT", "dang": "INTEGER", "id6": "TEXT"
        }
        for col, dtype in required.items():
            if col not in columns:
                cursor.execute(f"ALTER TABLE questions ADD COLUMN {col} {dtype} DEFAULT NULL")
        conn.commit(); conn.close()

    @staticmethod
    def get_filtered_questions(db_path, filters):
        conn = sqlite3.connect(db_path); conn.row_factory = sqlite3.Row

        # Chọn các cột cần thiết
        query = "SELECT id, content_tex, level, id6, dang, chapter, bai FROM questions WHERE 1=1"
        params = []

        # Áp dụng bộ lọc (Chỉ thêm điều kiện nếu giá trị khác 0/Rỗng)
        if filters.get("grade"):
            query += " AND grade = ?"; params.append(int(filters["grade"]))
        if filters.get("subject"):
            query += " AND subject = ?"; params.append(filters["subject"])
        if filters.get("chapter"):
            query += " AND chapter = ?"; params.append(int(filters["chapter"]))
        if filters.get("bai"):
            query += " AND bai = ?"; params.append(int(filters["bai"]))
        if filters.get("level"):
            query += " AND level = ?"; params.append(filters["level"])
        if filters.get("dang"):
            query += " AND dang = ?"; params.append(int(filters["dang"]))

        query += " ORDER BY id DESC LIMIT 1000" # Tăng giới hạn hiển thị
        rows = conn.execute(query, params).fetchall()
        conn.close()
        return rows

    @staticmethod
    def auto_scan_metadata(db_path):
        """Quét lại toàn bộ DB để cập nhật cột 'bai', 'dang', 'id6' từ nội dung TeX"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Lấy tất cả câu hỏi
        cursor.execute("SELECT id, content_tex FROM questions")
        rows = cursor.fetchall()

        count = 0
        id_pattern = r"\[([0-2])([DHC])(\d+)([NHVC])(\d+)-(\d+)\]"

        print("Đang chuẩn hóa dữ liệu...")

        cursor.execute("BEGIN TRANSACTION")
        try:
            for r in rows:
                q_id, content = r[0], r[1]
                updates = []
                vals = []

                # 1. Quét tìm ID6 chuẩn
                match = re.search(id_pattern, content)
                if match:
                    # Bóc tách dữ liệu
                    full_id = match.group(0).replace("[", "").replace("]", "")
                    gc, sc, chc, lc, bc, dc = match.groups()

                    g_val = {'0':10, '1':11, '2':12}.get(gc, 12)

                    # Cập nhật các trường: id6, grade, subject, chapter, level, bai
                    updates.append("id6 = ?"); vals.append(full_id)
                    updates.append("grade = ?"); vals.append(g_val)
                    updates.append("subject = ?"); vals.append(sc)
                    updates.append("chapter = ?"); vals.append(int(chc))
                    updates.append("level = ?"); vals.append(lc)
                    updates.append("bai = ?"); vals.append(int(bc))

                # 2. Quét lại Dạng (Hình thức thi)
                dang_val = 4
                if "\\choiceTF" in content: dang_val = 2
                elif "\\choice" in content: dang_val = 1
                elif "\\shortans" in content: dang_val = 3

                updates.append("dang = ?"); vals.append(dang_val)

                # Thực hiện Update
                if updates:
                    sql = f"UPDATE questions SET {', '.join(updates)} WHERE id = ?"
                    vals.append(q_id)
                    cursor.execute(sql, vals)
                    count += 1

            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Lỗi Scan: {e}")

        conn.close()
        return count
