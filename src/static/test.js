window.onload = (function(){
    // make and print array
    var b = [];
    b.push([22, 23]);
    console.log(b.toString(), b.length);
});

window.setInterval(function(){
    var a = 2;
    console.log(((new Date).getTime() / 1000).toString());
}, 1000);
