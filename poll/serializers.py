from rest_framework import serializers

from poll.models import Poll, PollQuestion, PollVote, User, Image


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    image = ImageSerializer()

    class Meta:
        model = User
        fields = ('id', 'first_name', 'username', 'image',)


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


class PollDetailSerializer(serializers.ModelSerializer):
    questions = PollQuestionSerializer(many=True)
    owner = UserSerializer(read_only=True, )

    class Meta:
        model = Poll
        fields = ['id', 'owner', 'head', 'message', 'questions', 'end_time',
                  'is_anonymous_vote','is_multiple_vote',]


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

