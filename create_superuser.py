import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shopuda.settings')
django.setup()

from accounts.models import User

# 관리자 계정 생성
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(
        username='admin',
        email='admin@shopuda.com',
        password='admin123',
        first_name='관리자',
        user_type='ADMIN',
        admin_level=5
    )
    print("관리자 계정이 생성되었습니다.")
    print("아이디: admin")
    print("비밀번호: admin123")
else:
    print("관리자 계정이 이미 존재합니다.")