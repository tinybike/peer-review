(function ($) {
    function PeerReview() {
        var self = this;
    }
    PeerReview.prototype.intake = function () {
        var self = this;
        socket.on('all-reports', function (res) {
            if (res && res.reports) {
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
            }
        });
        socket.on('users', function (res) {
            if (res && res.users) {
                var userlist = "<ul class='plain'>";
                for (var i = 0, len = res.users.length; i < len; ++i) {
                    userlist += "<li><a href='#' onclick=\"socket.emit('get-report', {'username': '" + res.users[i] + ", 'report-id': '" + res.report_ids[i] + "'})\">" + res.users[i] + "</a></li>";
                }
                userlist += "</ul>";
                $('#review-display').html(userlist);
            }
        });
        socket.on('reports', function (res) {
            if (res && res.reports) {
                for (var i = 0, len = res.reports.length; i < len; ++i) {
                    console.log(res.reports[i]);
                    console.log(res.timestamps[i]);
                }
            }
        });
        socket.on('report', function (res) {
            if (res && res.report_id) {
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
                $('#reviewee').val(res.username);
            }
        });
        socket.on('review-submitted', function (res) {
            if (res && res.review_id) {
                $('#review-display').html("<center><h4>Your review has been submitted successfully.  Thank you!</h4></center>");
            }
        });
        return self;
    };
    PeerReview.prototype.exhaust = function () {
        var self = this;
        $('#peer-review').click(function (event) {
            event.preventDefault();
            socket.emit('get-all-reports');
            // socket.emit('get-users');
            // socket.emit('get-report', { 'username': '4' });
        });
        $('form#review-form').submit(function (event) {
            event.preventDefault();
            var data = {
                rating: $('#rating').val(),
                reviewee: $('#reviewee').val(),
                comments: $('#comment-text').val()
            }
            console.log(data);
            socket.emit('submit-review', data);
            // $('#review-display').empty();
            $('#review-entry').hide();
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
