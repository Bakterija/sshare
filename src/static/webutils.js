String.prototype.formatUnicorn = String.prototype.formatUnicorn ||
function () {
    "use strict";
    var str = this.toString();
    if (arguments.length) {
        var t = typeof arguments[0];
        var key;
        var args = ("string" === t || "number" === t) ?
            Array.prototype.slice.call(arguments)
            : arguments[0];

        for (key in args) {
            str = str.replace(new RegExp("\\{" + key + "\\}", "gi"), args[key]);
        }
    }

    return str;
};

function bytesToMb() {
    var x = document.getElementsByClassName("bytes-to-mb");
    var i;
    var bytes;
    var result;
    for (i = 0; i < x.length; i++) {
        bytes = parseFloat(x[i].innerText + ".0");
        if (bytes > 1000000.0) {
            result = bytes / 1000000.0;
            x[i].innerText = result.toString() + " MB"
        }
        else {
            result = bytes / 1000.0;
            x[i].innerText = result.toString() + " KB"
        };
    };
};

function copyTextToClipboard(text) {
    console.log("Copy text to clipboard: " + text);
    var $temp = $("<input>");
    $("body").append($temp);
    $temp.val(text);
    $temp.select();
    document.execCommand("copy");
    $temp.remove();
};

function copyElementValueToClipboard(element) {
    var $temp = $("<input>");
    $("body").append($temp);
    $temp.val($(element).text()).select();
    document.execCommand("copy");
    $temp.remove();
};
