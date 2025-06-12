function openNav() {
  document.getElementById("mobile-menu").style.width = "100%";
}

function closeNav() {
  document.getElementById("mobile-menu").style.width = "0%";
}

// Este código se ejecuta cuando el DOM está cargado
document.addEventListener("DOMContentLoaded", function () {
  const menuItemsWithSubmenu = document.querySelectorAll(
    "#mobile-menu .overlay-content > li"
  );

  menuItemsWithSubmenu.forEach((item) => {
    const submenu = item.querySelector("ul");
    if (submenu) {
      item.addEventListener("click", function (e) {
        e.stopPropagation(); // Evita que se propague el clic
        // Cierra otros submenús si lo deseas (opcional)
        menuItemsWithSubmenu.forEach((i) => {
          if (i !== item) i.classList.remove("active");
        });

        // Alterna este submenú
        item.classList.toggle("active");
      });
    }
  });
});
