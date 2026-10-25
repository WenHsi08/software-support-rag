import math


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
    """計算各區塊的分數，回傳由高到低排序的結果。"""

    if len(document_vectors) != len(chunks):
        raise ValueError("文件向量數量與區塊數量不一致。")

    results = []

    for chunk, vector in zip(chunks, document_vectors):
        score = cosine_similarity(question_vector, vector)

        # 建立新字典，保留原本的來源與內容，另外加入分數
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


#   zip(chunks, document_vectors)：把相同位置的區塊與向量配成一組。
#  **chunk：把原字典的欄位放進新字典，再加入 score，不修改原本的區塊。
