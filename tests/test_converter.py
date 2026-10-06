from pathlib import Path
from app.converter import convert

def test_txt_to_pdf(tmp_path):
    src = tmp_path / "hello.txt"
    dst = tmp_path / "hello.pdf"
    src.write_text("Hello from file converter!", encoding="utf-8")
    convert(src, dst, "pdf")
    assert dst.exists() and dst.stat().st_size > 0

def test_same_format(tmp_path):
    src = tmp_path / "a.txt"
    dst = tmp_path / "b.txt"
    src.write_text("abc", encoding="utf-8")
    convert(src, dst, "txt")
    assert dst.read_text(encoding="utf-8") == "abc"
