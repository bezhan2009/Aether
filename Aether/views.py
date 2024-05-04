from django.shortcuts import render, redirect
from Aether.models import *
from django.http import HttpResponse, JsonResponse
from django.views.generic import TemplateView


def ping(request):
    data = {'message': 'Servers is up and running'}
    return JsonResponse(data)
    # return HttpResponse("Server is up and running")
