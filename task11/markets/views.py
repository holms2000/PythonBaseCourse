# markets/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import ReviewForm
from api.models import Market  # Импортируем модель Рынка
from api.models import Review  # Импортируем модель Отзыва
from .forms import SearchMarketsForm

def main_view(request):
    """
    Главная страница приложения.
    Здесь будет отображаться интерфейс с вкладками.
    """
    # Здесь может быть любая логика для главной страницы.
    # Сейчас мы просто рендерим шаблон.
    return render(request, 'markets/main.html')

@login_required
def submit_review(request, fmid):
    """
    Обработчик формы для добавления и редактирования отзыва.
    Работает через POST и GET.
    """
    # Получаем объект рынка по FMID. Если его нет, вернем страницу 404.
    market = get_object_or_404(Market, FMID=fmid)
    
    # Проверяем, оставлял ли текущий пользователь отзыв на этот рынок
    has_reviewed = Review.objects.filter(fmid=market, author=request.user).exists()
    
    # Обработка отправленной формы (метод POST)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            # Получаем чистые данные из формы
            rating = form.cleaned_data['rating']
            comment = form.cleaned_data['comment']
            
            if has_reviewed:
                # Если отзыв уже есть, обновляем его
                review = Review.objects.get(fmid=market, author=request.user)
                review.rating = rating
                review.comment = comment
                review.save()
                messages.success(request, "Ваш отзыв успешно обновлен!")
            else:
                # Если отзыва нет, создаем новый
                Review.objects.create(
                    fmid=market,
                    author=request.user,
                    rating=rating,
                    comment=comment
                )
                messages.success(request, "Ваш отзыв принят!")
            
            # Перенаправляем на страницу деталей рынка после отправки
            return redirect('market_details', fmid=fmid)
    else:
        # Если это GET-запрос (пользователь только открыл страницу)
        if has_reviewed:
            # Если отзыв уже есть, подставляем его данные в форму для редактирования
            existing_review = Review.objects.get(fmid=market, author=request.user)
            form = ReviewForm(initial={
                'rating': existing_review.rating,
                'comment': existing_review.comment
            })
        else:
            # Если отзыва нет, показываем пустую форму
            form = ReviewForm()

    # Получаем все отзывы для этого рынка, чтобы отобразить их на странице
    reviews = Review.objects.filter(fmid=market)

    # Передаем в шаблон все необходимые данные одним словарем (контекстом)
    return render(request, 'markets/details.html', {
        'market': market,
        'form_review': form,
        'has_reviewed': has_reviewed,
        'reviews': reviews,
    })
def view_all_markets(request):
    """
    Отображает страницу со списком всех рынков.
    """
    # Используем Django ORM, чтобы получить все объекты Market из базы данных
    markets = Market.objects.all()

    # Передаем список рынков в шаблон для отображения
    return render(request, 'markets/view_all.html', {
        'markets': markets
    })

def search_markets(request):
    """
    Обработчик простого поиска по городу и штату.
    """
    # Создаем форму и передаем в неё GET-параметры (данные из строки поиска)
    form = SearchMarketsForm(request.GET or None)
    markets = [] # Изначально список рынков пуст

    if form.is_valid():
        # Если форма заполнена корректно, получаем данные
        city = form.cleaned_data.get('city')
        state = form.cleaned_data.get('state')
        
        # Собираем параметры для поиска
        params = {}
        if city:
            params['city'] = city
        if state:
            params['state'] = state

        # Используем ORM для поиска рынков по заданным критериям
        markets = Market.objects.filter(**params)

    # Передаем форму и результаты поиска в шаблон
    return render(request, 'markets/search_results.html', {
        'form_search': form,
        'markets': markets,
    })
def market_details(request, fmid):
    """
    Отображает страницу с деталями конкретного рынка и отзывами.
    """
    # Получаем объект рынка по FMID. Если его нет, вернем страницу 404.
    market = get_object_or_404(Market, FMID=fmid)
    
    # Проверяем, оставлял ли текущий пользователь отзыв (для отображения кнопки "Редактировать")
    has_reviewed = False
    if request.user.is_authenticated:
        has_reviewed = Review.objects.filter(fmid=market, author=request.user).exists()

    # Получаем все отзывы для этого рынка
    reviews = Review.objects.filter(fmid=market)

    # Передаем данные в шаблон
    return render(request, 'markets/details.html', {
        'market': market,
        'reviews': reviews,
        'has_reviewed': has_reviewed,
        # Обратите внимание: здесь мы НЕ передаем форму, 
        # так как форма для отзыва обрабатывается в submit_review
    })

def find_market_for_review(request):
    """
    Поиск рынка по названию или FMID для последующей возможности оставить отзыв.
    Работает с базой данных напрямую через Django ORM.
    """
    # Инициализируем переменные для передачи в шаблон
    markets = []
    search_term = ''
    error_message = ''
    search_mode = 'name' # По умолчанию поиск по названию

    if request.method == 'POST':
        search_term = request.POST.get('search_market', '').strip()
        search_mode = request.POST.get('search_mode', 'name')

        if search_term:
            try:
                if search_mode == 'fmid':
                    # 1. ПОИСК ПО FMID (ТОЧНОЕ СОВПАДЕНИЕ)
                    # Используем filter, так как get() вызовет ошибку, если рынок не найден.
                    # Мы хотим получить список (даже если он из одного элемента).
                    markets = Market.objects.filter(FMID=search_term)

                    # Если по ID ничего не нашли, проверяем, не является ли строка числом.
                    # Если нет - выводим сообщение.
                    if not markets.exists():
                        try:
                            int(search_term)
                            error_message = f'Рынок с FMID {search_term} не найден.'
                        except ValueError:
                            error_message = f'Рынок с FMID {search_term} не найден. Проверьте правильность ввода.'

                else:
                    # 2. ПОИСК ПО НАЗВАНИЮ (ЧАСТИЧНОЕ СОВПАДЕНИЕ)
                    # ILIKE в SQL это то же самое, что icontains в Django ORM (без учета регистра)
                    markets = Market.objects.filter(MarketName__icontains=search_term)

                    if not markets.exists():
                        error_message = f'Рынков с названием "{search_term}" не найдено.'

            except Exception as e:
                # Обработка непредвиденных ошибок базы данных
                error_message = f'Произошла ошибка при поиске: {str(e)}'
        else:
            error_message = 'Введите название рынка или FMID для поиска.'

    # Передаем результаты в шаблон
    return render(request, 'markets/find_market_results.html', {
        'markets': markets,
        'search_term': search_term,
        'error_message': error_message,
        'search_mode': search_mode,
    })
