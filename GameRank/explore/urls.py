from . import views
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LoginView

urlpatterns = [
    path('', views.index, name='explore'),
    path('help/', views.help, name='help'),
    path('preferences/', views.preferences, name='preferences'),
    path('profile/', views.profile, name='user_profile'),
    path('user_games/<str:which>', views.userGamesTool, name='user_games'),
    path('follow_tool/<str:source_id>/<str:action>', views.followManager, name='follow_tool'),
    path('game/<str:source_id>/json', views.gameJson, name='game_json'),
    path('details/<str:source_id>', views.details, name='details'),
    path('rate/<str:source_id>', views.rate, name='rate'),
    path('coments/<int:comment_id>/react/', views.reactToComment, name='react_comment'),
    path('coments/<str:source_id>', views.commentsPartial, name='comments_partial'),
]
