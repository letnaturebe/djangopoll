from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.db.models import QuerySet, Prefetch


class Image(models.Model):
    image_url = models.CharField(max_length=128)


class User(AbstractUser):
    objects = UserManager()
    image = models.OneToOneField('Image', related_name='image', blank=True, null=True, on_delete=models.CASCADE)


class PollQuestion(models.Model):
    poll = models.ForeignKey(
        'Poll',
        verbose_name="투표ID",
        related_name='questions',
        on_delete=models.CASCADE)
    content = models.CharField(max_length=512)
    ordering = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f'[{self.id}]{self.content}'


class PollVote(models.Model):
    poll = models.ForeignKey(
        'Poll', verbose_name="투표ID", related_name='poll_votes', on_delete=models.CASCADE)
    question = models.ForeignKey(
        'PollQuestion', verbose_name="질문", related_name='question_votes', on_delete=models.CASCADE)
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='my_votes', verbose_name="투표자")

    def __str__(self):
        return f'투표자[{self.owner.first_name}]: {self.question}'


class Poll(models.Model):
    class PollManager(models.Manager):
        def get_queryset(self) -> QuerySet:
            queryset: QuerySet['Poll'] = (
                super().get_queryset()
                .prefetch_related(
                    Prefetch('questions', queryset=PollQuestion.objects.prefetch_related(
                        Prefetch('question_votes', queryset=PollVote.objects.select_related('owner__image')))))
                .select_related('owner__image'))
            return queryset

    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    head = models.CharField(max_length=50)
    message = models.CharField(max_length=128)
    end_time = models.DateTimeField(null=True, blank=True)
    is_anonymous_vote = models.BooleanField(verbose_name="익명투표", default=False)
    is_multiple_vote = models.BooleanField(verbose_name="복수투표", default=False)

    objects = PollManager()
