import os
import sys
import re
import shutil
import subprocess
import platform
import hashlib
import json
import random
import uuid
from datetime import datetime, timedelta
from config import LATEX_TEMPLATE, CACHE_DIR, IMAGE_LIB_PATH

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_hwid():
    """Lấy mã định danh phần cứng (Hardware ID) duy nhất của máy"""
    try:
        mac = uuid.getnode()
        node = platform.node()
        system = platform.system()
        raw_id = f"{mac}-{node}-{system}"
        return hashlib.md5(raw_id.encode()).hexdigest().upper()
    except:
        return "UNKNOWN-DEVICE-ID"

def open_file_or_url(path):
    """Mở file hoặc URL tương thích đa nền tảng (Win/Mac/Linux)"""
    system = platform.system()
    if system == 'Windows':
        os.startfile(path)
    elif system == 'Darwin':  # macOS
        subprocess.call(('open', path))
    else:  # Linux
        subprocess.call(('xdg-open', path))

def extract_metadata_from_tex(tex, q_type):
    """Trích xuất Key và Lời giải từ nội dung LaTeX"""
    key = "?"
    explanation = ""
    try:
        # 1. Lấy lời giải
        expl, _ = LatexParser.extract_command(tex, "loigiai")
        if expl: explanation = expl.strip()

        # 2. Lấy Key
        if q_type == 1: # MCQ
            m = re.search(r"\[KEY:\s*([A-D])\]", tex, re.IGNORECASE)
            if m: key = m.group(1).upper()
            else:
                args, _ = LatexParser.extract_multiple_args(tex, "choice")
                for i, arg in enumerate(args):
                    if "\\True" in arg: key = ['A','B','C','D'][i]; break
        elif q_type == 2: # TF
            args, _ = LatexParser.extract_multiple_args(tex, "choiceTF")
            if args:
                tf_res = {}
                for i, arg in enumerate(args):
                    sub = ['a','b','c','d'][i]
                    tf_res[sub] = "Đ" if "\\True" in arg else "S"
                key = tf_res
        elif q_type == 3: # Short
            k, _ = LatexParser.extract_command(tex, "shortans")
            if k: key = k.strip()
    except: pass
    return key, explanation

# =============================================================================
# UTILITY CLASSES
# =============================================================================

class LatexCleaner:
    @staticmethod
    def clean(text):
        if not text: return ""
        original_text = text

        # 1. Xóa comment (%) nhưng giữ lại \% (ký tự phần trăm thực sự)
        text = re.sub(r'(?<!\\)%.*', '', text)

        # 2. Xóa các wrapper môi trường không cần thiết
        text = re.sub(r'^\s*\\begin\s*\{[a-zA-Z0-9]+\}.*?(\[.*?\])?', '', text, flags=re.MULTILINE)
        text = re.sub(r'\\end\s*\{[a-zA-Z0-9]+\}\s*$', '', text, flags=re.MULTILINE)

        # 3. Xóa các lệnh định dạng trang in
        text = text.replace(r'\noindent', '').replace(r'\newpage', '').replace(r'\clearpage', '')

        text = text.strip()

        if not text:
            return original_text

        return text

