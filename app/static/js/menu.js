const btn = document.getElementById('btnMenu');
const menu = document.getElementById('menuMobile');
const fondo = document.getElementById('fondoMenu');

function abrirMenu() {
    menu.classList.remove('hidden');
    fondo.classList.remove('hidden');
}

function cerrarMenu() {
    menu.classList.add('hidden');
    fondo.classList.add('hidden');
}

if (btn && menu && fondo) {
    btn.addEventListener('click', abrirMenu);
    fondo.addEventListener('click', cerrarMenu);

    menu.querySelectorAll('a').forEach((enlace) => {
        enlace.addEventListener('click', cerrarMenu);
    });
}