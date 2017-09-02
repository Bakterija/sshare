$(function() {
    var bar = $('.bar');
    var speedlabel = $('#speedlabel');
    var percent = $('.percent');
    var status = $('#status');

    $('#manform').ajaxForm({
        beforeSend: function() {
            status.empty();
            var percentVal = '0%';
            bar.width(percentVal);
            percent.html(percentVal);
            upload_start_time = (new Date).getTime();
            pos_log = [];
        },
        uploadProgress: function(event, position, total, percentComplete) {
            var percentVal = percentComplete + '%';
            var speedtext = "";
            bar.width(percentVal);
            percent.html(percentVal);
            pos_log.push([position, (new Date).getTime()]);
            if (pos_log.length == 12){
                var first_pos = pos_log.shift();
                var last_pos = pos_log[10];
                speedtext = (
                    (last_pos[0] - first_pos[0]) / 1000000) / (
                        (last_pos[1] - first_pos[1]) / 1000);
                speedlabel.html(speedtext.toFixed(2).toString() + " MB/s");
            };
        },
        complete: function(xhr) {
            console.log(xhr.status, xhr.responseText);
            if (xhr.status == 200) {
                window.location = xhr.responseText;
            };
        }
    });
});
