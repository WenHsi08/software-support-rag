from google import genai
from google.genai import types
from pathlib import Path
from knowledge_base import load_chunks
from retriever import search_chunks


# 沿用目前環境變數中的 API key
client = genai.Client()

project_dir = Path(__file__).resolve().parent

chunks = load_chunks(project_dir / "docs")

print(f"文件共切分成 {len(chunks)} 個區塊。")




# 將各區塊轉成適合被搜尋的文件向量
print("正在將文件區塊轉成向量……")

document_response = client.models.embed_content(
    model="gemini-embedding-001",
    contents=[chunk["content"] for chunk in chunks],
    config=types.EmbedContentConfig(
        task_type="RETRIEVAL_DOCUMENT"
    )
)

document_vectors = [
    embedding.values
    for embedding in document_response.embeddings
]

# 確認每個區塊都有對應的向量
for number, vector in enumerate(document_vectors, start=1):
    print(f"區塊 {number}：向量維度 {len(vector)}")

#----------------------------------------------------------


# 接收自然語言問題，不限制一定要有錯誤代碼
question = input("請輸入你的問題：").strip()

if not question:
    print("你尚未輸入問題。")

else:
    print("\n正在將問題轉成向量……")

    response = client.models.embed_content(
        model="gemini-embedding-001",
        contents=question,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_QUERY"
        )
    )

    # 這次只送入一個問題，因此取第一筆 embedding
    question_vector = response.embeddings[0].values

    print("\n問題：", question)
    print("向量維度：", len(question_vector))
    print("前 5 個數值：", question_vector[:5])    # 這次只送入一個問題，因此取第一筆 embedding
    question_vector = response.embeddings[0].values


    # 比較問題與所有文件區塊，取得排序結果
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
        print(f"來源：{result['source_id']} / {result['source_file']}")