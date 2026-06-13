document.addEventListener("click", function (event) {
    document.querySelectorAll(".menu-acciones").forEach(function (menu) {
        if (!menu.contains(event.target)) {
            menu.removeAttribute("open");
        }
    });
});