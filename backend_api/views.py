from django.shortcuts import render
from rest_framework.views import APIView
from .models import Youtube
from .serialazer import YoutubeSerializer
from rest_framework.response import Response


# Create your views here.


class YoutubeView(APIView):
    def get(self, request):
        output = [{'title': item.title, 'channel': item.channel} for item in Youtube.objects.all()]
        return Response(output)

    def post(self, request):
        serializer = YoutubeSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data)
