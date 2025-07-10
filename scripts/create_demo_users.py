# File: scripts/create_demo_users.py
import os
import sys
import django

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shopuda.settings')
django.setup()

from django.contrib.auth.models import User

def create_demo_user():
    """데모 사용자 생성"""
    username = 'admin'
    email = 'admin@shopuda.com'
    password = 'admin123!'
    
    if User.objects.filter(username=username).exists():
        print(f'사용자 "{username}"이 이미 존재합니다.')
        return
    
    user = User.objects.create_superuser(
        username=username,
        email=email,
        password=password,
        first_name='관리자'
    )
    
    print(f'데모 사용자가 생성되었습니다!')
    print(f'아이디: {username}')
    print(f'비밀번호: {password}')
    print(f'이메일: {email}')

if __name__ == '__main__':
    create_demo_user()