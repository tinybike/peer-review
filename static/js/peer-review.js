(function ($) {
    function PeerReview() {
        var self = this;
    }
    PeerReview.prototype.intake = function () {
        var self = this;
        socket.on('users', function (res) {
            for (var i = 0, len = res.users.length; i < len; ++i) {
                console.log(res.users[i]);
            }
        });
        socket.on('report', function (res) { });
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
            socket.emit('get-users');
            // socket.emit('get-report', { 'username': '4' });
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
