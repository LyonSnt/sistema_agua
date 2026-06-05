document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.toast-message').forEach(function (toast) {
        setTimeout(function () {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';

            setTimeout(function () {
                toast.remove();
            }, 300);
        }, 5000);
    });
});