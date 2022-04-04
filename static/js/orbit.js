var tempStr = "<div class='c'></div>"

var result = "";

for(var i=0;i<300;i++){
  result = result + " " + tempStr;
}
var parser = new DOMParser();
    var doc = parser.parseFromString(result, 'text/html');
document.getElementsByClassName("wrap")[0].append(doc.body);