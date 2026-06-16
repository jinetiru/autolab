if (documents.length > 0) {
    var doc = activeDocument;
    var textItems = doc.textArtItems; 
    var changedCount = 0;

    for (var i = 0; i < textItems.length; i++) {
        var textItem = textItems[i];
        
        // Python側でここに「10」や「20」など抽出した数値の条件式を自動挿入します
        if (/*_CONDITION_*/) {
            
           
            textItem.resize(120.240, 120.240);
            changedCount++;
        }
    }
    
    if (changedCount > 0) {
        alert("Done! Scaled " + changedCount + " text item(s).");
    } else {
        alert("Target texts not found.");
    }
} else {
    alert("Please open a document first.");
}