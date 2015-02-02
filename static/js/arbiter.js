(function ($) {
    function Arbiter() {
        var self = this;
    }
    Arbiter.prototype.intake = function () {
        var self = this;
        socket.on('all-reports', function (res) {
            if (res && res.reports) {
                var reports = "<table>";
                for (var i = 0, len = res.reports.length; i < len; ++i) {
                    reports += "<tr>";
                    // reports += "<td><a href='#' onclick=\"socket.emit('get-report', {'username': '" + res.reports[i].username + "', 'report-id': '" + res.reports[i].report_id + "'})\">" + res.reports[i].report_id + "</a></td>";
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
            var mean_rating = (res.mean_rating) ? res.mean_rating.toString() + " (" + res.num_ratings.toString() + " ratings)" : "unrated";
            if (res && res.report_id) {
                var report_display = "<ul class='plain'>";
                report_display += "<li>Creator: <b>" + res.username + "</b></li>";
                // report_display += "<li>Report ID: " + res.report_id + "</li>";
                report_display += "<li>" + res.timestamp + "</li>";
                report_display += "<li>Average rating: <a href='#' onclick=\"$('#review-details').slideToggle()\">" + mean_rating + "</a><div id='review-details' style='display:none; background-color: #fff; border: 1px solid #ccc; margin: 5px; padding: 10px;' class='plain'></div></li>";
                report_display += "<li class='report-body'>" + res.report.replace(/(?:\r\n|\r|\n)/g, '<br />'); + "</li>";
                // report_display += "<li class='report-body'>" + res.report + "</li>";
                report_display += "</ul>";
                $('#review-display').html(report_display);
                $('#review-details').append($('<h5 />').text("Review comments:"));
                $('#review-details').append($('<ol id="review-details-list" />'));
                for (var i = 0, len = res.comments.length; i < len; ++i) {
                    $('#review-details-list').append($('<li />').text(res.comments[i].replace(/(?:\r\n|\r|\n)/g)));
                    // $('#review-details-list').append($('<li />').html(res.comments[i]));
                }
                $('#review-entry').show();
                $('#report-id').val(res.report_id.toString());
                $('#reviewee').val(res.username);
            }
        });
        socket.on('review-submitted', function (res) {
            if (res && res.review_id) {
                $('#review-display').html(
                    "<center><h4>Your review has been submitted successfully.  Thank you!</h4></center>"
                );
            }
        });
        return self;
    };
    Arbiter.prototype.exhaust = function () {
        var self = this;
        $('#peer-review').click(function (event) {
            event.preventDefault();
            $('#review-display').empty();
            $('#report-block').hide();
            $('#submitted').hide();
            socket.emit('get-all-reports');
        });
        $('form#review-form').submit(function (event) {
            event.preventDefault();
            var reviewee = $('#reviewee').val();
            if (reviewee == window.username) {
                alert("You cannot submit a review for yourself!");
            } else {
                var data = {
                    rating: $('#rating').val(),
                    reviewee: reviewee,
                    comments: $('#comment-text').val(),
                    report_id: $('#report-id').val()
                }
                socket.emit('submit-review', data);
                $('#review-display').empty();
                $('#report-id').val("");
                $('#reviewee').val("");
                $('#rating').val("");
                $('#comment-text').val("");
                $('#review-entry').hide();
            }
        });
        return self;
    };
    $(document).ready(function () {
        var socket_url, arbiter;
        socket_url = window.location.protocol + '//' + document.domain + ':' + location.port + '/socket.io/';
        window.socket = io.connect(socket_url);
        arbiter = new Arbiter();
        arbiter.intake().exhaust();
    });
})(jQuery);
