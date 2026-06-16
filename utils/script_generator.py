import os

def generate_illustrator_script(ai_json_data, output_filename="test_single_a.js"):
    js_code = """
    if (documents.length > 0) {
        var doc = activeDocument;
        
        var testLayer = doc.layers.add();
        testLayer.name = "Test_Layer_A";
        
        var tf = testLayer.textArtItems.add();
        
        // 1. NRSMを回避する文字の流し込み
        tf.textRange.contents = "a";
        
        // 2. 座標の指定
        tf.position = Array(150, -150);
        
        // 3. AI10専用の直接指定文法（characterAttributesは使わない）
        tf.size = 12;
        tf.font = "ArialMT";
        
        alert("Success: 'a' was created in Arial!");
    }
    """
    
    save_dir = 'generated'
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
        
    save_path = os.path.join(save_dir, output_filename)
    
    # UTF-8で出力
    with open(save_path, 'w', encoding='utf-8') as f:
        f.write(js_code)
        
    return output_filename