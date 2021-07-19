from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from web.forms.wiki import WikiModelForm
from web import models
from Tool.Tencent_tool import cos
from Tool.local_tool.encrypt import uid


def wiki(request, project_id):
    """wiki展示功能"""
    wiki_id = request.GET.get('wiki_id')
    if not wiki_id or not wiki_id.isdecimal():
        return render(request, 'wiki.html')
    wiki_object = models.Wiki.objects.filter(id=wiki_id, project_id=project_id).first()
    return render(request, 'wiki.html', {'wiki_object': wiki_object})


def wiki_add(request, project_id):
    """wiki创建文章功能"""
    if request.method == 'GET':
        form = WikiModelForm(request)
        return render(request, 'wiki_form.html', {'form': form})
    form = WikiModelForm(request, data=request.POST)
    if form.is_valid():
        if form.instance.parent:
            form.instance.depth = form.instance.parent.depth + 1
        form.instance.project = request.tracer.project
        form.save()
        url = reverse('wiki', kwargs={'project_id': project_id})
        return redirect(url)
    return render(request, 'wiki_form.html', {'error': form.errors})


def wiki_catalog(request, project_id):
    """wiki 目录预览功能"""
    data = models.Wiki.objects.filter(project=project_id).values('id', 'title', 'parent_id').order_by('depth', 'id')
    #用models从数据库取出的数据是queryset类型，不能直接在JsonResponse函数中调用jsondump转化为json类型，所以需要将queryset类型的数据list一下
    return JsonResponse({'status': True, 'data': list(data)})


def wiki_delete(request, project_id, wiki_id):
    """wiki 删除功能"""
    models.Wiki.objects.filter(project_id=project_id, id=wiki_id).delete()
    url = reverse('wiki', kwargs={'project_id': project_id})
    return redirect(url)


def wiki_edit(request, project_id, wiki_id):
    """
    wiki 编辑文章功能
    1、获取到之前创建的内容
    2、如果是GET请求就展示之前的内容
    3、如果是POST请求就进入form验证
    4、验证后拼接URL进入预览文章页面
    """

    wiki_object = models.Wiki.objects.filter(project_id=project_id, id=wiki_id).first()
    if not wiki_object:
        url = reverse('wiki', kwargs={'project_id': project_id})
        return redirect(url)

    if request.method == 'GET':
        form = WikiModelForm(request, instance=wiki_object)
        return render(request, 'wiki_form.html', {'form': form})

    form = WikiModelForm(request, data=request.POST, instance=wiki_object)
    if form.is_valid():
        if form.instance.parent:
            form.instance.depth = form.instance.parent.depth + 1
        form.save()
        url = reverse('wiki', kwargs={'project_id': project_id})
        preview_url = "{0}?wiki_id={1}".format(url, wiki_id)
        return redirect(preview_url)
    return render(request, 'wiki_form.html', {'error': form.errors})


@csrf_exempt         #免除前端POST请求CSRF_torken
def wiki_upload(request, project_id):
    result = {
        'success': 0,
        'message': None,
        'url': None,
    }

    image_object = request.FILES.get("editormd-image-file")
    if not image_object:
        result['message'] = '文件不存在'
        return JsonResponse(result)
    ext = image_object.name.rsplit(".")[-1]
    key = "{}-{}".format(uid(request.tracer.user.phone), ext)

    image_url = cos.upload_file(
        request.tracer.project.bucket,
        request.tracer.project.region,
        image_object,
        key
    )
    result['success'] = 1
    result['url'] = image_url
    return JsonResponse(result)

