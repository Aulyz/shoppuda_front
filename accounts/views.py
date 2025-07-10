# File: accounts/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

def login_view(request):
    """로그인 뷰"""
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                next_url = request.GET.get('next', 'dashboard:home')
                messages.success(request, f'{user.username}님, 환영합니다!')
                return redirect(next_url)
            else:
                messages.error(request, '아이디 또는 비밀번호가 올바르지 않습니다.')
        else:
            messages.error(request, '아이디와 비밀번호를 모두 입력해주세요.')
    
    return render(request, 'accounts/login.html')

def logout_view(request):
    """로그아웃 뷰"""
    if request.user.is_authenticated:
        username = request.user.username
        logout(request)
        messages.info(request, f'{username}님이 로그아웃되었습니다.')
    
    return redirect('accounts:login')

@login_required
def profile_view(request):
    """프로필 뷰"""
    return render(request, 'accounts/profile.html')

class SignUpView(CreateView):
    """회원가입 뷰"""
    model = User
    form_class = UserCreationForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('accounts:login')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, '회원가입이 완료되었습니다. 로그인해주세요.')
        return response
