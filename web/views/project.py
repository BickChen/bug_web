from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from web.forms.project import ProjectModelForm
from web import models
from Tool.Tencent_tool import cos
import time


def project_list(request):
    # print(request.tracer.user)
    # print(request.tracer.price_policy)
    if request.method == 'GET':
        project_dict = {'star': [], 'my': [], 'join': []}

        my_project = models.Project.objects.filter(creator=request.tracer.user)
        for row in my_project:
            if row.star:
                project_dict['star'].append({'value': row, 'type': 'my'})
            else:
                project_dict['my'].append(row)

        join_project_list = models.ProjectUser.objects.filter(user=request.tracer.user)
        for item in join_project_list:
            if item.star:
                project_dict['star'].append({'value': item.project, 'type': 'join'})
            else:
                project_dict['join'].append(item.project)

        form = ProjectModelForm(request)
        # print(project_dict)
        return render(request, 'project_list.html', {'form': form, 'project_dict': project_dict})

    # print(request.POST)
    form = ProjectModelForm(request, data=request.POST)
    if form.is_valid():
        # print("进入创建项目")
        name = form.cleaned_data['name']
        # 为项目创建COS桶
        bucket = "{}{}{}-1256457197".format(name, request.tracer.user.phone, str(int(time.time())))
        region = "ap-shanghai"
        cos.create_bucket(bucket, region)

        form.instance.bucket = bucket
        form.instance.region = region
        form.instance.creator = request.tracer.user
        instance = form.save()

        #创建默认的问题类型：仅供测试使用，正式环境可使用默认值
        issues_type_object_list = []
        RPOJECT_INIT_LIST = ['任务', 'bug', '功能']
        for item in RPOJECT_INIT_LIST:
            issues_type_object_list.append(models.IssuesType(project=instance, title=item))
        models.IssuesType.objects.bulk_create(issues_type_object_list)

        return JsonResponse({'status': True})
    return JsonResponse({'status': False, 'error': form.errors})


def project_star(request, project_type, project_id):

    if project_type == 'my':
        models.Project.objects.filter(id=project_id, creator=request.tracer.user).update(star=True)
        return redirect('project_list')
    elif project_type == 'join':
        models.ProjectUser.objects.filter(project_id=project_id, user=request.tracer.user).update(star=True)
        return redirect('project_list')
    return HttpResponse('请求错误')


def project_unstar(request, project_type, project_id):

    if project_type == 'my':
        models.Project.objects.filter(id=project_id, creator=request.tracer.user).update(star=False)
        return redirect('project_list')
    elif project_type == 'join':
        models.ProjectUser.objects.filter(project_id=project_id, user=request.tracer.user).update(star=False)
        return redirect('project_list')
    return HttpResponse('请求错误')