class LatexParser:
    @staticmethod
    def find_closing_brace(text, open_pos):
        balance = 1; i = open_pos + 1; n = len(text)
        while i < n:
            char = text[i]
            if char == '\\' and i + 1 < n: i += 2; continue
            if char == '{': balance += 1
            elif char == '}': balance -= 1
            if balance == 0: return i
            i += 1
        return -1

    @staticmethod
    def extract_command(text, cmd_name):
        try:
            pattern = f"\\\\{cmd_name}" + r"(?:\[.*?\])?\s*\{"
            match = re.search(pattern, text)
            if not match: return None, text
            start_content = match.end() - 1
            end_content = LatexParser.find_closing_brace(text, start_content)
            if end_content != -1:
                content = text[start_content+1 : end_content]
                remain = text[:match.start()] + " " + text[end_content+1:]
                return content, remain
        except: pass
        return None, text

    @staticmethod
    def extract_multiple_args(text, cmd_name):
        try:
            pattern = f"\\\\{cmd_name}" + r"(?:\[.*?\])?"
            match = re.search(pattern, text)
            if not match: return [], text
            args = []; idx = match.end(); text_before = text[:match.start()]
            while idx < len(text):
                while idx < len(text) and text[idx].isspace(): idx += 1
                if idx >= len(text) or text[idx] != '{': break
                end = LatexParser.find_closing_brace(text, idx)
                if end == -1: break
                args.append(text[idx+1:end])
                idx = end + 1
            return args, text_before
        except: return [], text

    @staticmethod
    def parse_full(raw_tex):
        original_tex = raw_tex

        try:
            q = LatexCleaner.clean(raw_tex)

            # 1. Tách lời giải
            solution_content, q = LatexParser.extract_command(q, "loigiai")
            if not solution_content: solution_content = ""

            # 2. Xử lý Hình ảnh & TikZ
            tikz_blocks = re.findall(r'(\\begin\{tikzpicture\}.*?\\end\{tikzpicture\})', q, re.DOTALL)
            for code in tikz_blocks:
                svg = TikzCompiler.compile(code)
                if svg: q = q.replace(code, f'<div class="tikz-wrapper">{svg}</div>')

            table_blocks = re.findall(r'(\\begin\{tabular\}.*?\\end\{tabular\})', q, re.DOTALL)
            for code in table_blocks:
                svg = TikzCompiler.compile(code)
                if svg: q = q.replace(code, f'<div class="tikz-wrapper">{svg}</div>')

            matches = list(re.finditer(r"\\includegraphics(\[.*?\])?\{([^{}]+)\}", q))
            for m in reversed(matches):
                img_path = m.group(2).strip()
                html = f'<div class="img-wrapper"><img src="/api/image/{img_path}" loading="lazy"></div>'
                q = q[:m.start()] + html + q[m.end():]

            q = re.sub(r'\\begin\{center\}(.*?)\\end\{center\}', r'<div style="text-align: center;">\1</div>', q, flags=re.DOTALL)

            if "\\immini" in q:
                match = re.search(r"\\immini(?:\[.*?\])?", q)
                if match:
                    start_parse = match.end()
                    temp_q = q[start_parse:]
                    args = []
                    curr = 0
                    for _ in range(2):
                        while curr < len(temp_q) and temp_q[curr].isspace(): curr += 1
                        if curr < len(temp_q) and temp_q[curr] == '{':
                            end = LatexParser.find_closing_brace(temp_q, curr)
                            if end != -1:
                                args.append(temp_q[curr+1:end])
                                curr = end + 1
                    if len(args) == 2:
                        html = f"""<div class="immini-box"><div class="immini-content">{args[0]}</div><div class="immini-media">{args[1]}</div></div>"""
                        q = q[:match.start()] + html + temp_q[curr:]

            # 3. Phân loại & Tách đáp án
            q_type = 3
            options = []
            correct_key = "?"

            tf_opts, text_before = LatexParser.extract_multiple_args(q, "choiceTF")
            if tf_opts:
                q_type = 2; q = text_before; options = tf_opts
            else:
                ans_content, text_before = LatexParser.extract_command(q, "shortans")
                if ans_content:
                    q_type = 3; q = text_before; correct_key = ans_content
                    q = q.replace(f"\\shortans{{{ans_content}}}", "")
                else:
                    c_opts, text_before = LatexParser.extract_multiple_args(q, "choice")
                    if c_opts:
                        q_type = 1; q = text_before
                        clean_opts = []
                        for i, o in enumerate(c_opts):
                            if "\\True" in o:
                                o = o.replace("\\True", ""); correct_key = ['A', 'B', 'C', 'D'][i]
                            clean_opts.append(o.strip())
                        options = clean_opts

            q = q.replace("\\True", "")
            solution_content = solution_content.replace("\\True", "")

            if not q.strip(): q = original_tex

            return {
                "type": q_type,
                "content": q,
                "options": options,
                "solution": solution_content,
                "correct_key": correct_key
            }

        except Exception as e:
            print(f"⚠️ Lỗi Parse: {e}. Đang dùng Fallback.")
            return {
                "type": 3,
                "content": original_tex,
                "options": [],
                "solution": "",
                "correct_key": "?"
            }

    @staticmethod
    def split_question_parts(raw_tex):
        clean_tex = LatexCleaner.clean(raw_tex)

        solution = ""
        sol_content, text_remains = LatexParser.extract_command(clean_tex, "loigiai")
        if sol_content:
            solution = sol_content
            clean_tex = text_remains

        options = []
        stem = clean_tex

        choice_opts, stem_remains = LatexParser.extract_multiple_args(clean_tex, "choice")

        if choice_opts:
            options = choice_opts
            stem = stem_remains
        else:
            tf_opts, stem_remains_tf = LatexParser.extract_multiple_args(clean_tex, "choiceTF")
            if tf_opts:
                options = tf_opts
                stem = stem_remains_tf

        stem = re.sub(r'\\choice\s*$', '', stem).strip()
        stem = re.sub(r'\\choiceTF\s*$', '', stem).strip()

        return {
            "stem": stem,
            "options": options,
            "solution": solution
        }

