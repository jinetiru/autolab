
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
    