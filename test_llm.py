from google import genai

# 自動讀取環境變數中的金鑰
client = genai.Client()

print("正在等待模型回答……")

# 發送文字給模型，並取得回應
response = client.models.generate_content(
    model="gemini-3.8-flash",
    contents="請用繁體中文，以一句話說明你能如何協助使用者排除軟體問題。"
)

# 顯示回應中的文字
print("\n模型回答：")
print(response.text)