from pathlib import Path
import re


# 目前知識文件使用的標題與類型對照
SECTION_TYPES = {
    "仍無法解決時": "support",
    "文件範圍": "scope",
    "操作步驟": "guide",
}


def classify_chunk(text: str) -> str:
    """根據區塊標題判斷用途，無法辨識時保留為 general。"""

    heading = text.splitlines()[0].strip()

    # 例如：## E202：沒有報表匯出權限
    # 接受一個英文字母加三位數字，不限定只能是 E
    if re.match(r"^##\s+[A-Za-z][0-9]{3}(?=：|:|\s|$)", heading):
        return "issue"

    # 文件開頭的一級標題，視為概述
    if heading.startswith("# "):
        return "overview"

    # 取得二級標題文字，再查詢分類對照表
    if heading.startswith("## "):
        title = heading.removeprefix("## ").strip()
        return SECTION_TYPES.get(title, "general")

    return "general"


def load_chunks(docs_dir: Path) -> list[dict]:
    """讀取 Markdown 文件，切分並保留來源與區塊類型。"""

    if not docs_dir.is_dir():
        raise FileNotFoundError(f"找不到知識文件資料夾：{docs_dir}")

    chunks = []

    for document_path in sorted(docs_dir.rglob("*.md")):
        content = document_path.read_text(encoding="utf-8")

        source_id = "未提供文件編號"

        for line in content.splitlines():
            if line.startswith("文件編號："):
                source_id = line.removeprefix("文件編號：").strip()
                break

        source_file = document_path.relative_to(docs_dir).as_posix()

        # 沿用目前依二級標題切分的方式
        sections = content.split("\n## ")

        for index, section in enumerate(sections):
            text = section.strip()

            if not text:
                continue

            if index > 0:
                text = "## " + text

            chunks.append({
                "source_id": source_id,
                "source_file": source_file,
                "chunk_type": classify_chunk(text),
                "content": text,
            })

    return chunks