"""
Settings module initialization
"""
import os

# 환경변수 DJANGO_ENV 값에 따라 설정 파일 선택
# 기본값은 'development'
env = os.environ.get('DJANGO_ENV', 'development')

if env == 'production':
    from .production import *
elif env == 'staging':
    from .staging import *
else:
    from .development import *