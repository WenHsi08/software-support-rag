import math
import re


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """計算兩個向量的餘弦相似度。"""

    if len(a) != len(b):
        raise ValueError("兩個向量的維度必須相同。")

    # 內積：對應位置相乘後加總
    dot_product = sum(x * y for x, y in zip(a, b))

    # 向量長度
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))

    if norm_a == 0 or norm_b == 0:
        raise ValueError("不能計算零向量的餘弦相似度。")

    return dot_product / (norm_a * norm_b)


def search_chunks(
    question_vector: list[float],
    document_vectors: list[list[float]],
    chunks: list[dict],
) -> list[dict]:
    """計算所有區塊的相似度，回傳由高到低排序的結果。"""

    if len(document_vectors) != len(chunks):
        raise ValueError("文件向量數量與區塊數量不一致。")

    results = []

    # 將相同位置的區塊與向量配成一組
    for chunk, vector in zip(chunks, document_vectors):
        score = cosine_similarity(question_vector, vector)

        # 保留原本欄位，另外加入分數，不修改原始區塊
        result = {
            **chunk,
            "score": score,
        }
        results.append(result)

    return sorted(
        results,
        key=lambda result: result["score"],
        reverse=True,
    )


def select_chunks(
    question: str,
    ranked_chunks: list[dict],
    top_k: int = 2,
) -> dict:
    """有代碼時精確選取，沒有代碼時選取語意搜尋結果。"""

    if top_k < 1:
        raise ValueError("top_k 必須至少為 1。")

    # 目前支援的代碼格式：一個英文字母加三位數字
    # 前後不能緊接其他英文字母或數字，
    # 避免把 AE202、E2020 的一部分誤認成代碼
    found_codes = re.findall(
        r"(?<![A-Za-z0-9])[A-Za-z][0-9]{3}(?![A-Za-z0-9])",
        question,
    )

    # 統一大寫、去除重複，並保留出現順序
    codes = list(dict.fromkeys(
        code.upper() for code in found_codes
    ))

    # ---------- 有明確代碼：精確選取 ----------

    if codes:
        selected = []
        matched_codes = set()

        for chunk in ranked_chunks:
            # 只有 issue 區塊可作為代碼對應的問題說明
            if chunk["chunk_type"] != "issue":
                continue

            heading = chunk["content"].splitlines()[0]

            # 從標題取得代碼，例如：
            # ## E202：沒有報表匯出權限
            match = re.match(
                r"^##\s+([A-Za-z][0-9]{3})(?=：|:|\s|$)",
                heading,
            )

            if match is None:
                continue

            document_code = match.group(1).upper()

            if document_code in codes:
                selected.append(chunk)
                matched_codes.add(document_code)

        # 使用者提到、但文件沒有對應說明的代碼
        unknown_codes = [
            code
            for code in codes
            if code not in matched_codes
        ]

        # 精確代碼選取不受 top_k 限制，
        # 避免使用者同時問多個代碼時漏掉對應區塊
        return {
            "mode": "exact_code",
            "selected_chunks": selected,
            "unknown_codes": unknown_codes,
        }

    # ---------- 沒有代碼：依語意排名選取 ----------

    # scope 與 overview 不占主要搜尋名額。
    # support 仍可被搜尋，以支援「我要聯絡誰」等問題。
    searchable_types = {"issue", "guide", "support", "general"}

    candidates = [
        chunk
        for chunk in ranked_chunks
        if chunk["chunk_type"] in searchable_types
    ]

    return {
        "mode": "semantic",
        "selected_chunks": candidates[:top_k],
        "unknown_codes": [],
    }