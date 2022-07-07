import datetime

import factory
from dateutil.tz import UTC
from django.db import connection
from django.db.models import QuerySet
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from factory.fuzzy import FuzzyDateTime

from poll.models import Poll, PollQuestion, PollVote, User, Image
from poll.serializers import PollDetailSerializer, PollSerializer


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    first_name = factory.Sequence(lambda n: "Agent %03d" % n)
    username = factory.Sequence(lambda n: "Agent %03d" % n)
    password = factory.Sequence(lambda n: "Agent %03d" % n)


class PollFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Poll

    head = factory.Sequence(lambda n: "Agent %d" % n)
    owner = factory.SubFactory(UserFactory)
    end_time = FuzzyDateTime(datetime.datetime(2023, 1, 1, tzinfo=UTC), datetime.datetime(2024, 1, 1, tzinfo=UTC))


class PollTest(TestCase):
    def setUp(self):
        self.user: User = User.objects.create(**self.create_user())
        self.user.image = Image.objects.create(image_url='www.image.com')
        self.user.save()

        user2 = self.create_user()
        user2['username'] = 'user2'
        self.user2: User = User.objects.create(**user2)
        self.user2.image = Image.objects.create(image_url='www.image.com')
        self.user2.save()

    def create_user(self) -> dict:
        return {
            "username": "leemoney93",
            "password": "mememememe",
            "first_name": "lee",
            "last_name": "money",
        }

    def create_poll(self):
        poll: Poll = PollFactory.create()
        q1 = PollQuestion.objects.create(poll=poll, content="yes")
        q2 = PollQuestion.objects.create(poll=poll, content="no")
        PollVote.objects.create(poll=poll, question=q1, owner=self.user)
        PollVote.objects.create(poll=poll, question=q2, owner=self.user2)

    def test_poll_create(self):
        end_time: datetime = datetime.datetime.now() + datetime.timedelta(hours=0, minutes=300, seconds=0)
        poll: Poll = Poll.objects.create(
            head='목요일 회식 가능??',
            owner=self.user,
            end_time=end_time)

        yes: PollQuestion = PollQuestion.objects.create(poll=poll, content="네")
        no: PollQuestion = PollQuestion.objects.create(poll=poll, content="아니오")

        PollVote.objects.create(poll=poll, question=yes, owner=self.user)
        PollVote.objects.create(poll=poll, question=no, owner=self.user2)

        self.assertEqual(poll.questions.all().count(), 2)
        self.assertEqual(poll.poll_votes.all().count(), 2)

        serializer = PollDetailSerializer(poll)
        self.assertEqual(len(serializer.data['questions']), 2)
        self.assertEqual(len(serializer.data['questions'][0]['question_votes']), 1)
        self.assertEqual(len(serializer.data['questions'][1]['question_votes']), 1)

    def test_poll_create2(self):
        for i in range(6):
            self.create_poll()

        with CaptureQueriesContext(connection) as num_queries:
            polls: QuerySet[Poll] = Poll.objects.all()
            serializer = PollDetailSerializer(polls, many=True)
            self.assertEqual(len(serializer.data), 6)

        print(len(num_queries.captured_queries))
        print(num_queries.captured_queries)

    def test_poll_n_plus1(self):
        self.create_poll()

        with CaptureQueriesContext(connection) as expected_num_queries:
            polls: QuerySet[Poll] = Poll.objects.all()
            serializer = PollDetailSerializer(polls, many=True)
            print(serializer.data)

        self.create_poll()
        self.create_poll()
        self.create_poll()
        self.create_poll()
        self.create_poll()

        with CaptureQueriesContext(connection) as checked_num_queries:
            polls: QuerySet[Poll] = Poll.objects.all()
            serializer = PollDetailSerializer(polls, many=True)
            print(serializer.data)

        self.assertEqual(len(expected_num_queries), len(checked_num_queries))

    def test_poll_create_serializer(self):
        end_time: datetime = datetime.datetime.now() + datetime.timedelta(hours=0, minutes=300, seconds=0)

        data = {
            'head': '목요일 회식 가능??',
            'message': '회식 장소 확인해주세요!',
            'is_anonymous_vote': False,
            'is_multiple_vote': False,
            'end_time': end_time,
            'questions': ['가능', '불가능']
        }

        serializer = PollSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        poll = serializer.save(owner=self.user)
        self.assertEqual(poll.questions.count(), 2)
        self.assertEqual(poll.head, data['head'])
