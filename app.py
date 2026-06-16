from flask import Flask, render_template, request, redirect, session, url_for, send_from_directory
import os
import json
from PIL import Image
import google.generativeai as genai

app = Flask(__name__)
app.secret_key = 'lab_automation_secret_key'

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ==========================================
# Gemini APIの設定（取得したAPIキーを入力してください）
# ==========================================
GEMINI_API_KEY = "AIzaSyCLfXsbCv03jzHM5JVHYfKBwxNK_IyiYD0"
genai.configure(api_key=GEMINI_API_KEY)


# (中略：index, login, select_experiment, analyze, upload_pageは元のまま)
@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    user_id = request.form.get('user_id')
    password = request.form.get('password')
    if user_id == 'photonics' and password == 'pmelab':
        return redirect(url_for('select_experiment'))
    else:
        return render_template('login.html', error='ログインできません')

@app.route('/select_experiment')
def select_experiment():
    return render_template('select_experiment.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    selected_type = request.form.get('experiment_type')
    if selected_type:
        session['experiment_type'] = selected_type
        return redirect(url_for('upload_page'))
    return redirect(url_for('select_experiment'))

@app.route('/upload')
def upload_page():
    exp_type = session.get('experiment_type')
    if not exp_type:
        return redirect(url_for('select_experiment'))
    return render_template('upload.html', exp_type=exp_type)

# ==========================================
# ファイル受け取りとGemini API解析処理
# ==========================================
@app.route('/upload_file', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'ファイルがアップロードされていません'
    
    file = request.files['file']
    if file.filename == '':
        return 'ファイルが選択されていません'

    if file and file.filename.lower().endswith('.eps'):
        filename = file.filename
        eps_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(eps_path)

        exp_type = session.get('experiment_type')

        # 1. EPSをPNGに変換する（GeminiはEPSを直接読めないため）
        png_path = os.path.splitext(eps_path)[0] + '.png'
        try:
            img = Image.open(eps_path)
            # EPSの背景が透過している場合があるため、白背景を追加して保存
            img.load(scale=2) # 画質を少し上げる
            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                bg = Image.new("RGB", img.size, (255, 255, 255))
                bg.paste(img, mask=img.split()[3])
                bg.save(png_path, 'PNG')
            else:
                img.save(png_path, 'PNG')
        except Exception as e:
            return f"画像変換エラー（Ghostscriptがインストールされているか確認してください）: {e}"

        # 2. Gemini APIで数値を読み取る
        try:
            # 画像をGeminiにアップロード
            gemini_file = genai.upload_file(png_path)
            
            # JSON形式で確実に出力させるための設定
            model = genai.GenerativeModel(
                'gemini-2.5-flash',
                generation_config={"response_mime_type": "application/json"}
            )
            
            # プロンプト（指示）
            prompt = """
            このグラフ画像を解析し、縦軸（Y軸）と横軸（X軸）の目盛りとして記述されている「数値」をすべて抽出してください。
            ラベル名や単位（例: degree, Intensityなど）は除外し、純粋な数字のみを取り出してください。
            出力は以下のJSONフォーマットのみで行ってください。
            {"numbers": ["10", "20", "30", "40", "-10", "0", ...]}
            """
            
            response = model.generate_content([gemini_file, prompt])
            ai_result = json.loads(response.text)
            axis_numbers = ai_result.get("numbers", [])
            
        except Exception as e:
            return f"Gemini API解析エラー: {e}"

        # 3. 取得した数値リストを使って template.js を書き換える
        script_name = "generated_script.js"
        output_js_path = os.path.join(app.config['UPLOAD_FOLDER'], script_name)
        
        try:
            generate_dynamic_js("template.js", output_js_path, axis_numbers)
        except Exception as e:
            # 失敗した場合はここで処理を止め、画面にエラーを表示する
            return f"スクリプト生成エラー: {e}"

        # 成功した場合のみ結果画面へ
        return render_template('result.html', filename=filename, exp_type=exp_type, script_name=script_name, detected_numbers=axis_numbers)

    return "対応していないファイル形式です（EPSファイルをアップロードしてください）。"

# ==========================================
# JS生成用ヘルパー関数
# ==========================================
def generate_dynamic_js(template_path, output_path, numbers):
    """
    Geminiが抽出した数値のリストを使って、JSの条件式を動的に生成する関数
    """
    # テンプレートが存在するか先にチェックする！
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"テンプレートファイルが見つかりません: {template_path} (app.pyと同じ階層に置いてください)")
        
    with open(template_path, 'r', encoding='utf-8') as f:
        js_code = f.read()

    conditions = []
    for num in numbers:
        conditions.append(f'textItem.contents.indexOf("{num}") !== -1')
    
    condition_str = " || ".join(conditions) if conditions else "false"
    final_code = js_code.replace("/*_CONDITION_*/", condition_str)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_code)
    
@app.route('/download/<filename>')
def download_file(filename):
    """
    生成されたスクリプトファイルをブラウザにダウンロードさせるためのルート
    """
    return send_from_directory(
        app.config['UPLOAD_FOLDER'], 
        filename, 
        as_attachment=True # これを入れることでブラウザで開かず「ダウンロード」になります
    )

if __name__ == '__main__':
    app.run(debug=True)