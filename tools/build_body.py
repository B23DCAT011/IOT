"""
Chuyen file Markdown trong docs/ thanh phan THAN BAI (body.docx)
theo dung style cua MauBaoCao.docx (PTIT).

Cach dung:
    python tools/build_body.py docs/01-SRS.md

Ket qua: build/body.docx  (chi co noi dung, chua co bia va muc luc)
Buoc ghep bia + muc luc do tools/assemble.ps1 dam nhiem.
"""
import sys, os, re, pypandoc

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(ROOT, "docs", "MauBaoCao.docx")
BUILD = os.path.join(ROOT, "build")


def split_fences(text):
    """Tach van ban thanh cac doan (is_code, noi_dung) de khong dong vao code block."""
    parts, buf, in_code = [], [], False
    for line in text.splitlines(keepends=True):
        if line.lstrip().startswith("```"):
            parts.append((in_code, "".join(buf)))
            buf = [line]
            in_code = not in_code
            continue
        buf.append(line)
    parts.append((in_code, "".join(buf)))
    return parts


def fix_image_paths(md):
    """Doi duong dan anh tuong doi -> tuyet doi.

    Pandoc chay voi thu muc lam viec la build/, nen 'docs/img/x.png' se khong
    tim thay. Thay bang duong dan tuyet doi tinh tu goc du an.
    """
    root = ROOT.replace("\\", "/")
    return re.sub(r"!\[([^\]]*)\]\((?!https?:)([^)]+)\)",
                  lambda m: "![%s](%s/%s)" % (m.group(1), root, m.group(2)),
                  md)


def transform(md):
    """Bo phan dau file, nang cap bac heading theo mau PTIT."""
    lines = md.splitlines(keepends=True)

    # Bo tu dau file den truoc muc "## 1. ..." (bia va muc luc se do Word tao)
    start = next((i for i, l in enumerate(lines) if re.match(r"^## \d+\. ", l)), 0)
    md = "".join(lines[start:])

    out = []
    for is_code, chunk in split_fences(md):
        if is_code:
            out.append(chunk)
            continue
        # Dung ky tu danh dau \x00 de cac lan thay the khong de len nhau
        chunk = re.sub(r"^##### ", lambda m: "\x00#### ", chunk, flags=re.M)
        chunk = re.sub(r"^#### ", lambda m: "\x00### ", chunk, flags=re.M)
        chunk = re.sub(r"^### ", lambda m: "\x00## ", chunk, flags=re.M)
        chunk = re.sub(r"^## (\d+)\. (.+)$",
                       lambda m: "\x00# CHƯƠNG %s. %s" % (m.group(1), m.group(2)),
                       chunk, flags=re.M)
        out.append(fix_image_paths(chunk.replace("\x00", "")))
    return "".join(out)


def main():
    if len(sys.argv) < 2:
        sys.exit("Thieu tham so: python tools/build_body.py docs/01-SRS.md")

    src = sys.argv[1]
    if not os.path.isabs(src):
        src = os.path.join(ROOT, src)

    os.makedirs(BUILD, exist_ok=True)
    md = transform(open(src, encoding="utf8").read())

    tmp_md = os.path.join(BUILD, "_body.md")
    with open(tmp_md, "w", encoding="utf8") as f:
        f.write(md)

    out = os.path.join(BUILD, "body.docx")
    pypandoc.convert_file(
        tmp_md, "docx", outputfile=out,
        extra_args=["--reference-doc=" + TEMPLATE, "--wrap=none"],
    )
    print("Nguon      :", src)
    print("Than bai   :", out, os.path.getsize(out), "bytes")
    print("So CHUONG  :", len(re.findall(r"^# CHƯƠNG ", md, flags=re.M)))


if __name__ == "__main__":
    main()