class TikzCompiler:
    TEMPLATE = r"""
\documentclass[dvisvgm]{standalone}
\usepackage[utf8]{inputenc}
\usepackage[T5]{fontenc}
\usepackage[vietnamese]{babel}
\usepackage{varwidth}
\usepackage{array, booktabs, longtable, colortbl}
\usepackage{multicol, multirow, makecell}
\usepackage{amsmath,amssymb,mathrsfs,mathabx}
\usepackage{mhchem, chemfig, siunitx, esvect}
\usepackage{enumerate, enumitem}
\usepackage{tabvar}
\usepackage{tikz, tkz-euclide, tkz-tab}
\usepackage{tikz-3dplot, pgfplots}
\pgfplotsset{compat=1.18}
\usepackage{venndiagram, tikz-dependency, tikzpeople}
\usetikzlibrary{arrows, calc, intersections, angles, quotes, backgrounds}
\usetikzlibrary{shapes.geometric, patterns, shadings, positioning, fadings}
\usetikzlibrary{decorations.markings, spy, bending, 3d, shadows}
\def\vec{\vv}
\def\overrightarrow{\vv}
\renewcommand{\arraystretch}{1.2}
\newcommand{\heva}[1]{\left\{\begin{aligned}#1\end{aligned}\right.}
\newcommand{\hoac}[1]{\left[\begin{aligned}#1\end{aligned}\right.}
\tikzset{
    equal mark/.style={postaction={decorate, decoration={markings, mark=at position 0.5 with {\draw[line width=0.4pt] (-0.05,0.05)--(0.05,-0.05);}}}},
    edge from parent/.style={draw, thick, cyan},
    level 3/.style={yshift=5cm},
    level 4/.style={level distance=5mm}
}
\begin{document}
<<CONTENT>>
\end{document}
    """
    @staticmethod
    def compile(code):
        clean_code = LatexCleaner.clean(code)

        if "\\begin{tikzpicture}" not in clean_code:
            clean_code = (
                r"\begin{tikzpicture}"
                r"\node[inner sep=5pt, anchor=center, align=center] at (0,0) {"
                r"\begin{varwidth}{18cm}"
                + clean_code +
                r"\end{varwidth}"
                r"};"
                r"\end{tikzpicture}"
            )

        code_hash = hashlib.md5(clean_code.encode('utf-8')).hexdigest()
        svg_path = os.path.join(CACHE_DIR, f"{code_hash}.svg")

        if os.path.exists(svg_path):
            with open(svg_path, 'r', encoding='utf-8') as f: return f.read()

        try:
            tex_path = os.path.join(CACHE_DIR, f"{code_hash}.tex")
            dvi_path = os.path.join(CACHE_DIR, f"{code_hash}.dvi")

            full_content = TikzCompiler.TEMPLATE.replace("<<CONTENT>>", clean_code)

            with open(tex_path, 'w', encoding='utf-8') as f:
                f.write(full_content)

            subprocess.run(["latex", "-interaction=nonstopmode", "-output-directory", CACHE_DIR, tex_path],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)

            if os.path.exists(dvi_path):
                subprocess.run(["dvisvgm", "--no-fonts", "--scale=1.4", "-o", svg_path, dvi_path],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)

                if os.path.exists(svg_path):
                    with open(svg_path, 'r', encoding='utf-8') as f: return f.read()
        except Exception as e:
            print(f"Lỗi biên dịch: {e}")
        return None

class PDFCompiler:
    @staticmethod
    def compile_tex_to_pdf(tex_content, output_name):
        build_dir = os.path.join(os.path.expanduser("~"), ".bankai_build")
        if not os.path.exists(build_dir): os.makedirs(build_dir)

        if getattr(sys, 'frozen', False):
            current_dir = sys._MEIPASS
        else:
            current_dir = os.path.dirname(os.path.abspath(__file__))
        sty_name = "ex_test.sty"
        src_sty = os.path.join(current_dir, sty_name)
        dst_sty = os.path.join(build_dir, sty_name)

        if os.path.exists(src_sty):
            try:
                shutil.copy(src_sty, dst_sty)
            except Exception as e:
                print(f"⚠️ Cảnh báo: Không copy được {sty_name}: {e}")

        tex_path = os.path.join(build_dir, f"{output_name}.tex")
        pdf_path = os.path.join(build_dir, f"{output_name}.pdf")

        try:
            with open(tex_path, "w", encoding="utf-8") as f:
                f.write(tex_content)

            process = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", f"-output-directory={build_dir}", tex_path],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60
            )

            if os.path.exists(pdf_path):
                return "Thành công", pdf_path
            else:
                log_content = process.stdout.decode('utf-8', errors='ignore')
                print(f"\n❌ LỖI CHI TIẾT KHI TẠO PDF ({output_name}):")
                print(log_content[-1500:])
                return "Lỗi biên dịch LaTeX (Xem log chi tiết ở trên)", None

        except Exception as e:
            return str(e), None

