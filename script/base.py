import os
import sys
import django

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)     #添加配置文件寻找路径到PATH变量中
os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'bug_web.settings')
#写入名为bug_web的django项目的settings文件路径到环境变量中
django.setup()
