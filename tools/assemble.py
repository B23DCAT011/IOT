"""
Ghep BIA (lay tu MauBaoCao.docx) + MUC LUC tu dong + THAN BAI (build/body.docx)
thanh file bao cao hoan chinh theo dung mau PTIT.

Cach dung:
    python tools/build_body.py docs/01-SRS.md
    python tools/assemble.py "ĐẶC TẢ YÊU CẦU PHẦN MỀM (SRS)" docs/01-SRS.docx

Yeu cau: Microsoft Word da cai tren may.
"""
import sys, os, win32com.client as win32

# Console Windows mac dinh la cp1252 -> print chuoi tieng Viet se nem
# UnicodeEncodeError va lam hong ca tien trinh Word dang mo dang dang.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(ROOT, "docs", "MauBaoCao.docx")
BODY = os.path.join(ROOT, "build", "body.docx")

# ---- Thong tin trang bia: SUA O DAY ----------------------------------------
# Nhung dong KHONG doi giua cac tai lieu.
COVER_FIXED = [
    ("BÁO CÁO BÀI THỰC HÀNH", "BÁO CÁO BÀI TẬP LỚN"),
    ("HỌC PHẦN: THỰC TẬP CƠ SỞ", "HỌC PHẦN: IOT VÀ ỨNG DỤNG"),
    ("MÃ HỌC PHẦN: INT13147", "MÃ HỌC PHẦN: INT14149"),
    ("<Mã sinh viên>", "B23DCAT011"),
    ("<Họ tên sinh viên>", "Lưu Đức Anh"),
    ("<Chức danh> + <Họ tên GV>", "TS. Nguyễn Quốc Uy"),
    ("HỌC KỲ 2 NĂM HỌC 2024-2025", "HỌC KỲ 1 NĂM HỌC 2026-2027"),
]

# Hai dong doi theo tung tai lieu, truyen tu dong lenh.
LABEL_PLACEHOLDER = "BÀI THỰC HÀNH 1.1"
TITLE_PLACEHOLDER = "CÀI ĐẶT HỆ ĐIỀU HÀNH MÁY TRẠM WINDOWS"
DEFAULT_LABEL = "TÀI LIỆU"
# ---------------------------------------------------------------------------

WD_PAGE_BREAK = 7
WD_REPLACE_ALL = 2
WD_COLLAPSE_END = 0
WD_STORY = 6


def main():
    doc_title = sys.argv[1] if len(sys.argv) > 1 else "TÀI LIỆU"
    out = sys.argv[2] if len(sys.argv) > 2 else "docs/output.docx"
    doc_label = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_LABEL
    if not os.path.isabs(out):
        out = os.path.join(ROOT, out)

    cover = COVER_FIXED + [
        (LABEL_PLACEHOLDER, doc_label),
        (TITLE_PLACEHOLDER, doc_title),
    ]

    if not os.path.exists(BODY):
        sys.exit("Chua co build/body.docx — chay tools/build_body.py truoc.")

    # DispatchEx: luon tao mot tien trinh Word RIENG thay vi bam vao instance
    # dang chay. Neu bam nham vao mot instance dang loi thi doi tuong tra ve
    # khong phan giai duoc, bao "AttributeError: Open.Paragraphs".
    word = win32.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    try:
        # Mo mau o che do CHI DOC. Hai ly do:
        #  1. Script khong bao gio sua mau — no chi sua trong bo nho roi SaveAs
        #     sang file dich, nen khong can quyen ghi.
        #  2. Mo ghi thi Word tao file khoa "~$auBaoCao.docx" ben canh. Neu tien
        #     trinh Word chet bat thuong, file khoa o lai va lan chay sau se bat
        #     hop thoai "file dang duoc mo" — hop thoai nay VO HINH vi
        #     Visible=False, khien script treo vo thoi han thay vi bao loi.
        # Tham so theo VI TRI: FileName, ConfirmConversions, ReadOnly,
        #                      AddToRecentFiles
        doc = word.Documents.Open(TEMPLATE, False, True, False)

        # 1) Xoa toan bo phan sau trang bia (tu doan "MỤC LỤC" den het)
        start = None
        for i in range(1, doc.Paragraphs.Count + 1):
            if doc.Paragraphs(i).Range.Text.strip() == "MỤC LỤC":
                start = doc.Paragraphs(i).Range.Start
                break
        if start is None:
            sys.exit("Khong tim thay doan 'MỤC LỤC' trong mau.")
        doc.Range(start, doc.Content.End).Delete()

        # 2) Thay noi dung trang bia.
        # Phai truyen tham so theo VI TRI: COM late-binding bo qua tham so dat ten.
        # Execute(FindText, MatchCase, MatchWholeWord, MatchWildcards,
        #         MatchSoundsLike, MatchAllWordForms, Forward, Wrap,
        #         Format, ReplaceWith, Replace)
        for old, new in cover:
            f = doc.Content.Find
            f.ClearFormatting()
            f.Replacement.ClearFormatting()
            ok = f.Execute(old, True, False, False, False, False,
                           True, 1, False, new, WD_REPLACE_ALL)
            print(("  [OK] " if ok else "  [!!] ") + old[:45])

        # 3) Them trang MUC LUC
        rng = doc.Content
        rng.Collapse(WD_COLLAPSE_END)
        rng.InsertBreak(WD_PAGE_BREAK)

        rng = doc.Content
        rng.Collapse(WD_COLLAPSE_END)
        rng.InsertParagraphAfter()
        rng = doc.Paragraphs(doc.Paragraphs.Count).Range
        rng.Text = "MỤC LỤC"
        # Ep ve style Normal (wdStyleNormal = -1): neu de nguyen style tieu de
        # cua mau thi chinh dong "MỤC LỤC" se tu lot vao bang muc luc.
        rng.Style = -1
        rng.ParagraphFormat.OutlineLevel = 10      # wdOutlineLevelBodyText
        rng.ParagraphFormat.Alignment = 1          # can giua
        rng.Font.Bold = True
        rng.Font.Size = 14

        rng = doc.Content
        rng.Collapse(WD_COLLAPSE_END)
        rng.InsertParagraphAfter()
        toc_rng = doc.Paragraphs(doc.Paragraphs.Count).Range
        toc_rng.ParagraphFormat.Alignment = 0
        doc.TablesOfContents.Add(toc_rng, True, 1, 3)

        # 4) Chen than bai sang trang moi
        rng = doc.Content
        rng.Collapse(WD_COLLAPSE_END)
        rng.InsertBreak(WD_PAGE_BREAK)
        rng = doc.Content
        rng.Collapse(WD_COLLAPSE_END)
        rng.InsertFile(BODY)

        # 5) Danh so trang o chan trang
        for sec in doc.Sections:
            footer = sec.Footers(1)          # wdHeaderFooterPrimary
            footer.Range.Fields.Add(footer.Range, 33)   # wdFieldPage
            footer.Range.ParagraphFormat.Alignment = 1

        # 6) Cap nhat muc luc va luu
        doc.TablesOfContents(1).Update()
        doc.SaveAs2(out, 16)                 # wdFormatDocumentDefault (.docx)
        pages = doc.ComputeStatistics(2)
        tables = doc.Tables.Count
        doc.Close(False)
        print("Da tao :", out)
        print("So trang:", pages, "| So bang:", tables, "| Tieu de:", doc_title)
    finally:
        word.Quit()


if __name__ == "__main__":
    main()
