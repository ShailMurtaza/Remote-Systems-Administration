function check_del(url) {
    if (confirm('Are you sure?')) {
        window.location.href = url;
    }
}