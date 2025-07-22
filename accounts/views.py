from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import CreateView, UpdateView, ListView, DeleteView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from .forms import CustomLoginForm, CustomSignUpForm, UserUpdateForm, ShippingAddressForm
from .models import ShippingAddress, PointHistory
import json

User = get_user_model()


def login_view(request):
    """로그인 뷰"""
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    
    if request.method == 'POST':
        print(f"POST data: {request.POST}")  # Debug
        form = CustomLoginForm(request, data=request.POST)
        print(f"Form is valid: {form.is_valid()}")  # Debug
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            remember_me = form.cleaned_data.get('remember_me')
            
            # 이메일로도 로그인 가능하도록 처리
            user = None
            if '@' in username:
                try:
                    user_obj = User.objects.get(email=username)
                    user = authenticate(request, username=user_obj.username, password=password)
                except User.DoesNotExist:
                    pass
            else:
                user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                
                # Remember me 처리
                if not remember_me:
                    request.session.set_expiry(0)
                else:
                    request.session.set_expiry(1209600)  # 2주
                
                messages.success(request, f'{user.first_name or user.username}님, 환영합니다!')
                
                # next 파라미터 처리 및 사용자 타입별 리디렉션
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                else:
                    # 사용자 타입에 따라 리디렉션
                    if user.user_type == 'ADMIN':
                        return redirect('dashboard:home')
                    else:
                        return redirect('shop:home')
            else:
                messages.error(request, '아이디 또는 비밀번호가 올바르지 않습니다.')
        else:
            # 폼 에러 메시지 추가
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
            messages.error(request, '입력한 정보를 다시 확인해주세요.')
    else:
        form = CustomLoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    """로그아웃 뷰"""
    logout(request)
    messages.success(request, '로그아웃되었습니다.')
    return redirect('shop:home')


class SignUpView(CreateView):
    """회원가입 뷰"""
    model = User
    form_class = CustomSignUpForm
    template_name = 'accounts/user_signup.html'  # 유저용 템플릿 사용
    success_url = reverse_lazy('accounts:login')
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.user_type == 'ADMIN':
                return redirect('dashboard:home')
            else:
                return redirect('shop:home')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # SystemSettings에서 회원가입 포인트 설정 가져오기
        from core.models import SystemSettings
        from core.email_utils import EmailService
        settings = SystemSettings.get_settings()
        
        # 회원가입 포인트 지급 여부 확인
        if settings.welcome_points_enabled and settings.welcome_points_amount > 0:
            # 포인트 지급
            self.object.add_points(settings.welcome_points_amount)
            
            # 포인트 내역 기록
            PointHistory.objects.create(
                user=self.object,
                point_type='EARN',
                amount=settings.welcome_points_amount,
                balance=self.object.points,
                description='회원가입 축하 포인트'
            )
            
            messages.success(self.request, f'회원가입이 완료되었습니다. 축하 포인트 {settings.welcome_points_amount:,}P가 지급되었습니다!')
        else:
            messages.success(self.request, '회원가입이 완료되었습니다. 로그인해주세요.')
        
        # 환영 이메일 발송
        try:
            EmailService.send_welcome_email(self.object)
        except Exception as e:
            # 이메일 발송 실패해도 회원가입은 정상 처리
            pass
        
        return response
    
    def form_invalid(self, form):
        messages.error(self.request, '입력한 정보를 다시 확인해주세요.')
        return super().form_invalid(form)


@login_required
def profile_view(request):
    """프로필 뷰"""
    user = request.user
    
    # 최근 주문 내역
    try:
        from orders.models import Order
        recent_orders = Order.objects.filter(
            user=user
        ).order_by('-created_at')[:5]
    except:
        recent_orders = []
    
    # 최근 포인트 내역
    recent_points = PointHistory.objects.filter(
        user=user
    ).order_by('-created_at')[:5]
    
    # 배송지 목록
    shipping_addresses = ShippingAddress.objects.filter(user=user)
    
    context = {
        'user': user,
        'recent_orders': recent_orders,
        'recent_points': recent_points,
        'shipping_addresses': shipping_addresses,
    }
    
    return render(request, 'accounts/profile.html', context)


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """프로필 수정 뷰"""
    model = User
    form_class = UserUpdateForm
    template_name = 'accounts/profile_edit.html'
    success_url = reverse_lazy('accounts:profile')
    
    def get_object(self):
        return self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, '프로필이 수정되었습니다.')
        return super().form_valid(form)


