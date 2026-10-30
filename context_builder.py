def build_context(
    selected_chunks: list[dict],
    all_chunks: list[dict],
) -> str:
    """組合選中的區塊，以及同來源的支援流程和文件範圍。"""

    context_chunks = []
    seen = set()

    # 使用文件編號與檔案路徑，一起辨識來源
    selected_sources = {
        (chunk["source_id"], chunk["source_file"])
        for chunk in selected_chunks
    }

    # 先放入搜尋選中的區塊
    # 再找出同來源的補充資料
    supplementary_chunks = [
        chunk
        for chunk in all_chunks
        if (chunk["source_id"], chunk["source_file"]) in selected_sources
        and chunk["chunk_type"] in {"support", "scope"}
    ]

    for chunk in selected_chunks + supplementary_chunks:
        # 相同來源、相同內容只加入一次
        key = (
            chunk["source_id"],
            chunk["source_file"],
            chunk["content"],
        )

        if key in seen:
            continue

        seen.add(key)
        context_chunks.append(chunk)

    context_parts = []

    for number, chunk in enumerate(context_chunks, start=1):
        part = (
            f"[參考資料 {number}]\n"
            f"文件編號：{chunk['source_id']}\n"
            f"來源檔案：{chunk['source_file']}\n"
            f"區塊類型：{chunk['chunk_type']}\n"
            f"{chunk['content']}"
        )
        context_parts.append(part)

    return "\n\n".join(context_parts)