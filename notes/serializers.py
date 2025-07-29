from rest_framework import serializers

from users.serializers import UserSerializer
from .models import Note, DefectImage, DefectStatement


class DefectImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = DefectImage
        fields = "__all__"


class NoteSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    defect_images = DefectImageSerializer(many=True, read_only=True)

    class Meta:
        model = Note
        fields = "__all__"
        extra_kwargs = {
            "note_type": {"choices": ["personal", "work", "defect", "statement"]}
        }


class DefectStatementSerializer(serializers.ModelSerializer):
    defects = NoteSerializer(many=True, read_only=True)

    class Meta:
        model = DefectStatement
        fields = "__all__"
