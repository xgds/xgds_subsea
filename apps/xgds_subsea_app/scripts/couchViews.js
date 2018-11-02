{
  "_id": "_design/deepzoom",
  "language": "javascript",
  "views": {
    "tiledImages": {
      "map": "function(doc) {\n   var len = doc.basename.length;\n   var ext = doc.basename.substring(len-4,len);\n   if (ext == \".dzi\") {\n      emit(doc.basename, doc);\n   }\n}",
      "reduce": "_count"
    },
    "tiledImageTiles": {
      "map": "function(doc) {\n   if (doc.basename.match(/\\d+_\\d+\\.jpg/i)) {\n      nameTailParts = doc.name.split(\"/\").slice(-2);\n      // Generate key from base filename and zoom level\n      nameKey = nameTailParts[0] + \":\" + nameTailParts[1];\n      emit(nameKey, doc);\n   }\n}",
      "reduce": "_count"
    },
    "baseImages": {
      "map": "function(doc) {\n   var dzIndex = doc.name.indexOf(\"_deepzoom_\");\n   var thumbnailIndex = doc.basename.indexOf(\"_thumbnail\");\n   if (dzIndex == -1 && thumbnailIndex == -1) {\n      emit(doc.basename, doc);\n   }\n}",
      "reduce": "_count"
    },
    "thumbnailImages": {
      "map": "function(doc) {\n   var dzIndex = doc.name.indexOf(\"_deepzoom_\");\n   var thumbnailIndex = doc.basename.indexOf(\"_thumbnail\");\n   if (dzIndex == -1 && thumbnailIndex != -1) {\n      emit(doc.basename, doc);\n   }\n}",
      "reduce": "_count"
    }
  }
}
