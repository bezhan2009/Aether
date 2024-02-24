from django.shortcuts import render, redirect
from Aether.models import *
from django.http import HttpResponse, JsonResponse
from django.views.generic import TemplateView


def ping(request):
    data = {'message': 'Server is up and running'}
    return JsonResponse(data)
    # return HttpResponse("Server is up and running")


"""
def get_tasks(request):
    for task in tasks:
        del task["_state"]
    return JsonResponse(tasks, safe=False)


def get_task_by_id(request, id):
    for task in tasks:
        if task["id"] == id:
            del task["_state"]
            return JsonResponse(task, safe=False)

    return JsonResponse({'message': 'нет задачи с таким ID'}, status=404)

"""
"""
from django.http import JsonResponse
from django.views import View
from .models import Task  # Подключите вашу модель задачи

class TaskView(View):
    def get(self, request, task_id=None):
        if task_id:
            # Получение деталей задачи по идентификатору
            task = Task.objects.get(id=task_id)
            task_data = {'id': task.id, 'name': task.name, 'description': task.description}
            return JsonResponse(task_data)
        else:
            # Получение списка всех задач
            tasks = Task.objects.all()
            tasks_data = [{'id': task.id, 'name': task.name} for task in tasks]
            return JsonResponse(tasks_data, safe=False)

    def post(self, request):
        # Создание новой задачи
        # Обработка данных из запроса и сохранение в базу данных
        return JsonResponse({'message': 'Task created successfully'})

    def put(self, request, task_id):
        # Обновление существующей задачи по идентификатору task_id
        # Обработка данных из запроса и обновление соответствующей задачи в базе данных
        return JsonResponse({'message': f'Task with ID {task_id} updated successfully'})

    def delete(self, request, task_id):
        # Удаление задачи по идентификатору task_id
        # Обработка удаления задачи из базы данных
        return JsonResponse({'message': f'Task with ID {task_id} deleted successfully'})

    def patch(self, request, task_id):
        # Обновление части существующей задачи по идентификатору task_id
        # Обработка данных из запроса и частичное обновление соответствующей задачи в базе данных
        return JsonResponse({'message': f'Task with ID {task_id} partially updated successfully'})

"""
