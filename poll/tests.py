import datetime

import factory
from dateutil.tz import UTC
from django.db import connection
from django.db.models import QuerySet
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from factory.fuzzy import FuzzyDateTime
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from poll.models import Poll, PollQuestion, PollVote, User
from poll.serializers import PollSerializer, PollListSerializer


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
        self.user.save()

        user2 = self.create_user()
        user2['username'] = 'user2'
        self.user2: User = User.objects.create(**user2)

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

    def test_poll(self):
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

    def test_poll_queryset(self):
        from django.test.client import RequestFactory
        rf = RequestFactory()
        rf.user = self.user

        self.create_poll()

        with CaptureQueriesContext(connection) as expected_num_queries:
            polls: QuerySet[Poll] = Poll.objects.all()
            serializer = PollListSerializer(polls, many=True)
            print(serializer.data)

        self.create_poll()
        # self.create_poll()
        # self.create_poll()
        # self.create_poll()
        # self.create_poll()
        # self.create_poll()

        with CaptureQueriesContext(connection) as checked_num_queries:
            polls: QuerySet[Poll] = Poll.objects.all()
            serializer = PollListSerializer(polls, many=True)
            print(serializer.data)

        self.assertEqual(len(expected_num_queries), len(checked_num_queries))
