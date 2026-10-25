import hashlib
from pathlib import Path

from google import genai
from google.genai import types

from knowledge_base import load_chunks
from retriever import search_chunks
from context_builder import build_context
from storage import init_db, save_document, load_document_vectors


# 統一問題與文件使用的 Embedding 設定
EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIMENSIONS = 3072

# 自動讀取環境變數中的 API key
client = genai.Client()

project_dir = Path(__file__).resolve().parent
docs_dir = project_dir / "docs"
db_path = project_dir / "data" / "knowledge.db"

init_db(db_path)

# 讀取、切分並分類文件
chunks = load_chunks(docs_dir)

if not chunks:
    raise ValueError("沒有找到可使用的文件區塊。")

print(f"文件共切分成 {len(chunks)} 個區塊。")


# ---------- 載入或產生文件向量 ----------

document_vectors = []

# 取得不重複的來源檔案，保留原本順序
source_files = list(dict.fromkeys(
    chunk["source_file"] for chunk in chunks
))

for source_file in source_files:
    document_chunks = [
        chunk
        for chunk in chunks
        if chunk["source_file"] == source_file
    ]

    # 計算文件指紋，檢查文件內容是否改變
    document_path = docs_dir / source_file
    content_hash = hashlib.sha256(
        document_path.read_bytes()
    ).hexdigest()

    # 先嘗試從 SQLite 載入可使用的向量
    vectors = load_document_vectors(
        db_path=db_path,
        source_file=source_file,
        source_id=document_chunks[0]["source_id"],
        content_hash=content_hash,
        chunks=document_chunks,
        model=EMBEDDING_MODEL,
        dimensions=EMBEDDING_DIMENSIONS,
    )

    if vectors is not None:
        # 有可用快取，不呼叫文件 Embedding API
        print(f"直接載入文件向量：{source_file}")

    else:
        # 沒有可用快取，才呼叫 API
        print(f"正在產生文件向量：{source_file}")

        document_response = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=[
                chunk["content"]
                for chunk in document_chunks
            ],
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_DOCUMENT",
                output_dimensionality=EMBEDDING_DIMENSIONS,
            ),
        )

        vectors = [
            embedding.values
            for embedding in document_response.embeddings
        ]

        # 保存這份文件的區塊與向量
        save_document(
            db_path=db_path,
            source_file=source_file,
            source_id=document_chunks[0]["source_id"],
            content_hash=content_hash,
            chunks=document_chunks,
            vectors=vectors,
            model=EMBEDDING_MODEL,
        )

        print(
            f"已保存：{source_file}，"
            f"共 {len(document_chunks)} 個區塊與向量。"
        )

    # load_chunks 按文件順序產生區塊，
    # 這裡依相同順序加入對應向量
    document_vectors.extend(vectors)

# 檢查區塊與向量數量是否一致
if len(chunks) != len(document_vectors):
    raise ValueError("文件區塊與向量數量不一致。")

for number, vector in enumerate(document_vectors, start=1):
    print(f"區塊 {number}：向量維度 {len(vector)}")


# ---------- 使用者問題向量化 ----------

question = input("\n請輸入你的問題：").strip()

if not question:
    print("你尚未輸入問題。")

else:
    print("\n正在將問題轉成向量……")

    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=question,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=EMBEDDING_DIMENSIONS,
        ),
    )

    question_vector = response.embeddings[0].values

    print("\n問題：", question)
    print("向量維度：", len(question_vector))
    print("前 5 個數值：", question_vector[:5])


    # ---------- 相似度搜尋 ----------

    results = search_chunks(
        question_vector,
        document_vectors,
        chunks,
    )

    print("\n--- 檢索結果：依相似度由高到低 ---")

    for rank, result in enumerate(results, start=1):
        heading = result["content"].splitlines()[0]

        print(f"\n第 {rank} 名｜相似度：{result['score']:.4f}")
        print(f"標題：{heading}")
        print(
            f"來源：{result['source_id']} / "
            f"{result['source_file']}"
        )


    # ---------- 組合 LLM 參考資料 ----------

    # 暫時取前兩名，尚未加入門檻與精確代碼選取
    selected_chunks = results[:2]

    context = build_context(
        selected_chunks,
        chunks,
    )

    print("\n--- 準備提供給 LLM 的參考資料 ---")
    print(context)