@login_required
def password_change_view(request):
    """비밀번호 변경 뷰"""
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # 현재 비밀번호 확인
        if not request.user.check_password(current_password):
            messages.error(request, '현재 비밀번호가 올바르지 않습니다.')
            return redirect('accounts:password_change')
        
        # 새 비밀번호 확인
        if new_password != confirm_password:
            messages.error(request, '새 비밀번호가 일치하지 않습니다.')
            return redirect('accounts:password_change')
        
        # 비밀번호 길이 확인
        if len(new_password) < 8:
            messages.error(request, '비밀번호는 8자 이상이어야 합니다.')
            return redirect('accounts:password_change')
        
        # 비밀번호 변경
        request.user.set_password(new_password)
        request.user.save()
        
        # 세션 업데이트 (로그아웃 방지)
        update_session_auth_hash(request, request.user)
        
        messages.success(request, '비밀번호가 변경되었습니다.')
        return redirect('accounts:profile')
    
    return render(request, 'accounts/password_change.html')


class ShippingAddressListView(LoginRequiredMixin, ListView):
    """배송지 목록 뷰"""
    model = ShippingAddress
    template_name = 'accounts/shipping_addresses.html'
    context_object_name = 'addresses'
    
    def get_queryset(self):
        return ShippingAddress.objects.filter(user=self.request.user)


class ShippingAddressCreateView(LoginRequiredMixin, CreateView):
    """배송지 추가 뷰"""
    model = ShippingAddress
    form_class = ShippingAddressForm
    template_name = 'accounts/shipping_address_form.html'
    success_url = reverse_lazy('accounts:shipping_addresses')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, '배송지가 추가되었습니다.')
        return super().form_valid(form)


class ShippingAddressUpdateView(LoginRequiredMixin, UpdateView):
    """배송지 수정 뷰"""
    model = ShippingAddress
    form_class = ShippingAddressForm
    template_name = 'accounts/shipping_address_form.html'
    success_url = reverse_lazy('accounts:shipping_addresses')
    
    def get_queryset(self):
        return ShippingAddress.objects.filter(user=self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, '배송지가 수정되었습니다.')
        return super().form_valid(form)


class ShippingAddressDeleteView(LoginRequiredMixin, DeleteView):
    """배송지 삭제 뷰"""
    model = ShippingAddress
    template_name = 'accounts/shipping_address_confirm_delete.html'
    success_url = reverse_lazy('accounts:shipping_addresses')
    
    def get_queryset(self):
        return ShippingAddress.objects.filter(user=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, '배송지가 삭제되었습니다.')
        return super().delete(request, *args, **kwargs)


@login_required
def point_history_view(request):
    """포인트 내역 뷰"""
    point_histories = PointHistory.objects.filter(
        user=request.user
    ).order_by('-created_at')
    
    # 필터링
    point_type = request.GET.get('type')
    if point_type:
        point_histories = point_histories.filter(point_type=point_type)
    
    # 페이지네이션
    from django.core.paginator import Paginator
    paginator = Paginator(point_histories, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'current_type': point_type,
    }
    
    return render(request, 'accounts/point_history.html', context)


@login_required
def check_username(request):
    """아이디 중복 확인 API"""
    username = request.GET.get('username', '')
    
    if len(username) < 4:
        return JsonResponse({
            'available': False,
            'message': '아이디는 4자 이상이어야 합니다.'
        })
    
    if User.objects.filter(username=username).exists():
        return JsonResponse({
            'available': False,
            'message': '이미 사용 중인 아이디입니다.'
        })
    
    return JsonResponse({
        'available': True,
        'message': '사용 가능한 아이디입니다.'
    })


@login_required
def check_email(request):
    """이메일 중복 확인 API"""
    email = request.GET.get('email', '')
    
    if not email or '@' not in email:
        return JsonResponse({
            'available': False,
            'message': '올바른 이메일 형식이 아닙니다.'
        })
    
    # 본인의 이메일은 제외
    if User.objects.filter(email=email).exclude(pk=request.user.pk).exists():
        return JsonResponse({
            'available': False,
            'message': '이미 사용 중인 이메일입니다.'
        })
    
    return JsonResponse({
        'available': True,
        'message': '사용 가능한 이메일입니다.'
    })


@login_required
def withdrawal_view(request):
    """회원 탈퇴 뷰"""
    if request.method == 'POST':
        password = request.POST.get('password')
        reason = request.POST.get('reason', '')
        
        # 비밀번호 확인
        if not request.user.check_password(password):
            messages.error(request, '비밀번호가 올바르지 않습니다.')
            return redirect('accounts:withdrawal')
        
        # 회원 탈퇴 처리
        user = request.user
        user.is_active = False
        user.withdrawal_reason = reason
        user.withdrawal_date = timezone.now()
        user.save()
        
        logout(request)
        messages.success(request, '회원 탈퇴가 완료되었습니다.')
        return redirect('accounts:login')
    
    return render(request, 'accounts/withdrawal.html')