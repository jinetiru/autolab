if (documents.length > 0) {
    var doc = activeDocument;
    var sel = doc.selection;
    var textItems = [];

    if (sel.length > 0) {
        // Get only text objects from selection
        for (var i = 0; i < sel.length; i++) {
            if (sel[i].typename == "TextArtItem" || sel[i].typename == "TextFrame") {
                textItems.push(sel[i]);
            }
        }

        if (textItems.length >= 2) {
            
            // Manual sorting to avoid Illustrator 10 native sort bug
            var len = textItems.length;
            for (var i = 0; i < len - 1; i++) {
                for (var j = 0; j < len - 1 - i; j++) {
                    // Compare X position (position[0])
                    if (textItems[j].position[0] > textItems[j+1].position[0]) {
                        var temp = textItems[j];
                        textItems[j] = textItems[j+1];
                        textItems[j+1] = temp;
                    }
                }
            }

            // Combine text into the first object
            var baseItem = textItems[0];
            var combinedText = baseItem.contents;

            for (var k = 1; k < textItems.length; k++) {
                combinedText += textItems[k].contents;
            }
            
            baseItem.contents = combinedText;

            // Remove the rest of the text objects (from back to front)
            for (var m = textItems.length - 1; m >= 1; m--) {
                textItems[m].remove();
            }

            // --- 追加部分：フォントサイズを1.388倍（138.8%）に拡大 ---
            baseItem.resize(138.8, 138.8);

            alert("Done! Combined into one object and resized to 1.388x.");
        } else {
            alert("Please select 2 or more text objects.");
        }
    } else {
        alert("Please select text objects first.");
    }
} else {
    alert("No document open.");
}