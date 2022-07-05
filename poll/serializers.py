from django.db.models import QuerySet
from rest_framework import serializers

from poll.models import Poll, PollQuestion, PollVote, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'first_name', 'username',)


class PollVoteSerializer(serializers.ModelSerializer):
    owner = UserSerializer()

    class Meta:
        model = PollVote
        exclude = ('poll', 'question',)


class PollQuestionSerializer(serializers.ModelSerializer):
    question_votes = PollVoteSerializer(many=True)

    class Meta:
        model = PollQuestion
        exclude = ('poll',)


class PollSerializer(serializers.ModelSerializer):
    questions = serializers.ListField(child=serializers.CharField(max_length=512, required=True), required=True)

    class Meta:
        model = Poll
        fields = ['head', 'message', 'end_time', 'is_anonymous_vote', 'is_multiple_vote', 'questions', ]

    def save(self, **kwargs) -> Poll:
        questions: list[str] = self.validated_data.pop('questions')
        poll: Poll = Poll.objects.create(**self.validated_data, **kwargs)
        for poll_question in questions:
            PollQuestion.objects.create(poll=poll, content=poll_question)
        return poll


class PollListSerializer(serializers.ModelSerializer):
    questions = PollQuestionSerializer(many=True)
    owner = UserSerializer(read_only=True, )
    # is_voted = serializers.SerializerMethodField(label='투표했니?', read_only=True)

    class Meta:
        model = Poll
        fields = ['id',
                  'owner',
                  'head',
                  'message',
                  'questions',
                  'end_time',
                  'is_anonymous_vote',
                  'is_multiple_vote',
                  # 'is_voted',
                  ]

    # def get_is_voted(self, obj: Poll) -> bool:
    #     user: User = self.context['request'].user
    #     if user.is_anonymous:
    #         return False
    #
    #     questions: QuerySet[PollQuestion] = obj.questions.all()
    #     for question in questions:
    #         poll_votes: QuerySet[PollVote] = question.question_votes.all()
    #         for poll_vote in poll_votes:
    #             if poll_vote.owner.id == user.id:
    #                 return True
    #     return False
