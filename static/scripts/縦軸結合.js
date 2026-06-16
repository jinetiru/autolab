if (documents.length > 0) {
    var doc = activeDocument;
    var sel = null;
    var isError = false;

    // テキスト編集モード中のエラー回避
    try {
        sel = doc.selection;
    } catch(e) {
        isError = true;
    }

    if (isError) {
        alert("Error: You are in Text-Edit mode.\nPlease press ESC key or use the Black Arrow tool to select objects, then run again.");
    } else if (sel !== null && sel.length >= 2) {
        
        // 選択範囲からテキストオブジェクトのみを抽出
        var textItems = [];
        for (var i = 0; i < sel.length; i++) {
            if (sel[i].typename == "TextArtItem" || sel[i].typename == "TextFrame") {
                textItems.push(sel[i]);
            }
        }

        if (textItems.length >= 2) {
            
            // 【ステップ1】すべてを-90度回転
            for (var r = 0; r < textItems.length; r++) {
                textItems[r].rotate(-90);
            }

            // 【ステップ2】X座標（左から右）の順番に並び替え
            var len = textItems.length;
            for (var a = 0; a < len - 1; a++) {
                for (var b = 0; b < len - 1 - a; b++) {
                    if (textItems[b].position[0] > textItems[b+1].position[0]) {
                        var temp = textItems[b];
                        textItems[b] = textItems[b+1];
                        textItems[b+1] = temp;
                    }
                }
            }

            // 【ステップ3】最初のテキストに文字をすべて結合
            var baseItem = textItems[0];
            var combinedText = baseItem.contents;

            for (var k = 1; k < textItems.length; k++) {
                combinedText += textItems[k].contents;
                // 結合した後の不要なテキストオブジェクトを削除
                textItems[k].remove();
            }
            
            baseItem.contents = combinedText;

            baseItem.resize(138.8, 138.8);

            // 【ステップ4】完成した1つのオブジェクトを90度回転して元の向きに戻す
            baseItem.rotate(90);

            alert("Done! Vertical texts combined successfully.");
            
        } else {
            alert("Please select 2 or more text objects.");
        }
    } else {
        alert("Please select 2 or more objects first.");
    }
} else {
    alert("No document open.");
}