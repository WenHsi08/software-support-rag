from google import genai
from google.genai import types

# 沿用目前環境變數中的 API key
client = genai.Client()

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
    print("前 5 個數值：", question_vector[:5])