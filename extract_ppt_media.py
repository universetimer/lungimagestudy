# -*- coding: utf-8 -*-
"""Extract all raw media files from each PPT (pptx is a zip)."""
import sys, io, os, glob, zipfile, shutil
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PPT_DIR = r"C:/Users/unive/OneDrive/111 유튜버/학생 흉부 사진/20260519 학생"
DUMP_DIR = r"C:/Users/unive/OneDrive/111 Claude/병동 가이드 라인/cxr-grading-app/_ppt_media"

# Only keep UNIQUE PPTs (skip duplicates)
UNIQUE = {
    "홍예림": "CXR (1) 홍예림.pptx",
    "이현수": "CXR (2) 이현수.pptx",
    "서동성": "CXR (3)서동성.pptx",
    "유병진": "CXR 발표_A반 19조 57번 202300060 유병진.pptx",
    "목승민": "CXR 판독_A반 20조 60번 202300028 목승민.pptx",
    "최시연": "CXR 판독_A반 20조 61번 202300095 최시연.pptx",
}

if os.path.exists(DUMP_DIR):
    shutil.rmtree(DUMP_DIR)
os.makedirs(DUMP_DIR)

for student, fname in UNIQUE.items():
    ppt_path = os.path.join(PPT_DIR, fname)
    if not os.path.exists(ppt_path):
        print(f"[MISS] {student}: {fname}")
        continue
    out_dir = os.path.join(DUMP_DIR, student)
    os.makedirs(out_dir, exist_ok=True)
    try:
        with zipfile.ZipFile(ppt_path) as z:
            media_files = [n for n in z.namelist() if n.startswith("ppt/media/")]
            for m in media_files:
                target = os.path.join(out_dir, os.path.basename(m))
                with z.open(m) as src, open(target, "wb") as dst:
                    shutil.copyfileobj(src, dst)
            print(f"[OK] {student}: {len(media_files)} media files")
    except Exception as e:
        print(f"[ERR] {student}: {e}")
print(f"\nAll media in: {DUMP_DIR}")
