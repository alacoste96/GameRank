
from explore.models import Game, Comment, Rating

def global_metrics(request):
    total_games = Game.objects.count()
    total_comments = Comment.objects.count()
    
    user_votes = 0
    user_comments = 0
    if request.user.is_authenticated:
        user_votes = Rating.objects.filter(user=request.user).count()
        user_comments = Comment.objects.filter(user=request.user).count()

    return {
        'total_games': total_games,
        'total_comments': total_comments,
        'user_votes': user_votes,
        'user_comments': user_comments,
    }

