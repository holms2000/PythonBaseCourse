# api/views.py

import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from api.models import Market, Review, OperatingSchedule
# Используем стандартный метод Django для получения модели пользователя
from django.contrib.auth import get_user_model

# Эта переменная будет ссылаться на модель, указанную в settings.AUTH_USER_MODEL
User = get_user_model()

from django.db.models import Q

@csrf_exempt
def api_router(request):
    """
    Единая точка входа для всех API-запросов.
    Принимает POST с JSON: {"action": "...", "params": {...}}.
    Возвращает JSON-ответ.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Метод не поддерживается. Используйте POST.'})

    try:
        data = json.loads(request.body)
        action = data.get('action')
        params = data.get('params', {})

        if action == 'find_markets':
            result = handle_find_markets(params)
        elif action == 'find_market_by_name':
            result = handle_find_market_by_name(params)
        elif action == 'find_market_by_fmid':
            result = handle_find_market_by_fmid(params)
        elif action == 'get_market_details':
            result = handle_get_market_details(params)
        elif action == 'get_reviews_by_fmid':
            result = handle_get_reviews_by_fmid(params)
        elif action == 'add_review':
            result = handle_add_review(request, params)
        elif action == 'edit_review':
            result = handle_edit_review(request, params)
        elif action == 'remove_review':
            result = handle_remove_review(request, params)
        elif action == 'user_has_reviewed':
            result = handle_user_has_reviewed(params)
        elif action == 'check_user_exists':
            result = handle_check_user_exists(params)
        elif action == 'create_user':
            result = handle_create_user(params)
        elif action == 'verify_login':
            result = handle_verify_login(request, params)
        else:
            result = {'status': 'error', 'message': f'Действие "{action}" не поддерживается.'}

    except json.JSONDecodeError:
        result = {'status': 'error', 'message': 'Некорректный формат JSON.'}
    except Exception as e:
        result = {'status': 'error', 'message': f'Внутренняя ошибка сервера: {str(e)}'}

    return JsonResponse(result)


# --- ОБРАБОТЧИКИ ДЕЙСТВИЙ ---

def handle_find_markets(params):
    """Поиск рынков по различным критериям."""
    query = Market.objects.all()

    if city := params.get('city'):
        query = query.filter(address__city__icontains=city)
    if state := params.get('state'):
        query = query.filter(address__state__icontains=state)
    if zip_code := params.get('zip_code'):
        query = query.filter(address__zip_code=zip_code)

    # Сортировка по рейтингу
    if params.get('sort_by_rating'):
        order = params.get('sort_order', 'desc')
        query = query.order_by('-avg_rating' if order == 'desc' else 'avg_rating')

    markets = list(query.values(
        'FMID', 'market_name',
        'address__street', 'address__city', 'address__state', 'address__zip_code'
    ))
    return {'status': 'ok', 'data': markets}


def handle_find_market_by_name(params):
    """Поиск по части названия."""
    name_part = params.get('market_name_part', '')
    markets = list(Market.objects.filter(market_name__icontains=name_part).values(
        'FMID', 'market_name',
        'address__street', 'address__city', 'address__state', 'address__zip_code'
    ))
    return {'status': 'ok', 'data': markets}


def handle_find_market_by_fmid(params):
    """Поиск по точному FMID."""
    fmid = params.get('fmid')
    if not fmid:
        return {'status': 'error', 'message': 'Параметр FMID обязателен.'}
    
    try:
        market = Market.objects.get(FMID=fmid)
        data = {
            'FMID': market.FMID,
            'market_name': market.market_name,
            'address_street': market.address.street,
            'address_city': market.address.city,
            'address_state': market.address.state,
            'address_zip_code': market.address.zip_code,
            # Координаты
            'latitude': market.coordinates.latitude,
            'longitude': market.coordinates.longitude,
        }
        return {'status': 'ok', 'data': [data]}
    except Market.DoesNotExist:
        return {'status': 'ok', 'data': []}


def handle_get_market_details(params):
    """Сборка полной информации о рынке."""
    fmid = params.get('fmid')
    try:
        market = Market.objects.select_related(
            'address', 'coordinates', 'social_links',
            'payment_options', 'products'
        ).prefetch_related('schedule').get(FMID=fmid)
        
        data = {
            # Основная информация о рынке
            'market': [
                market.FMID,
                market.market_name,
                market.website, # Пример другого поля из модели Market
                market.update_date.strftime('%Y-%m-%d') if market.update_date else None, # Обработка даты
            ],
            
            # Адрес (из связанной модели Address)
            'address': [
                market.address.street,
                market.address.city,
                market.address.state,
                market.address.zip_code,
                market.address.country, # Пример поля
            ],
            
            # Координаты (из связанной модели Coordinates)
            'coords': [
                market.coordinates.latitude,
                market.coordinates.longitude,
            ],
            
            # Социальные сети (из связанной модели SocialLinks)
            'social': {
                "Facebook": market.social_links.facebook,
                "Twitter": market.social_links.twitter,
                "Instagram": market.social_links.instagram, # Добавлено для примера
                "YouTube": market.social_links.youtube,
                "Website": market.social_links.website_link,
            },
            
            # Способы оплаты (из связанной модели PaymentOptions)
            'payment': {
                "Кредитные карты": market.payment_options.credit_cards,
                "WIC": market.payment_options.wic,
                "WIC Cash": market.payment_options.wic_cash,
                "SFMNP": market.payment_options.sfmnp,
                "SNAP": market.payment_options.snap,
                "EBT": market.payment_options.ebt, # Добавлено для примера
            },
            
            # Продукты (из связанной модели Products)
            # Поля модели Products - это булевы значения (True/False)
            'products': [
                "Organic" if market.products.organic else "",
                "Baked Goods" if market.products.baked_goods else "",
                "Cheese" if market.products.cheese else "",
                "Crafts" if market.products.crafts else "",
                "Flowers" if market.products.flowers else "",
                "Eggs" if market.products.eggs else "",
                "Seafood" if market.products.seafood else "",
                "Herbs" if market.products.herbs else "",
                "Vegetables" if market.products.vegetables else "",
                "Honey" if market.products.honey else "",
                # ... и так далее для всех продуктов ...
                
                # Последний продукт из вашего списка
                "Wild Harvested" if market.products.wild_harvested else "",
            ],
            
            # График работы (из связанной модели OperatingSchedule через ManyToMany)
            # Фильтруем пустые значения времени/даты
            'schedule': [
                {
                    "Season Number": sched.season_number,
                    "Season Date": sched.season_date or "",
                    "Season Time": sched.season_time or "",
                    "Season End Date": sched.season_enddate or "",
                    "Season End Time": sched.season_endtime or "",
                    "Day of Week": sched.day_of_week or "",
                    "Time Open": sched.time_open or "",
                    "Time Close": sched.time_close or "",
                    "Season Long Description": sched.long_description or "",
                    "Season Start Year": sched.start_year or "",
                    "Season End Year": sched.end_year or "",
                    "Season Month": sched.month or "",
                    "Season Day": sched.day or "",
                    "Season Month End": sched.month_end or "",
                    "Season Day End": sched.day_end or "",
                    "Season Date Raw": sched.season_date_raw or "",
                    "Season Time Raw": sched.season_time_raw or "",
                    "Season End Date Raw": sched.season_enddate_raw or "",
                    "Season End Time Raw": sched.season_endtime_raw or "",
                 }
                 for sched in market.schedule.all() if any([
                     sched.season_date, sched.season_time, sched.day_of_week, sched.time_open
                 ])
             ],
        }
        
        return {'status': 'ok', 'data': data}
        
    except Market.DoesNotExist:
        return {'status': 'error', 'message': f'Рынок с FMID {fmid} не найден.'}


def handle_get_reviews_by_fmid(params):
    """Получение всех отзывов для рынка."""
    fmid = params.get('fmid')
    reviews = list(Review.objects.filter(fmid__FMID=fmid).values(
        'id', 'rating', 'comment',
        'author__first_name', 'author__last_name', 'author__username'
    ))
    
    # Формируем красивое имя автора или используем username
    for rev in reviews:
         fullname = f"{rev['author__first_name']} {rev['author__last_name']}".strip()
         rev['fullname'] = fullname if fullname else rev['author__username']
         # Удаляем ненужные поля автора из ответа
         del rev['author__first_name']
         del rev['author__last_name']
         del rev['author__username']
         
    return {'status': 'ok', 'data': reviews}


# --- Действия с отзывами ---
def _get_user_review(fmid, author_username):
    """Вспомогательная функция для получения отзыва пользователя."""
    try:
         return Review.objects.get(fmid__FMID=fmid, author__username=author_username)
    except Review.DoesNotExist:
         return None

def handle_add_review(request, params):
     if not request.user.is_authenticated:
         return {'status': 'error', 'message': 'Требуется авторизация.'}
     
     fmid_val = params.get('fmid')
     rating_val = params.get('rating')
     comment_val = params.get('comment')
     
     # Проверка на дубликат отзыва от пользователя
     if _get_user_review(fmid_val, request.user.username):
         return {'status': 'error', 'message': 'Вы уже оставляли отзыв на этот рынок.'}
     
     try:
         Review.objects.create(
             fmid_id=fmid_val,  # Используем fmid_id для прямой вставки ID (быстрее)
             author=request.user,
             rating=rating_val,
             comment=comment_val
         )
         return {'status': "ok", "message": "Отзыв добавлен."}
     except Exception as e:
         return {'status': "error", "message": f"Ошибка БД: {str(e)}"}


def handle_edit_review(request, params):
     if not request.user.is_authenticated:
         return {'status': 'error', 'message': 'Требуется авторизация.'}
     
     review = _get_user_review(params.get('fmid'), request.user.username)
     if not review:
         return {'status': 'error', 'message': 'Отзыв не найден или нет прав на редактирование.'}
     
     review.rating = params.get('new_rating')
     review.comment = params.get('new_comment')
     review.save()
     return {'status': "ok", "message": "Отзыв обновлён."}


def handle_remove_review(request, params):
     if not request.user.is_authenticated:
         return {'status': 'error', 'message': 'Требуется авторизация.'}
     
     review = _get_user_review(params.get('fmid'), request.user.username)
     if not review:
         return {'status': 'error', 'message': 'Отзыв не найден или нет прав на удаление.'}
     
     review.delete()
     return {'status': "ok", "message": "Отзыв удалён."}


# --- Действия с пользователями ---
def handle_check_user_exists(params):
     username = params.get('username')
     # ИСПРАВЛЕНО: Используем User вместо CustomUser
     exists = User.objects.filter(username=username).exists()
     return {'status': "ok", "exists": exists}


def handle_create_user(params):
     username = params.get('username')
     password = params.get('password')
     firstname = params.get('firstname')
     lastname = params.get('lastname')
     
     # ИСПРАВЛЕНО: Используем User вместо CustomUser
     if User.objects.filter(username=username).exists():
         return {'status': "error", "message": "Пользователь с таким именем уже существует."}
         
     User.objects.create_user(username, password=password, first_name=firstname, last_name=lastname)
     return {'status': "ok", "message": "Пользователь создан."}


def handle_verify_login(request, params):
     username = params.get('username')
     password = params.get('password')
     
     user = authenticate(username=username, password=password)
     
     if user is not None:
         login(request, user) # Создаем сессию
         return {
             'status': "ok",
             "authenticated": True,
             "fullname": f"{user.first_name} {user.last_name}"
         }
     else:
         return {
             'status': "ok",
             "authenticated": False,
             "message": "Неверное имя пользователя или пароль."
         }


def handle_user_has_reviewed(params):
     fmid_val = params.get('fmid')
     author_username = params.get('author')
     
     has_reviewed = Review.objects.filter(fmid__FMID=fmid_val, author__username=author_username).exists()
     return {'status': "ok", "has_reviewed": has_reviewed}