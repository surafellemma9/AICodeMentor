import json
import os

import requests
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import render


def ping(_request):
    return HttpResponse("chatbot pong")

def index(_request):
    # TEMP: prove the route works first
    return HttpResponse("chatbot index ok")

# keep your chat_api here; doesn’t run on page load if your JS only calls it on submit
