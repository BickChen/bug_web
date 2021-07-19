from django.utils.deprecation import MiddlewareMixin
from web import models
from django.shortcuts import redirect
from bug_web import settings
import datetime


class Tracer(object):

    def __init__(self):
        self.user = None
        self.price_policy = None
        self.project = None


class AuthMiddleware(MiddlewareMixin):

    def process_request(self, request):

        request.tracer = Tracer()

        user_id = request.session.get('user_id')
        user_object = models.UserInfo.objects.filter(id=user_id).first()

        request.tracer.user = user_object

        if request.path_info in settings.WHITE_REGEX_URL_LIST:
            return

        if not request.tracer.user:
            return redirect('login')

        _object = models.Transaction.objects.filter(user=user_id, status=2).order_by('-id').first()
        # print(_object)
        current_datatime = datetime.datetime.now()
        if _object.end_datetime and _object.end_datetime < current_datatime:
            _object = models.Transaction.objects.filter(user=user_id, status=2, price_policy__category=1).first()
        request.tracer.price_policy = _object.price_policy

    def process_view(self, request, view_func, view_args, view_kwargs):

        if not request.path_info.startswith('/manage/'):
            return

        project_id = view_kwargs.get('project_id')
        project_object = models.Project.objects.filter(creator=request.tracer.user, id=project_id).first()
        if project_object:
            request.tracer.project = project_object
            return

        project_user_object = models.ProjectUser.objects.filter(user=request.tracer.user, project_id=project_id).first()
        if project_user_object:
            request.tracer.project = project_user_object.project
            return

        return redirect('project_list')