class ImageCompiler:
    @staticmethod
    def compile_question_to_png(tex_content, output_name):
        from pdf2image import convert_from_path

        template = r"""
\documentclass[preview,border=3pt,varwidth=18cm]{standalone}
\usepackage[utf8]{inputenc}
\usepackage[T5]{fontenc}
\usepackage[vietnamese]{babel}
\usepackage{amsmath,amssymb,mathrsfs,mathabx}
\usepackage{tikz, tkz-euclide, pgfplots, tikz-3dplot}
\usepackage[most]{tcolorbox}
\usepackage{esvect}
\usepackage{xcolor}
\definecolor{mainbrown}{HTML}{582704}
\definecolor{mauVD}{HTML}{AC203D}
\definecolor{mauBT}{HTML}{041F60}
\usetikzlibrary{arrows, calc, intersections, angles, quotes, backgrounds, shapes.geometric}
\usetikzlibrary{decorations.markings, bending, patterns.meta, shadows}
\pgfplotsset{compat=1.18}
\IfFileExists{ex_test.sty}{\usepackage[dethi]{ex_test}}{}
\def\vec{\vv}
\def\True{}
\renewcommand{\arraystretch}{1.2}
\newcommand{\heva}[1]{\left\{\begin{aligned}#1\end{aligned}\right.}
\newcommand{\hoac}[1]{\left[\begin{aligned}#1\end{aligned}\right.}
\begin{document}
__CONTENT__
\end{document}
"""
        full_tex = template.replace("__CONTENT__", tex_content)

        build_dir = os.path.join(os.path.expanduser("~"), ".bankai_build")
        if not os.path.exists(build_dir): os.makedirs(build_dir)

        tex_path = os.path.join(build_dir, f"{output_name}.tex")
        pdf_path = os.path.join(build_dir, f"{output_name}.pdf")
        png_path = os.path.join(build_dir, f"{output_name}.png")

        try:
            with open(tex_path, "w", encoding="utf-8") as f:
                f.write(full_tex)

            process = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", f"-output-directory={build_dir}", tex_path],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30
            )

            if not os.path.exists(pdf_path):
                print(f"❌ Lỗi biên dịch LaTeX ({output_name}):")
                print(process.stdout.decode('utf-8', errors='ignore')[-500:])
                return None

            try:
                images = convert_from_path(pdf_path, dpi=400)
                if images:
                    images[0].save(png_path, 'PNG')
                    return png_path
            except Exception as e_poppler:
                print(f"❌ Lỗi Poppler (pdf2image): {e_poppler}")
                return None

        except Exception as e:
            print(f"❌ Lỗi hệ thống ImageCompiler: {e}")

        return None

class ImageHandler:
    IMAGE_MAP = {}
    @staticmethod
    def load_library():
        try:
            if os.path.exists(IMAGE_LIB_PATH):
                with open(IMAGE_LIB_PATH, 'r', encoding='utf-8') as f:
                    ImageHandler.IMAGE_MAP = json.load(f)
        except: pass

    @staticmethod
    def get_image_path(filename):
        clean_name = os.path.basename(filename).strip()

        if clean_name in ImageHandler.IMAGE_MAP:
            return ImageHandler.IMAGE_MAP[clean_name]

        local_path = os.path.abspath(filename)
        if os.path.exists(local_path): return local_path

        return None
ImageHandler.load_library()

