"""bug_web URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from web.views import account, home, project, manage, wiki, file, setting, issues

urlpatterns = [
    # 首页、注册、短信验证
    url(r'^index/$', home.index, name='index'),
    url(r'^register/$', account.register, name='register'),
    url(r'^send/sms/$', account.send_sms, name='send_sms'),
    # 邮箱手机号密码登陆、
    url(r'^login/$', account.login, name='login'),
    url(r'^image/code/$', account.image_code, name='image_code'),
    # 手机验证码登陆
    url(r'^login/sms/$', account.login_sms, name='login_sms'),
    # 测试页
    url(r'^test/$', account.index, name='test'),

    # 退出登陆
    url(r'^logout/$', account.logout, name='logout'),
    # 项目列表
    url(r'^project/list/$', project.project_list, name='project_list'),
    # 星标取消星标操作URL
    url(r'^project/star/(?P<project_type>\w+)/(?P<project_id>\d+)/$', project.project_star, name='project_star'),
    url(r'^project/unstar/(?P<project_type>\w+)/(?P<project_id>\d+)/$', project.project_unstar, name='project_unstar'),

    # 项目管理详情页
    url(r'^manage/(?P<project_id>\d+)/', include([
        url(r'^dashboard/$', manage.dashboard, name='dashboard'),

        url(r'^statistice/$', manage.statistice, name='statistice'),

        # wiki管理详情页
        url(r'^wiki/$', wiki.wiki, name='wiki'),
        url(r'^wiki/add/$', wiki.wiki_add, name='wiki_add'),
        url(r'^wike/catalog/$', wiki.wiki_catalog, name='wiki_catalog'),
        url(r'^wike/delete/(?P<wiki_id>\d+)/$', wiki.wiki_delete, name='wiki_delete'),
        url(r'^wike/edit/(?P<wiki_id>\d+)/$', wiki.wiki_edit, name='wiki_edit'),
        url(r'^wike/upload/$', wiki.wiki_upload, name='wiki_upload'),

        # 文件管理详情页
        url(r'^file/$', file.file, name='file'),
        url(r'^file/delete/$', file.file_delete, name='file_delete'),
        url(r'^cos/credential/$', file.cos_credential, name='cos_credential'),
        url(r'^file/post/$', file.file_post, name='file_post'),
        url(r'^file/download/(?P<file_id>\d+)/$', file.file_download, name='file_download'),

        # 设置管理页面
        url(r'^setting/$', setting.setting, name='setting'),
        url(r'^setting/delete/$', setting.delete, name='setting_delete'),
        url(r'^setting/addissuestype/$', setting.add_issues_type, name='setting_add_issues_type'),
        url(r'^setting/addissuesmodular/$', setting.add_issues_modular, name='setting_add_issues_modular'),
        # 任务管理页
        url(r'^issues/$', issues.issues, name='issues'),
        url(r'^issues/detail/(?P<issues_id>\d+)/$', issues.detail, name='detail'),
        url(r'^issues/record/(?P<issues_id>\d+)/$', issues.issues_record, name='issues_record'),
        url(r'^issues/change/(?P<issues_id>\d+)/$', issues.issues_change, name='issues_change'),
        url(r'^issues/invite/url/$', issues.invite_url, name='invite_url'),
    ], None, None)),
    url(r'^issues/invite/join/(?P<code>\w+)/$', issues.invite_join, name='invite_join'),
]
