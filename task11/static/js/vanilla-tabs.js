javascript// static/js/vanilla-tabs.js

document.addEventListener('DOMContentLoaded', function () {    // Находим все элементы вкладок и контента    const tabLinks = document.querySelectorAll('.tab-link');    const tabPanes = document.querySelectorAll('.tab-pane');

Копировать
// Функция для скрытия всех вкладок и деактивации всех ссылок
function hideAllTabs() {
    tabLinks.forEach(link => link.classList.remove('active'));
    tabPanes.forEach(pane => pane.classList.remove('active'));
}

// Добавляем обработчик клика на каждую ссылку вкладки
tabLinks.forEach(link => {
    link.addEventListener('click', function (e) {
        e.preventDefault(); // Предотвращаем переход по ссылке

        // Скрываем все и убираем активность
        hideAllTabs();

        // Получаем цель из атрибута data-tab-target
        const target = this.getAttribute('data-tab-target');
        
        // Показываем нужную вкладку и делаем ссылку активной
        this.classList.add('active');
        document.getElementById(target).classList.add('active');
    });
});
});

