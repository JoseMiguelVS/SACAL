document.addEventListener('DOMContentLoaded', function() {
    const menuToggle = document.querySelector('.header');
    const navMenu = document.querySelector('.navs-links');

    menuToggle.addEventListener('click', function() {
        navMenu.classList.toggle('show');
    });
});
