from django.contrib import admin
from .models import Game, Comment, Rating, FollowedGame

admin.site.register(Game)
admin.site.register(Comment)
admin.site.register(Rating)
admin.site.register(FollowedGame)

# Register your models here.
