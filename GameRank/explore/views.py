from django.http import HttpResponse
from django.template import loader
from django.shortcuts import redirect, render
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Avg, Count, Value, Q
from django.db.models.functions import Coalesce
import urllib.request
import json
import xml.etree.ElementTree as ET
from django.core.paginator import Paginator
from .models import Game, FollowedGame, Comment, Rating, CommentReaction
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.template.loader import render_to_string

def gameJson(request, source_id):
    try:
        game = Game.objects.get(source_id=source_id)
    except Game.DoesNotExist:
        return render(request, "404.html")

    data = {
        "source_id": game.source_id,
        "title": game.title,
        "thumbnail": game.thumbnail,
        "genre": game.genre,
        "platform": game.platform,
        "developer": game.developer,
        "publisher": game.publisher,
        "release_date": game.release_date,
        "description": game.description,
        "url": game.url,
        "average_rating": game.averageRating(),
        "rating_count": game.ratingCount(),
        "comment_count": game.comments.count(),
    }

    return JsonResponse(data)

def createGame(game, prefix, isXML):
    if isXML:
        Game.objects.create(
            source_id = f"{prefix}{game.find('id').text}",
            title = game.find("title").text,
            description = game.find('short_description').text,
            platform = game.find('platform').text,
            genre = game.find('genre').text,
            thumbnail = game.ifind('thumbnail').text,
            url = game.find('game_url').text,
            developer = game.find('developer').text,
            publisher = game.find('publisher').text,
            release_date = game.find('release_date').text
        )
    else:
        Game.objects.create(
            source_id = f"{prefix}{game['id']}",
            title = game['title'],
            description = game['short_description'],
            platform = game['platform'],
            genre = game['genre'],
            thumbnail = game['thumbnail'],
            url = game['game_url'],
            developer = game.get('developer', ''),
            publisher = game.get('publisher', ''),
            release_date = game.get('release_date', None)
        )

def titleExists(title_aux):
    for title in Game.objects.values_list('title', flat=True):
        if title.lower() == title_aux.lower():
            return True
    return False

def updateGames():
    # ----------- Listado 1: XML -----------
    xml_url = "https://gitlab.eif.urjc.es/cursosweb/2024-2025/final-gamerank/raw/main/listado1.xml"
    try:
        with urllib.request.urlopen(xml_url) as response:
            xml_data = response.read().decode()
            root = ET.fromstring(xml_data)

            for game in root.findall("game"):
                title = game.find('title').text
                if not titleExists(title):
                    createGame(game, "LIS1-", True)
    except Exception as e:
        print("Error cargando el listado XML:", e)

    # ----------- Listado 2(Opcional): JSON API (freetogame) -----------
    json_url_2 = "https://www.freetogame.com/api/games"
    try:
        with urllib.request.urlopen(json_url_2) as response:
            data = json.loads(response.read().decode())
            for game in data:
                title = game['title']
                if not titleExists(title):
                    createGame(game, "LIS2-", False)
    except Exception as e:
        print("Error cargando listado JSON 2:", e)

    # ----------- Listado 3(Opcional): JSON API (mmobomb) -----------
    json_url_3 = "https://www.mmobomb.com/api1/games"
    try:
        with urllib.request.urlopen(json_url_3) as response:
            data = json.loads(response.read().decode())
            for game in data:
                title = game['title']
                if not titleExists(title):
                    createGame(game, "LIS3-", False)
    except Exception as e:
        print("Error cargando listado JSON 3:", e)


def index(request):
    updateGames()

    query = request.GET.get('q')
    games = Game.objects.all()
    if query:
        games = games.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(genre__icontains=query) |
            Q(platform__icontains=query)
        )

    games = games.annotate(
                avg_rating=Coalesce(Avg('ratings__score'), Value(0.0)),
                num_votes=Count('ratings')
            ).order_by('-avg_rating')
    followed = set()
    if request.user.is_authenticated:
        followed = set(
            FollowedGame.objects.filter(user=request.user).values_list('game__id', flat=True)
        )
    paginator = Paginator(games, 21)  # 21 juegos por página
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {
        "page_obj": page_obj,
        "followed": followed
    }

    if request.headers.get("HX-Request"):  # si es una petición HTMX
        return render(request, "_game_list.html", context)

    return render(request, "index.html", context)

def commentsPartial(request, source_id):
    try:
        game = Game.objects.get(source_id=source_id)
    except Game.DoesNotExist:
        return render(request, "404.html")
    comments = game.comments.order_by('-created_at')
    context = {
        'comments': comments,
        'game': game
    }
    return render(request, '_comments.html', context)

