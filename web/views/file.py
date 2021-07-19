import json
from django.shortcuts import render, HttpResponse
import requests
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from web.forms.file import FolderModelForm, FileModelForm
from django.forms import model_to_dict
from django.http import JsonResponse
from web import models
from Tool.Tencent_tool.cos import delete_file, delete_file_list, credential


def file(request, project_id):
    """文件列表实现&添加文件夹"""

    parent_object = None
    folder_id = request.GET.get('folder', "")
    # print(folder_id)
    if folder_id.isdecimal():
        parent_object = models.FileRepository.objects.filter(id=int(folder_id), file_type=2, project=request.tracer.project).first()

    if request.method == 'GET':
        breadcrumb_list = []
        parent = parent_object
        #生成导航栏列表
        while parent:
            #breadcrumb_list.insert(0, {"id": parent.id, 'name': parent.name}) 和下面的方法效果一样，后者更省事
            breadcrumb_list.insert(0, model_to_dict(parent, ['id', 'name']))
            parent = parent.parent

        queryset = models.FileRepository.objects.filter(project=request.tracer.project)
        if parent_object:
            file_object_list = queryset.filter(parent=parent_object).order_by('-file_type')
        else:
            file_object_list = queryset.filter(parent__isnull=True).order_by('-file_type')
        form = FolderModelForm(request, parent_object)
        """folder_object参数拥有定位当前在那个项目文件目录中"""
        context = {
            "form": form,
            'file_object_list': file_object_list,
            'breadcrumb_list': breadcrumb_list,
            'folder_object': parent_object
                   }
        # for i in file_object_list:
        #     print(i.name)
        #     print(i.file_type)
        #     print(i.file_size)
        return render(request, 'file.html', context)

    """添加文件夹&修改文件夹"""
    fid = request.POST.get('fid', '')
    # print(fid)
    if fid.isdecimal():
        edit_object = models.FileRepository.objects.filter(id=int(fid), file_type=2, project=request.tracer.project).first()
        """form中加instance参数修改数据库中的对象，也可以用两个modelForm来校验"""
        form = FolderModelForm(request, parent_object, data=request.POST, instance=edit_object)
    else:
        form = FolderModelForm(request, parent_object, data=request.POST)
    if form.is_valid():
        form.instance.project = request.tracer.project
        form.instance.file_type = 2
        form.instance.updata_user = request.tracer.user
        form.instance.parent = parent_object
        form.save()
        return JsonResponse({'status': True})
    return JsonResponse({'status': False, 'error': form.errors})


def file_delete(request, project_id):
    fid = request.GET.get('fid')
    delete_object = models.FileRepository.objects.filter(id=fid, project=request.tracer.project).first()
    if delete_object.file_type == 1:
        """删除数据库文件记录，删除COS文件，更新项目使用空间"""
        """删除COS文件"""
        delete_file(request.tracer.project.bucket, request.tracer.project.region, delete_object.key)
        """更新项目使用空间"""
        request.tracer.project.use_space -= delete_object.file_size
        request.tracer.project.save()
        """删除数据记录"""
        delete_object.delete()
        return JsonResponse({'status': True})

    """删除数据库文件夹记录，删除文件夹中的子文件夹以及子文件，删除COS文件，更新项目使用空间"""
    total_size = 0
    file_list = []
    folder_list = [delete_object, ]
    for folder in folder_list:
        child_list = models.FileRepository.objects.filter(project=request.tracer.project, parent=folder).order_by('-file_type')
        for child in child_list:
            if child.file_type == 2:
                folder_list.append(child)
            else:
                file_list.append({'Key': child.key})
                total_size += child.file_size
    if file_list:
        """调用COS量删除函数将COS里的文件进行删除"""
        delete_file_list(request.tracer.project.bucket, request.tracer.project.bucket.region, file_list)
    if total_size:
        request.tracer.project.use_space -= total_size
        request.tracer.project.save()
    print(folder_list)
    delete_object.delete()
    return JsonResponse({'status': True})


@csrf_exempt
def cos_credential(request, project_id):
    file_dict = json.loads(request.body.decode("utf-8"))
    per_file_limit = request.tracer.price_policy.per_file_size * 1024 * 1024
    per_total_limit = request.tracer.price_policy.project_space * 1024 * 1024 * 1024
    total_size = 0
    # print(file_dict)
    for itme in file_dict:
        if itme['size'] > per_file_limit:
            mrg = "{}文件超出单文件最大上传限制（{}M），请升级套餐增加单文件上传限制！".format(itme['name'], request.tracer.price_policy.per_file_size)
            # print(mrg)
            return JsonResponse({'status': False, "error": mrg})
        total_size += itme['size']

    if request.tracer.project.use_space + total_size > per_total_limit:
        mrg = "{}项目空间已不足，无法上传文件，请升级套餐增加项目空间！".format(request.tracer.project.name)
        # print(mrg)
        return JsonResponse({'status': False, 'error': mrg})

    data_dict = credential(request.tracer.project.bucket, request.tracer.project.region)
    # print(data_dict)
    return JsonResponse({'status': True, 'data': data_dict})


@csrf_exempt
def file_post(request, project_id):
    """前端上传文件返回数据存储至数据库"""
    """
    'name': fileName,
    'file_size': fileSize,
    'key': key,
    'parent': CURRENT_FOLDER_ID,
    'etag': data.ETag,
    'file_path': data.Location,
    """
    #print("aaa")
    form = FileModelForm(request, data=request.POST)
    if form.is_valid():
        """校验完毕将数据写入数据库"""
        #print("开始写入数据库")
        data_dict = form.cleaned_data
        data_dict.pop('etag')
        data_dict.update({'project': request.tracer.project, 'file_type': 1, 'updata_user': request.tracer.user})
        instance = models.FileRepository.objects.create(**data_dict)

        # 项目已使用空间更新
        request.tracer.project.use_space += data_dict['file_size']
        #print(request.tracer.project.use_space)
        request.tracer.project.save()


        result = {
            'id': instance.id,
            'name': instance.name,
            'file_size': instance.file_size,
            'username': instance.updata_user.username,
            'datetime': instance.updata_datatime.strftime("%Y年%m月%d日 %H:%M"),
            'download_url': reverse('file_download', kwargs={"project_id": project_id, "file_id": instance.id})
        }
        return JsonResponse({'status': True, 'data': result})
    print(form.errors)
    return JsonResponse({
        'status': False,
        'error': form.errors,
    })


def file_download(request, project_id, file_id):
    """下载文件"""
    file_object = models.FileRepository.objects.filter(id=file_id, project_id=project_id).first()
    #requests获取网络上的数据
    res = requests.get(file_object.file_path)
    data = res.content
    #设置响应头
    response = HttpResponse(data)
    response['Content-Disposition'] = "attachment; filename={}".format(file_object.name)
    return response