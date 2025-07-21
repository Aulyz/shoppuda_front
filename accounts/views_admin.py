from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta

from .models import UserPermission, PointHistory
from .forms import CustomSignUpForm
from .permissions import (
    permission_required, admin_level_required, 
    PermissionRequiredMixin, AdminLevelRequiredMixin
)

User = get_user_model()


class AdminCreateUserView(AdminLevelRequiredMixin, CreateView):
    """관리자용 사용자 생성 뷰"""
    model = User
    form_class = CustomSignUpForm
    template_name = 'accounts/admin_user_create.html'
    success_url = reverse_lazy('accounts:admin_user_list')
    min_admin_level = 3  # 중간 관리자 이상
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # 회원가입 시 기본 포인트 지급
        self.object.add_points(1000)
        
        # 포인트 내역 기록
        PointHistory.objects.create(
            user=self.object,
            point_type='EARN',
            amount=1000,
            balance=self.object.points,
            description='회원가입 축하 포인트'
        )
        
        # 생성자 정보 저장 (옵션)
        # self.object.created_by = self.request.user
        # self.object.save()
        
        messages.success(self.request, f'사용자 "{self.object.username}"이(가) 성공적으로 생성되었습니다.')
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_admin_create'] = True
        return context


@login_required
@admin_level_required(3)
def user_permissions_management(request, user_id):
    """사용자 권한 관리 페이지"""
    target_user = get_object_or_404(User, pk=user_id)
    
    # 현재 사용자가 대상 사용자보다 높은 레벨이어야 함
    if request.user.admin_level <= target_user.admin_level:
        messages.error(request, "더 높은 레벨의 관리자 권한을 수정할 수 없습니다.")
        return redirect('accounts:user_list')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'grant':
            permission_code = request.POST.get('permission')
            expires_days = request.POST.get('expires_days')
            
            # 권한 부여
            permission, created = UserPermission.objects.get_or_create(
                user=target_user,
                permission=permission_code,
                defaults={
                    'granted_by': request.user,
                    'is_active': True
                }
            )
            
            if expires_days:
                permission.expires_at = timezone.now() + timedelta(days=int(expires_days))
            else:
                permission.expires_at = None
            
            permission.is_active = True
            permission.save()
            
            messages.success(request, f"{target_user.username}에게 {permission.get_permission_display()} 권한을 부여했습니다.")
        
        elif action == 'revoke':
            permission_id = request.POST.get('permission_id')
            permission = get_object_or_404(UserPermission, pk=permission_id, user=target_user)
            permission.is_active = False
            permission.save()
            messages.success(request, f"{permission.get_permission_display()} 권한을 회수했습니다.")
        
        return redirect('accounts:user_permissions', user_id=user_id)
    
    # 사용자의 현재 권한 목록
    current_permissions = target_user.permissions.filter(is_active=True)
    
    # 부여 가능한 권한 목록 (현재 사용자의 레벨에 따라)
    available_permissions = []
    for perm_code, perm_name in UserPermission.PERMISSION_CHOICES:
        # 이미 가진 권한은 제외
        if not current_permissions.filter(permission=perm_code).exists():
            # 레벨에 따른 권한 부여 제한
            if request.user.admin_level >= 4:  # 상위 관리자
                available_permissions.append((perm_code, perm_name))
            elif request.user.admin_level == 3:  # 중간 관리자
                if not perm_code.startswith(('system_', 'financial_')):
                    available_permissions.append((perm_code, perm_name))
    
    context = {
        'target_user': target_user,
        'current_permissions': current_permissions,
        'available_permissions': available_permissions,
    }
    
    return render(request, 'accounts/user_permissions.html', context)


class AdminUserListView(AdminLevelRequiredMixin, ListView):
    """관리자 전용 사용자 목록"""
    model = User
    template_name = 'accounts/admin_user_list.html'
    context_object_name = 'users'
    paginate_by = 50
    min_admin_level = 2
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 권한 개수를 미리 계산
        queryset = queryset.annotate(
            permission_count=Count('permissions', filter=Q(permissions__is_active=True))
        )
        
        # 검색 기능
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        
        # 필터링
        user_type = self.request.GET.get('user_type')
        if user_type:
            queryset = queryset.filter(user_type=user_type)
        
        admin_level = self.request.GET.get('admin_level')
        if admin_level:
            queryset = queryset.filter(admin_level=admin_level)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_types'] = User.USER_TYPE_CHOICES
        context['admin_levels'] = User.ADMIN_LEVEL_CHOICES
        return context


