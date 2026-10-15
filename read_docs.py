from pathlib import Path
from google import genai
import time


# 以這支 Python 檔案的位置，找出專案資料夾
project_dir = Path(__file__).resolve().parent

# 組合出知識文件的路徑
document_path = project_dir / "docs" / "report_export.md"

# 使用 UTF-8 編碼讀取中文文字
content = document_path.read_text(encoding="utf-8")

# 從文件中尋找文件編號
source_id = "未提供文件編號"

for line in content.splitlines():
    if line.startswith("文件編號："):
        source_id = line.removeprefix("文件編號：").strip()
        break

#print(f"文件名稱：{document_path.name}")
#print(f"文字長度：{len(content)} 個字元")
#print("\n--- 文件內容 ---")
#print(content)

##-------------------------------------------

# 依照 Markdown 的二級標題切分文件
sections = content.split("\n## ")

chunks = []

for index, section in enumerate(sections):
    # 移除區塊前後的空白與換行
    text = section.strip()

    # 跳過沒有內容的區塊
    if not text:
        continue

    # split 會移除分隔符號，補回後續區塊的標題符號
    if index > 0:
        text = "## " + text

    chunks.append(text)

#print(f"\n--- 切分結果：共 {len(chunks)} 個區塊 ---")

#for number, chunk in enumerate(chunks, start=1):
#    print(f"\n[區塊 {number}]")
#    print(chunk)

##測試關鍵字檢索--------------------------------------------------------

def search_error_code(chunks, query, source_id, source_file):
    # 每次搜尋，都建立新的結果列表
    results = []

    for chunk in chunks:
        heading = chunk.splitlines()[0]

        if heading.startswith("## E"):
            heading_text = heading.removeprefix("## ")
            error_code = heading_text.split("：")[0].strip().upper()

            if query == error_code:
                result = {
                    "source_id": source_id,
                    "source_file": source_file,
                    "content": chunk
                }

                results.append(result)

    return results

# 取得使用者輸入，移除前後空白，並統一轉成大寫
query = input("\n請輸入錯誤代碼，例如 E201：").strip().upper()


if not query:
    print("你尚未輸入錯誤代碼。")

elif not (
    len(query) == 4
    and query.startswith("E")
    and query[1:].isascii()
    and query[1:].isdigit()
):
    print("請輸入完整錯誤代碼，例如 E201（E 加上三位數字）。")

else:
    # 呼叫函式，把回傳的列表存入 matched_chunks
    matched_chunks = search_error_code(
        chunks,
        query,
        source_id,
        document_path.name
    )

    #暫時測試用
    #print("回傳資料的型別：", type(matched_chunks))
    #print("結果筆數：", len(matched_chunks))
    #print("回傳的完整資料：", matched_chunks)

    if matched_chunks:
        print(f"\n找到 {len(matched_chunks)} 個錯誤代碼相符的區塊：")

        for number, result in enumerate(matched_chunks, start=1):
            print(f"\n[搜尋結果 {number}]")
            print(f"文件編號：{result['source_id']}")
            print(f"來源檔案：{result['source_file']}")
            #print(result["content"])

# 將每筆結果整理成帶有來源的文字
        context_parts = []

        for result in matched_chunks:
            part = (
                f"文件編號：{result['source_id']}\n"
                f"來源檔案：{result['source_file']}\n"
                f"{result['content']}"
            )
            context_parts.append(part)

        # 用空白行分隔各筆參考資料
        context = "\n\n".join(context_parts)

        print("\n--- 準備提供給 LLM 的參考資料 ---")
        #print(context)

                # 組合回答規則、參考資料與使用者問題
        prompt = f"""你是 HelpDesk Lite 的軟體支援助手。

回答規則：
1. 使用繁體中文，先直接回答使用者最在意的問題，再補充必要步驟，避免重複。
2. 原因、解法與流程必須有參考資料支持，不得自行補充未記載的規定。
3. 區分「文件明確記載」與「文件沒有提供資訊」。未提到某方法有效，不代表已證明該方法無效或完全無關。
4. 如果只能確認部分原因，請使用「根據目前文件」或「此錯誤代碼對應的是」等限定說法，不要把局部資訊推廣成全面結論。
5. 資料不足以回答時，明確說明缺少什麼，並提出必要的釐清問題。
6. 回答最後標示使用的文件編號與檔名。
7. 不得聲稱已上報、已記錄或已開通權限，因為目前沒有執行這些動作。

以下是參考資料：
<reference>
{context}
</reference>

使用者問題：
我在匯出工單報表時遇到 {query}。同事說把日期縮短就可以，
但我不知道這跟權限有沒有關係。請根據文件說明，
我現在應該先找主管還是資訊支援部門？為什麼？
"""

        print("\n--- 準備提供給 LLM 的提示詞 ---")
        print(prompt)

        client = genai.Client()

        print("\n正在根據文件產生回答……")
        start_time = time.perf_counter()

        # 將包含規則、參考資料與問題的提示詞送給模型
        response = client.models.generate_content(
            model = "gemini-3.8-flash",
            contents = prompt
        )

        elapsed = time.perf_counter() - start_time

        print(f"\n本次 API 等待時間：{elapsed:.1f} 秒")
        print("\n---助手回答---")
        print(response.text)

    else:
        print("\n目前文件沒有此錯誤代碼的說明，無法確認原因。")