$(document).ready(function () {
    // Визначаємо висоту елементу <nav>
    var navHeight = $("nav").outerHeight();
    // Встановлюємо відступ для елементу .content
    $(".content").css("margin-top", navHeight + "px");
});
