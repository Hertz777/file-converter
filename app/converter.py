
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image
from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer


def convert(source: Path, target: Path, target_format: str):
    fmt = target_format.lower().lstrip(".")
    source_ext = source.suffix.lower().lstrip(".")
    target.parent.mkdir(parents=True, exist_ok=True)
    if source_ext == "pdf" and fmt == "txt":
        reader = PdfReader(str(source))
        text = "\n".join(
            page.extract_text() or ""
            for page in reader.pages
        )
        target.write_text(text, encoding="utf-8")
        return

    if source_ext == "txt" and fmt == "pdf":
        font_path = Path(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        )

        if not font_path.exists():
            raise RuntimeError(
                "Не найден шрифт DejaVu Sans для поддержки кириллицы"
            )

        if "DejaVu" not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont("DejaVu", str(font_path)))

        document = SimpleDocTemplate(
            str(target),
            pagesize=A4,
            rightMargin=20 * mm,
            leftMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
        )

        style = ParagraphStyle(
            "CyrillicText",
            fontName="DejaVu",
            fontSize=11,
            leading=16,
            textColor=colors.black,
            wordWrap="CJK",
        )

        text = source.read_text(encoding="utf-8-sig")
        story = []

        for line in text.splitlines():
            if line.strip():
                story.append(Paragraph(escape(line), style))
            else:
                story.append(Spacer(1, 8))

        if not story:
            story.append(Paragraph("", style))

        document.build(story)
        return

    if source_ext in {"png", "jpg", "jpeg"} and fmt in {
        "png", "jpg", "jpeg"
    }:
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
