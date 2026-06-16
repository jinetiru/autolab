from flask import Flask, render_template, request, redirect, session, url_for, send_from_directory
import os
import json
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
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)


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

    # PNGに加えて、.jpg と .jpeg も許可するように修正
    if file and file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        filename = file.filename
        img_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(img_path) # アップロードされた画像をそのまま保存

        exp_type = session.get('experiment_type')

        # 2. Gemini APIで数値を読み取る
        try:
            # 保存した画像をそのままGeminiにアップロード（PNGもJPGも対応）
            gemini_file = genai.upload_file(img_path)
            
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
            return f"Gemini API解析エラー: {type(e).__name__}: {e}"

        # 3. 取得した数値リストを使って template.js を書き換える
        script_name = "generated_script.js"
        output_js_path = os.path.join(app.config['UPLOAD_FOLDER'], script_name)
        
        try:
            generate_dynamic_js("template.js", output_js_path, axis_numbers)
        except Exception as e:
            return f"スクリプト生成エラー: {e}"

        # 成功した場合のみ結果画面へ
        return render_template('result.html', filename=filename, exp_type=exp_type, script_name=script_name, detected_numbers=axis_numbers)

    # エラーメッセージもPNG/JPG用に変更
    return "対応していないファイル形式です（PNGまたはJPGファイルをアップロードしてください）。"

# ==========================================
# JS生成用ヘルパー関数
# ==========================================
def generate_dynamic_js(template_path, output_path, numbers):
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
    return send_from_directory(
        app.config['UPLOAD_FOLDER'], 
        filename, 
        as_attachment=True
    )

if __name__ == '__main__':
    app.run(debug=True)