@login_required
@permission_required('user_edit')
def change_user_type(request, user_id):
    """사용자 타입 변경"""
    user = get_object_or_404(User, pk=user_id)
    
    if request.method == 'POST':
        new_type = request.POST.get('user_type')
        new_admin_level = request.POST.get('admin_level', 0)
        
        # 권한 체크
        if new_type == 'ADMIN' and request.user.admin_level < 4:
            messages.error(request, "관리자로 변경하려면 상위 관리자 권한이 필요합니다.")
            return redirect('accounts:admin_user_list')
        
        user.user_type = new_type
        if new_type == 'ADMIN':
            user.admin_level = int(new_admin_level)
            user.is_staff = True
        else:
            user.admin_level = 0
            user.is_staff = False
        
        user.save()
        
        messages.success(request, f"{user.username}의 사용자 타입을 변경했습니다.")
        return redirect('accounts:admin_user_list')
    
    return render(request, 'accounts/change_user_type.html', {
        'target_user': user,
        'user_types': User.USER_TYPE_CHOICES,
        'admin_levels': User.ADMIN_LEVEL_CHOICES,
    })


@login_required
@admin_level_required(5)
def permission_dashboard(request):
    """권한 대시보드 - 최고 관리자 전용"""
    # 전체 사용자 수
    total_users = User.objects.filter(is_active=True).count()
    total_admins = User.objects.filter(user_type='ADMIN', is_active=True).count()
    active_permissions = UserPermission.objects.filter(
        is_active=True
    ).exclude(
        expires_at__lt=timezone.now()
    ).count()
    
    # 권한별 사용자 수
    permission_stats = []
    for perm_code, perm_name in UserPermission.PERMISSION_CHOICES:
        count = UserPermission.objects.filter(
            permission=perm_code,
            is_active=True
        ).exclude(
            expires_at__lt=timezone.now()
        ).count()
        permission_stats.append({
            'code': perm_code,
            'name': perm_name,
            'count': count
        })
    
    # 관리자 레벨별 사용자 수
    admin_stats = []
    for level, level_name in User.ADMIN_LEVEL_CHOICES:
        count = User.objects.filter(
            user_type='ADMIN',
            admin_level=level,
            is_active=True
        ).count()
        admin_stats.append({
            'level': level,
            'name': level_name,
            'count': count
        })
    
    # 최근 권한 부여 내역
    recent_permissions = UserPermission.objects.select_related(
        'user', 'granted_by'
    ).order_by('-granted_at')[:20]
    
    # 만료 예정 권한
    expiring_permissions = UserPermission.objects.filter(
        is_active=True,
        expires_at__isnull=False,
        expires_at__lt=timezone.now() + timedelta(days=7),
        expires_at__gt=timezone.now()
    ).select_related('user').order_by('expires_at')
    
    context = {
        'total_users': total_users,
        'total_admins': total_admins,
        'active_permissions': active_permissions,
        'permission_stats': permission_stats,
        'admin_stats': admin_stats,
        'recent_permissions': recent_permissions,
        'expiring_permissions': expiring_permissions,
    }
    
    return render(request, 'accounts/permission_dashboard.html', context)


@login_required
@admin_level_required(2)
def user_detail_view(request, user_id):
    """사용자 상세 정보 뷰 - 관리자 전용"""
    target_user = get_object_or_404(User, pk=user_id)
    
    # 최근 주문 내역
    try:
        from orders.models import Order
        recent_orders = Order.objects.filter(
            user=target_user
        ).order_by('-created_at')[:10]
    except:
        recent_orders = []
    
    # 최근 포인트 내역
    recent_points = PointHistory.objects.filter(
        user=target_user
    ).order_by('-created_at')[:10]
    
    # 보유 권한
    active_permissions = target_user.permissions.filter(
        is_active=True
    ).exclude(
        expires_at__lt=timezone.now()
    )
    
    context = {
        'target_user': target_user,
        'recent_orders': recent_orders,
        'recent_points': recent_points,
        'active_permissions': active_permissions,
        'total_permissions': target_user.get_permissions(),
    }
    
    return render(request, 'accounts/admin_user_detail.html', context)