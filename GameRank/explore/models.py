from django.db import models
from django.contrib.auth.models import User

# ------------------------------
#        JUEGO BASE
# ------------------------------
class Game(models.Model):
    source_id = models.CharField(max_length=100, unique=True)  # e.g. LIS1-345
    title = models.CharField(max_length=255)
    thumbnail = models.URLField()
    genre = models.CharField(max_length=100)
    platform = models.CharField(max_length=100)
    developer = models.CharField(max_length=255, blank=True)
    publisher = models.CharField(max_length=255, blank=True)
    release_date = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    url = models.URLField(blank=True)

    def __str__(self):
        return self.title

    def averageRating(self):
        return self.ratings.aggregate(models.Avg('score'))['score__avg'] or 0

    def ratingCount(self):
        return self.ratings.count()


# ------------------------------
#         COMENTARIO
# ------------------------------
class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.game.title}"

    # el @property es un decorador de python que permite acceder a esos metodos de clase como si fuesen
    # atributos, por lo que se podrá acceder desde los templates de django más facilmente
    # como sus nombres indican, los dos metodos estos son para el tema de los likes en comentarios
    @property
    def likesCount(self):
        return self.reactions.filter(is_like=True).count()

    @property
    def dislikesCount(self):
        return self.reactions.filter(is_like=False).count()

# ------------------------------
#      PUNTUACIONES (0 a 5)
# ------------------------------
class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='ratings')
    score = models.IntegerField()

    class Meta:
        unique_together = ('user', 'game') # sólo permito 1 valoracion por juego

    def __str__(self):
        return f"{self.user.username} - {self.game.title}: {self.score}"


# ------------------------------
#        JUEGOS SEGUIDOS
# ------------------------------
class FollowedGame(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='followers')

    class Meta:
        unique_together = ('user', 'game') # sólo puedes seguir 1 vez el mismo juego

    def __str__(self):
        return f"{self.user.username} sigue {self.game.title}"

# ------------------------------
#        ME GUSTASSSSS
# ------------------------------
class CommentReaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='reactions')
    is_like = models.BooleanField()  # True = like, False = dislike

    class Meta:
        unique_together = ('user', 'comment')  # Solo una reacción por usuario por comentario

    def __str__(self):
        return f"{self.user.username} reaccionó {'👍' if self.is_like else '👎'} a comentario {self.comment.id}"


