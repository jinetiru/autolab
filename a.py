import google.generativeai as genai

# ご自身のAPIキーを入力してください
genai.configure(api_key="AIzaSyCLfXsbCv03jzHM5JVHYfKBwxNK_IyiYD0")

print("利用可能なモデル一覧:")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)