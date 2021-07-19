from django.shortcuts import render


def dashboard(request, project_id):
    return render(request, 'dashboard.html')


def issues(request, project_id):
    return render(request, 'issues.html')


def statistice(request, project_id):
    return render(request, 'statistice.html')


def file(request, project_id):
    return render(request, 'file.html')


def wiki(request, project_id):
    return render(request, 'wiki.html')


def setting(request, project_id):
    return render(request, 'setting.html')