def followManager(request, source_id, action):
    if not request.user.is_authenticated:
        return redirect('login')

    if action not in ['true', 'false']:
        return render(request, "404.html")

    try:
        game = Game.objects.get(source_id=source_id)
    except Game.DoesNotExist:
        return render(request, "404.html")

    to_follow = (action == 'true')
    if to_follow:
        FollowedGame.objects.get_or_create(user=request.user, game=game)
    else:
        FollowedGame.objects.filter(user=request.user, game=game).delete()

    if request.headers.get("Hx-Request"):
        followed = FollowedGame.objects.filter(user=request.user, game=game).exists()
        html = render_to_string("_follow_button.html", {
            'game': game,
            'followed': followed
        }, request=request)
        return HttpResponse(html)

    return redirect(request.META.get('HTTP_REFERER', 'explore'))

def rate(request, source_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    if not request.user.is_authenticated:
        return redirect('login')

    try:
        game = Game.objects.get(source_id=source_id)
    except Game.DoesNotExist:
        return render(request, "404.html")

    try:
        score = int(request.POST.get('score'))
        if score < 0 or score > 5:
            raise ValueError("Puntuación inválida")

        rating, created = Rating.objects.update_or_create(
            user=request.user,
            game=game,
            defaults={'score': score}
        )
        messages.success(request, "¡Puntuación guardada correctamente!")
    except (ValueError, TypeError):
        messages.error(request, "Error al guardar la puntuación.")

    return redirect('details', source_id=source_id)

def userGamesTool(request, which):
    if not request.user.is_authenticated:
        return redirect('login')

    user = request.user

    if which == "voted":
        ratings = Rating.objects.filter(user=user).select_related('game')
        user_games = [r.game for r in ratings]
        page_title = "Juegos Votados"
    elif which == "followed":
        followed = FollowedGame.objects.filter(user=user).select_related('game')
        user_games = [r.game for r in followed]
        page_title = "Juegos Seguidos"
    else:
        return render(request, "404.html")

    # Anotamos stats de cada juego
    games_with_stats = Game.objects.filter(id__in=[g.id for g in user_games]).annotate(
        avg_rating=Coalesce(Avg('ratings__score'), Value(0.0)),
        num_votes=Count('ratings')
    ).order_by('-avg_rating')

    followed_ids = set(
        FollowedGame.objects.filter(user=user).values_list('game__id', flat=True)
    )

    context = {
        'games': games_with_stats,
        'followed': followed_ids,
        'title': page_title
    }

    return render(request, 'user_games.html', context)

def details(request, source_id):
    if not request.user.is_authenticated:
        return redirect('login')
    try:
        game = Game.objects.get(source_id=source_id)
    except Game.DoesNotExist:
        return render(request, "404.html")

    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            Comment.objects.create(
                user=request.user,
                game=game,
                text=content
            )
            return redirect('details', source_id=source_id)

    comments = Comment.objects.filter(game=game).order_by('-created_at')
    user_rating = Rating.objects.filter(game=game, user=request.user).first()
    is_following = FollowedGame.objects.filter(game=game, user=request.user).exists()
    
    context = {
        'game': game,
        'comments': comments,
        'user_rating': user_rating,
        'is_following': is_following,
    }
    return render(request, 'game_details.html', context)

def preferences(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.method == 'POST':
        alias = request.POST.get('alias', '').strip()
        font = request.POST.get('font')
        size = request.POST.get('size')

        if alias:
            request.user.username = alias
            request.user.save()
        request.session['font'] = font
        request.session['size'] = size
        messages.success(request, "Preferencias guardadas correctamente.")

    return render(request, 'preferences.html')

def profile(request):
    if not request.user.is_authenticated:
        return redirect('login')

    user = request.user

    num_ratings = Rating.objects.filter(user=user).count()
    avg_rating = Rating.objects.filter(user=user).aggregate(avg=Avg('score'))['avg'] or 0

    context = {
        'num_ratings': num_ratings,
        'avg_rating': round(avg_rating, 2),
    }
    return render(request, 'profile.html', context)

def help(request):
    return render(request, 'help.html')

def reactToComment(request, comment_id):
    if request.method != 'POST':
        return render(request, '405.html')
    try:
        comment = Comment.objects.get(id=comment_id)
    except Game.DoesNotExist:
        return render(request, "404.html")

    is_like = request.POST.get('reaction') == 'like'

    # Actualizar o crear la reacción
    reaction, created = CommentReaction.objects.update_or_create(
        user=request.user,
        comment=comment,
        defaults={'is_like': is_like}
    )

    return redirect(request.META.get('HTTP_REFERER', 'explore'))
