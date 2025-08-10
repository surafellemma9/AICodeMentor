import json

from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse


def ping(_request):
    return HttpResponse("chatbot pong")

def index(_request):
    return HttpResponse("chatbot index ok")

def chat_api(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")
    data = json.loads((request.body or b"{}").decode())
    return JsonResponse({"reply": f"echo: {data.get('message', '')}"})
