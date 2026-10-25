from pathlib import Path


def load_chunks(docs_dir: Path) -> list[dict]:
    """讀取資料夾內的 Markdown 文件，切分並保留來源資訊。"""

    if not docs_dir.is_dir():
        raise FileNotFoundError(f"找不到知識文件資料夾：{docs_dir}")

    chunks = []

    # 搜尋資料夾與子資料夾中的 Markdown 文件
    for document_path in sorted(docs_dir.rglob("*.md")):
        content = document_path.read_text(encoding="utf-8")

        # 每份文件各自取得文件編號
        source_id = "未提供文件編號"

        for line in content.splitlines():
            if line.startswith("文件編號："):
                source_id = line.removeprefix("文件編號：").strip()
                break

        # 沿用目前依二級標題切分的方式
        sections = content.split("\n## ")

        for index, section in enumerate(sections):
            text = section.strip()

            if not text:
                continue

            if index > 0:
                text = "## " + text

            # 保存相對路徑，避免子資料夾內有同名檔案時混淆
            source_file = document_path.relative_to(docs_dir).as_posix()

            chunks.append({
                "source_id": source_id,
                "source_file": source_file,
                "content": text
            })

    return chunks