from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from explore.models import Game, Rating, FollowedGame, Comment, CommentReaction
from django.utils import timezone

class GameViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='alex', password='testpass')
        self.game = Game.objects.create(
            source_id='LIS1-1',
            title='Hearthstone',
            description='Card game',
            platform='PC',
            genre='Strategy',
            thumbnail='http://example.com/img.png',
            url='http://example.com',
        )

    def test_index_view(self):
        response = self.client.get(reverse('explore'))
        self.assertEqual(response.status_code, 200)

    def test_index_search_query(self):
        response = self.client.get(reverse('explore') + '?q=Hearth')
        self.assertContains(response, 'Hearthstone')

    def test_follow_game(self):
        self.client.login(username='alex', password='testpass')
        response = self.client.get(reverse('follow_tool', args=[self.game.source_id, 'true']))
        self.assertRedirects(response, reverse('explore'))
        self.assertTrue(FollowedGame.objects.filter(user=self.user, game=self.game).exists())

    def test_vote_game(self):
        self.client.login(username='alex', password='testpass')
        response = self.client.post(reverse('rate', args=[self.game.source_id]), {'score': '4'})
        self.assertRedirects(response, reverse('details', args=[self.game.source_id]))
        rating = Rating.objects.get(user=self.user, game=self.game)
        self.assertEqual(rating.score, 4)

    def test_post_comment(self):
        self.client.login(username='alex', password='testpass')
        response = self.client.post(reverse('details', args=[self.game.source_id]), {'content': 'Muy buen juego'})
        self.assertRedirects(response, reverse('details', args=[self.game.source_id]))
        self.assertEqual(Comment.objects.filter(game=self.game).count(), 1)

    def test_game_json(self):
        response = self.client.get(reverse('game_json', args=[self.game.source_id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Hearthstone')

    def test_preferences_update(self):
        self.client.login(username='alex', password='testpass')
        response = self.client.post(reverse('preferences'), {
            'alias': 'alexito',
            'font': 'mono',
            'size': 'lg'
        })
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'alexito')

    def test_comment_reaction(self):
        comment = Comment.objects.create(user=self.user, game=self.game, text='Top juego', created_at=timezone.now())
        self.client.login(username='alex', password='testpass')
        response = self.client.post(reverse('react_comment', args=[comment.id]), {'reaction': 'like'})
        self.assertRedirects(response, reverse('explore'))
        self.assertTrue(CommentReaction.objects.filter(user=self.user, comment=comment, is_like=True).exists())
