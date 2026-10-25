from google import genai


# 建立 API 用戶端，自動讀取環境變數 GEMINI_API_KEY
client = genai.Client()

print("支援生成內容的模型：")

# 向 Google 取得模型列表
for model in client.models.list():
    # 只顯示支援 generateContent 的模型
    if "generateContent" in (model.supported_actions or []):
        print(model.name)