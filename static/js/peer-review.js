(function ($) {
    function PeerReview() {
        var self = this;
    }
    PeerReview.prototype.intake = function () {
        var self = this;
        socket.on('all-reports', function (res) {
            var reports = "<table>";
            for (var i = 0, len = res.reports.length; i < len; ++i) {
                reports += "<tr>";
                reports += "<td><a href='#' onclick=\"socket.emit('get-report', {'username': '" + res.reports[i].username + "', 'report-id': '" + res.reports[i].report_id + "'})\">" + res.reports[i].report_id + "</a></td>";
                reports += "<td><a href='#' onclick=\"socket.emit('get-report', {'username': '" + res.reports[i].username + "', 'report-id': '" + res.reports[i].report_id + "'})\">" + res.reports[i].username + "</a></td>";
                reports += "<td><a href='#' onclick=\"socket.emit('get-report', {'username': '" + res.reports[i].username + "', 'report-id': '" + res.reports[i].report_id + "'})\">" + res.reports[i].timestamp + "</td>";
                reports += "</tr>";
            }
            reports += "</table>";
            $('#review-display').html(reports);
        });
        socket.on('users', function (res) {
            var userlist = "<ul class='plain'>";
            for (var i = 0, len = res.users.length; i < len; ++i) {
                userlist += "<li><a href='#' onclick=\"socket.emit('get-report', {'username': '" + res.users[i] + ", 'report-id': '" + res.report_ids[i] + "'})\">" + res.users[i] + "</a></li>";
            }
            userlist += "</ul>";
            $('#review-display').html(userlist);
        });
        socket.on('reports', function (res) {
            for (var i = 0, len = res.reports.length; i < len; ++i) {
                console.log(res.reports[i]);
                console.log(res.timestamps[i]);
            }
        });
        socket.on('report', function (res) {
            window.report_displayed = true;
            var report_display = "<ul class='plain'>";
            report_display += "<li>Creator: <b>" + res.username + "</b></li>";
            report_display += "<li>Report ID: " + res.report_id + "</li>";
            report_display += "<li>" + res.timestamp + "</li>";
            report_display += "<li class='report-body'>" + res.report + "</li>";
            report_display += "</ul>";
            $('#review-display').html(report_display);
            $('#review-entry').show();
            $('#report-id').val(res.report_id.toString());
        });
        return self;
    };
    PeerReview.prototype.exhaust = function () {
        var self = this;
        $('form#scribble-broadcast').submit(function (event) {
            event.preventDefault();
            socket.emit('scribble', {
                data: $('#scribble_data').val(),
                scribblee_name: window.profile_name,
                scribblee_id: window.profile_id
            });
            $('#scribble_data').val('');
        });
        $('#peer-review').click(function (event) {
            event.preventDefault();
            socket.emit('get-all-reports');
            // socket.emit('get-users');
            // socket.emit('get-report', { 'username': '4' });
        });
        $('#review-form').submit(function (event) {
            event.preventDefault();
            
        });
        return self;
    };
    $(document).ready(function () {
        var socket_url, pr;
        socket_url = window.location.protocol + '//' + document.domain + ':' + location.port + '/socket.io/';
        window.socket = io.connect(socket_url);
        pr = new PeerReview();
        pr.intake().exhaust();
    });
})(jQuery);
