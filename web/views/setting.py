from django.shortcuts import render, redirect
from web import models
from Tool.Tencent_tool.cos import delete_bucket


def setting(request, project_id):
    #设置管理详情页
    return render(request, 'setting.html')


def delete(request, project_id):
    """删除项目"""
    if request.method == 'GET':
        return render(request, 'setting_delete.html')

    project_name = request.POST.get('project_name')

    if not project_name or project_name != request.tracer.project.name:
        return render(request, 'setting_delete.html', {'error': "项目名错误"})

    if request.tracer.user != request.tracer.project.creator:
        return render(request, 'setting_delete.html', {'error': "您不是项目创建者，无法删除项目"})

    #删除桶
    #1、删除桶中的文件
    #2、删除桶中的碎片文件
    #3、删除桶
    delete_bucket(request.tracer.project.bucket, request.tracer.project.region)
    models.Project.objects.filter(id=project_id).delete()
    #删除数据库项目记录

    return redirect('project_list')


def add_issues_type(request, project_id):
    if request.method == "GET":
        return render(request, 'setting_addissuestype.html')
    issues_type_name = request.POST.get('issues_type_name')
    if not issues_type_name:
        return render(request, 'setting_addissuestype.html', {'error': "此字段为必填项"})
    if len(issues_type_name) > 64:
        return render(request, 'setting_addissuestype.html', {'error': "任务类型名字太长了"})

    try:
        models.IssuesType.objects.create(project=request.tracer.project, title=issues_type_name)
    except Exception as e:
        return render(request, 'setting_addissuestype.html', {'error': "未添加成功"})
    return render(request, 'setting_addissuestype.html', {'error': "添加成功"})


def add_issues_modular(request, project_id):
    if request.method == "GET":
        return render(request, 'setting_addissuesmodular.html')

    issues_modular_name = request.POST.get('issues_modular_name')
    if not issues_modular_name:
        return render(request, 'setting_addissuesmodular.html', {'error': "此字段为必填项"})
    if len(issues_modular_name) > 64:
        return render(request, 'setting_addissuesmodular.html', {'error': "模块名称太长了"})

    try:
        models.Module.objects.create(project=request.tracer.project, title=issues_modular_name)
    except Exception as e:
        return render(request, 'setting_addissuesmodular.html', {'error': "未添加成功"})
    return render(request, 'setting_addissuesmodular.html', {'error': "添加成功"})