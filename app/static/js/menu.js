const btn = document.getElementById('btnMenu');
const menu = document.getElementById('menuMobile');
const fondo = document.getElementById('fondoMenu');

function abrirMenu() {
    menu.classList.remove('hidden');
    fondo.classList.remove('hidden');
    document.body.classList.add('overflow-hidden');
}

function cerrarMenu() {
    menu.classList.add('hidden');
    fondo.classList.add('hidden');
    document.body.classList.remove('overflow-hidden');
}

if (btn && menu && fondo) {
    btn.addEventListener('click', abrirMenu);
    fondo.addEventListener('click', cerrarMenu);

    menu.querySelectorAll('a').forEach((enlace) => {
        enlace.addEventListener('click', cerrarMenu);
    });

    document.addEventListener('keydown', (evento) => {
        if (evento.key === 'Escape') {
            cerrarMenu();
        }
    });
}