class ExamMixer:

    def find_closing_brace(self, text, open_pos):
        balance = 1
        i = open_pos + 1
        n = len(text)
        while i < n:
            char = text[i]
            if char == '\\' and i + 1 < n:
                i += 2
                continue
            if char == '{':
                balance += 1
            elif char == '}':
                balance -= 1
            if balance == 0:
                return i
            i += 1
        return -1

    def permute_content(self, text):
        match = re.search(r"\\choice(?:\s*\[.*?\])?", text)

        if not match:
            key_match = re.search(r"\[KEY:\s*([A-D])\]", text, re.IGNORECASE)
            return text, (key_match.group(1).upper() if key_match else "?")

        start_idx = match.end()
        full_command_start = match.start()

        options = []
        current_idx = start_idx

        try:
            for _ in range(4):
                while current_idx < len(text) and text[current_idx].isspace():
                    current_idx += 1

                if current_idx >= len(text) or text[current_idx] != '{':
                    return text, "A"

                close_idx = self.find_closing_brace(text, current_idx)
                if close_idx == -1: return text, "A"

                content = text[current_idx+1 : close_idx]
                options.append(content)
                current_idx = close_idx + 1

            full_command_end = current_idx

        except Exception as e:
            print(f"Lỗi parse choice: {e}")
            return text, "A"

        correct_idx = -1
        clean_options = []

        for idx, opt in enumerate(options):
            if "\\True" in opt:
                correct_idx = idx
                clean_options.append(opt.replace("\\True", "").strip())
            else:
                clean_options.append(opt.strip())

        if correct_idx == -1:
            key_match = re.search(r"\[KEY:\s*([A-D])\]", text, re.IGNORECASE)
            if key_match:
                key_map = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
                correct_idx = key_map.get(key_match.group(1).upper(), -1)

        indices = [0, 1, 2, 3]
        random.shuffle(indices)

        new_options_tex = ""
        for i in indices:
            opt_content = clean_options[i]
            if i == correct_idx:
                opt_content = "\\True " + opt_content
            new_options_tex += f"{{{opt_content}}}"

        prefix = text[:full_command_start]
        suffix = text[full_command_end:]
        command_head = text[match.start():match.end()].strip()
        new_text = f"{prefix}{command_head}{new_options_tex}{suffix}"

        new_key_char = "?"
        if correct_idx != -1:
            new_correct_idx = indices.index(correct_idx)
            inv_key_map = {0: 'A', 1: 'B', 2: 'C', 3: 'D'}
            new_key_char = inv_key_map[new_correct_idx]

        return new_text, new_key_char

    def mix_exam(self, questions, num_variants=1, start_code=101):
        mixed_results = {}

        p1 = [q for q in questions if q.get('dang') == 1] # TN
        p2 = [q for q in questions if q.get('dang') == 2] # Đ/S
        p3 = [q for q in questions if q.get('dang') == 3] # TLN
        others = [q for q in questions if q.get('dang') not in [1, 2, 3]]

        for i in range(num_variants):
            exam_code = start_code + i
            variant_qs = []

            curr_p1 = [q.copy() for q in p1]
            random.shuffle(curr_p1)

            final_p1 = []
            for q in curr_p1:
                content = q.get('content_tex', '')
                new_content, new_key = self.permute_content(content)

                if re.search(r"\[KEY:.*?\]", new_content):
                     new_content = re.sub(r"\[KEY:.*?\]", f"[KEY: {new_key}]", new_content)
                else:
                     new_content += f"\n% [KEY: {new_key}]"

                q_new = q.copy()
                q_new['content_tex'] = new_content
                q_new['final_key'] = new_key
                final_p1.append(q_new)

            curr_p2 = [q.copy() for q in p2]; random.shuffle(curr_p2)
            curr_p3 = [q.copy() for q in p3]; random.shuffle(curr_p3)
            curr_others = [q.copy() for q in others]

            variant_qs.extend(final_p1)
            variant_qs.extend(curr_p2)
            variant_qs.extend(curr_p3)
            variant_qs.extend(curr_others)

            mixed_results[exam_code] = variant_qs

        return mixed_results

class SchedulerManager:
    FILE_PATH = "scheduled_tasks.json"

    @staticmethod
    def load_tasks():
        if not os.path.exists(SchedulerManager.FILE_PATH): return []
        try:
            with open(SchedulerManager.FILE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: return []

    @staticmethod
    def save_tasks(tasks):
        with open(SchedulerManager.FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)

    @staticmethod
    def add_schedule(course_id, course_name, grade, subject, chapter, level, num_q, days, time_str):
        tasks = SchedulerManager.load_tasks()
        start_date = datetime.now()

        for i in range(days):
            run_date = start_date + timedelta(days=i)
            task = {
                "id": str(uuid.uuid4()),
                "run_date": run_date.strftime("%Y-%m-%d"),
                "run_time": time_str,
                "course_id": course_id,
                "course_name": course_name,
                "config": {
                    "grade": grade, "subject": subject, "chapter": chapter,
                    "level": level, "num_q": num_q
                },
                "status": "pending",
                "log": ""
            }
            tasks.append(task)

        SchedulerManager.save_tasks(tasks)
        return len(tasks)
