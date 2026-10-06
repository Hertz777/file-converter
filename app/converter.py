from pathlib import Path
from PIL import Image
from reportlab.pdfgen import canvas

def convert(source: Path, target: Path, target_format: str):
    fmt = target_format.lower().lstrip(".")
    source_ext = source.suffix.lower().lstrip(".")
    target.parent.mkdir(parents=True, exist_ok=True)

    if source_ext == "txt" and fmt == "pdf":
        c = canvas.Canvas(str(target))
        y = 800
        for line in source.read_text(encoding="utf-8").splitlines():
            c.drawString(50, y, line[:110])
            y -= 16
            if y < 50:
                c.showPage(); y = 800
        c.save()
        return

    if source_ext in {"png", "jpg", "jpeg"} and fmt in {"png", "jpg", "jpeg"}:
        with Image.open(source) as img:
            if fmt in {"jpg", "jpeg"}:
                img = img.convert("RGB")
                img.save(target, "JPEG", quality=90)
            else:
                img.save(target, "PNG")
        return

    if source_ext == fmt:
        target.write_bytes(source.read_bytes())
        return

    raise ValueError(f"Unsupported conversion: {source_ext} -> {fmt}")
