from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from django.db import transaction
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST

from .models import Coupon, UserCoupon, CouponLog
from .services import CouponService
from .forms import CouponForm, IssueCouponForm, BulkIssueCouponForm, ClaimCouponForm
from accounts.models import User
from products.models import Product
import json


class AdminRequiredMixin(UserPassesTestMixin):
    """관리자 권한 확인 믹스인"""
    def test_func(self):
        return self.request.user.is_authenticated and (
            self.request.user.is_staff or 
            self.request.user.user_type in ['ADMIN', 'STAFF']
        )


class CouponListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """쿠폰 목록 (관리자)"""
    model = Coupon
    template_name = 'coupons/admin/list.html'
    context_object_name = 'coupons'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 검색
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(code__icontains=search_query) |
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        # 필터
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(
                is_active=True,
                valid_from__lte=timezone.now(),
                valid_to__gte=timezone.now()
            )
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        elif status == 'expired':
            queryset = queryset.filter(valid_to__lt=timezone.now())
        elif status == 'upcoming':
            queryset = queryset.filter(valid_from__gt=timezone.now())
        
        discount_type = self.request.GET.get('discount_type')
        if discount_type:
            queryset = queryset.filter(discount_type=discount_type)
        
        issue_type = self.request.GET.get('issue_type')
        if issue_type:
            queryset = queryset.filter(issue_type=issue_type)
        
        # 정렬
        sort_by = self.request.GET.get('sort', '-created_at')
        queryset = queryset.order_by(sort_by)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_count'] = self.get_queryset().count()
        context['active_count'] = Coupon.objects.filter(
            is_active=True,
            valid_from__lte=timezone.now(),
            valid_to__gte=timezone.now()
        ).count()
        context['search_query'] = self.request.GET.get('q', '')
        context['current_filters'] = self.request.GET.dict()
        return context


class CouponCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    """쿠폰 생성 (관리자)"""
    model = Coupon
    form_class = CouponForm
    template_name = 'coupons/admin/form.html'
    success_url = reverse_lazy('coupons:admin_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, '쿠폰이 생성되었습니다.')
        
        # 로그 기록
        response = super().form_valid(form)
        CouponLog.objects.create(
            coupon=self.object,
            user=self.request.user,
            action='CREATED',
            details={'initial_data': form.cleaned_data}
        )
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '쿠폰 생성'
        return context


class CouponUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    """쿠폰 수정 (관리자)"""
    model = Coupon
    form_class = CouponForm
    template_name = 'coupons/admin/form.html'
    success_url = reverse_lazy('coupons:admin_list')
    
    def form_valid(self, form):
        messages.success(self.request, '쿠폰이 수정되었습니다.')
        
        # 로그 기록
        CouponLog.objects.create(
            coupon=self.object,
            user=self.request.user,
            action='MODIFIED',
            details={'changed_fields': list(form.changed_data)}
        )
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '쿠폰 수정'
        return context


class CouponDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    """쿠폰 삭제 (관리자)"""
    model = Coupon
    template_name = 'coupons/admin/delete.html'
    success_url = reverse_lazy('coupons:admin_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, '쿠폰이 삭제되었습니다.')
        return super().delete(request, *args, **kwargs)


class CouponDetailView(LoginRequiredMixin, AdminRequiredMixin, DetailView):
    """쿠폰 상세 (관리자)"""
    model = Coupon
    template_name = 'coupons/admin/detail.html'
    context_object_name = 'coupon'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        coupon = self.object
        
        # 발급 내역
        issued_coupons = UserCoupon.objects.filter(coupon=coupon).select_related('user')
        context['issued_coupons'] = issued_coupons[:10]
        context['issued_total'] = issued_coupons.count()
        
        # 사용 내역
        used_coupons = issued_coupons.filter(status='USED')
        context['used_coupons'] = used_coupons[:10]
        context['used_total'] = used_coupons.count()
        
        # 통계
        context['stats'] = {
            'issued_count': coupon.issued_quantity,
            'used_count': coupon.used_count,
            'remaining_quantity': coupon.remaining_quantity,
            'usage_rate': (coupon.used_count / coupon.issued_quantity * 100) if coupon.issued_quantity > 0 else 0,
            'total_discount': used_coupons.aggregate(Sum('discount_amount'))['discount_amount__sum'] or 0
        }
        
        # 로그
        context['logs'] = CouponLog.objects.filter(coupon=coupon).order_by('-created_at')[:20]
        
        return context


@login_required
@user_passes_test(lambda u: u.is_staff or u.user_type in ['ADMIN', 'STAFF'])
def duplicate_coupon(request, pk):
    """쿠폰 복제"""
    original_coupon = get_object_or_404(Coupon, pk=pk)
    
    # 쿠폰 복제
    new_coupon = original_coupon
    new_coupon.pk = None
    new_coupon.code = None  # 새로운 코드 자동 생성
    new_coupon.name = f"{original_coupon.name} (복사본)"
    new_coupon.issued_quantity = 0
    new_coupon.used_count = 0
    new_coupon.created_by = request.user
    new_coupon.save()
    
    # M2M 관계 복사
    new_coupon.applicable_categories.set(original_coupon.applicable_categories.all())
    new_coupon.applicable_products.set(original_coupon.applicable_products.all())
    new_coupon.target_users.set(original_coupon.target_users.all())
    
    messages.success(request, f'쿠폰이 복제되었습니다. 새 쿠폰 코드: {new_coupon.code}')
    return redirect('coupons:admin_edit', pk=new_coupon.pk)


@login_required
@user_passes_test(lambda u: u.is_staff or u.user_type in ['ADMIN', 'STAFF'])
@require_POST
def toggle_coupon_active(request, pk):
    """쿠폰 활성/비활성 토글"""
    coupon = get_object_or_404(Coupon, pk=pk)
    coupon.is_active = not coupon.is_active
    coupon.save()
    
    status = "활성화" if coupon.is_active else "비활성화"
    messages.success(request, f'쿠폰이 {status}되었습니다.')
    
    # 로그 기록
    CouponLog.objects.create(
        coupon=coupon,
        user=request.user,
        action='MODIFIED',
        details={'is_active': coupon.is_active}
    )
    
    return redirect('coupons:admin_detail', pk=pk)


class IssueCouponView(LoginRequiredMixin, AdminRequiredMixin, FormView):
    """개별 쿠폰 발급 (관리자)"""
    form_class = IssueCouponForm
    template_name = 'coupons/admin/issue.html'
    success_url = reverse_lazy('coupons:admin_issued_list')
    
    def form_valid(self, form):
        coupon = form.cleaned_data['coupon']
        user = form.cleaned_data['user']
        
        success, result = CouponService.issue_coupon_to_user(coupon, user)
        
        if success:
            messages.success(self.request, f'{user.username}님에게 쿠폰이 발급되었습니다.')
        else:
            messages.error(self.request, result)
            return self.form_invalid(form)
        
        return super().form_valid(form)


class BulkIssueCouponView(LoginRequiredMixin, AdminRequiredMixin, FormView):
    """대량 쿠폰 발급 (관리자)"""
    form_class = BulkIssueCouponForm
    template_name = 'coupons/admin/bulk_issue.html'
    success_url = reverse_lazy('coupons:admin_issued_list')
    
    def form_valid(self, form):
        coupon = form.cleaned_data['coupon']
        target_type = form.cleaned_data['target_type']
        
        # 대상 사용자 선택
        users = User.objects.filter(is_active=True)
        
        if target_type == 'ALL':
            pass  # 모든 사용자
        elif target_type == 'MEMBERSHIP':
            membership_levels = form.cleaned_data.get('membership_levels', [])
            if membership_levels:
                users = users.filter(membership_level__in=membership_levels)
        elif target_type == 'SPECIFIC':
            specific_users = form.cleaned_data.get('specific_users', [])
            if specific_users:
                users = users.filter(id__in=[u.id for u in specific_users])
        elif target_type == 'NEW':
            days = form.cleaned_data.get('days_since_join', 7)
            date_threshold = timezone.now() - timezone.timedelta(days=days)
            users = users.filter(created_at__gte=date_threshold)
        
        # 발급 처리
        success_count = 0
        fail_count = 0
        
        with transaction.atomic():
            for user in users:
                success, result = CouponService.issue_coupon_to_user(coupon, user, log=False)
                if success:
                    success_count += 1
                else:
                    fail_count += 1
            
            # 대량 발급 로그
            CouponLog.objects.create(
                coupon=coupon,
                user=self.request.user,
                action='ISSUED',
                details={
                    'bulk_issue': True,
                    'target_type': target_type,
                    'success_count': success_count,
                    'fail_count': fail_count
                }
            )
        
        messages.success(
            self.request, 
            f'{success_count}명에게 쿠폰이 발급되었습니다. (실패: {fail_count}명)'
        )
        
        return super().form_valid(form)


class IssuedCouponListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """발급된 쿠폰 목록 (관리자)"""
    model = UserCoupon
    template_name = 'coupons/admin/issued_list.html'
    context_object_name = 'user_coupons'
    paginate_by = 30
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('user', 'coupon', 'order')
        
        # 필터
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        coupon_id = self.request.GET.get('coupon')
        if coupon_id:
            queryset = queryset.filter(coupon_id=coupon_id)
        
        user_id = self.request.GET.get('user')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # 검색
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(user__username__icontains=search_query) |
                Q(user__email__icontains=search_query) |
                Q(coupon__code__icontains=search_query) |
                Q(coupon__name__icontains=search_query)
            )
        
        return queryset.order_by('-issued_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['coupons'] = Coupon.objects.all()
        context['current_filters'] = self.request.GET.dict()
        return context


class CouponStatsView(LoginRequiredMixin, AdminRequiredMixin, DetailView):
    """쿠폰 통계 (관리자)"""
    model = Coupon
    template_name = 'coupons/admin/stats.html'
    
    def get_object(self):
        return None  # 전체 통계를 보여줄 때는 특정 객체 없음
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 전체 통계
        context['total_coupons'] = Coupon.objects.count()
        context['active_coupons'] = Coupon.objects.filter(
            is_active=True,
            valid_from__lte=timezone.now(),
            valid_to__gte=timezone.now()
        ).count()
        
        # 발급/사용 통계
        user_coupons = UserCoupon.objects.all()
        context['total_issued'] = user_coupons.count()
        context['total_used'] = user_coupons.filter(status='USED').count()
        context['total_expired'] = user_coupons.filter(status='EXPIRED').count()
        
        # 할인 금액 통계
        context['total_discount'] = user_coupons.filter(
            status='USED'
        ).aggregate(Sum('discount_amount'))['discount_amount__sum'] or 0
        
        # 쿠폰별 통계 (상위 10개)
        context['top_coupons'] = Coupon.objects.annotate(
            usage_count=Count('user_coupons', filter=Q(user_coupons__status='USED')),
            total_discount=Sum('user_coupons__discount_amount', filter=Q(user_coupons__status='USED'))
        ).order_by('-usage_count')[:10]
        
        # 월별 통계 (최근 6개월)
        from django.db.models.functions import TruncMonth
        six_months_ago = timezone.now() - timezone.timedelta(days=180)
        
        context['monthly_stats'] = UserCoupon.objects.filter(
            issued_at__gte=six_months_ago
        ).annotate(
            month=TruncMonth('issued_at')
        ).values('month').annotate(
            issued_count=Count('id'),
            used_count=Count('id', filter=Q(status='USED'))
        ).order_by('month')
        
        return context


class MyCouponListView(LoginRequiredMixin, ListView):
    """내 쿠폰 목록 (사용자)"""
    model = UserCoupon
    template_name = 'coupons/user/my_list.html'
    context_object_name = 'user_coupons'
    paginate_by = 20
    
    def get_queryset(self):
        return UserCoupon.objects.filter(
            user=self.request.user
        ).select_related('coupon').order_by('-issued_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['available_count'] = self.get_queryset().filter(
            status='ISSUED',
            expires_at__gte=timezone.now()
        ).count()
        context['used_count'] = self.get_queryset().filter(status='USED').count()
        context['expired_count'] = self.get_queryset().filter(status='EXPIRED').count()
        return context


class ClaimCouponView(LoginRequiredMixin, FormView):
    """쿠폰 코드 입력 (사용자)"""
    form_class = ClaimCouponForm
    template_name = 'coupons/user/claim.html'
    success_url = reverse_lazy('coupons:my_list')
    
    def form_valid(self, form):
        code = form.cleaned_data['code']
        
        success, result = CouponService.issue_coupon_by_code(code, self.request.user)
        
        if success:
            messages.success(self.request, '쿠폰이 발급되었습니다.')
        else:
            messages.error(self.request, result)
            return self.form_invalid(form)
        
        return super().form_valid(form)


class AvailableCouponListView(LoginRequiredMixin, ListView):
    """사용 가능한 쿠폰 목록 (사용자)"""
    model = UserCoupon
    template_name = 'coupons/user/available.html'
    context_object_name = 'available_coupons'
    
    def get_queryset(self):
        return UserCoupon.objects.filter(
            user=self.request.user,
            status='ISSUED',
            expires_at__gte=timezone.now(),
            coupon__is_active=True
        ).select_related('coupon')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 주문 금액이 전달된 경우 할인 금액 계산
        order_amount = self.request.GET.get('amount')
        if order_amount:
            try:
                order_amount = float(order_amount)
                for user_coupon in context['available_coupons']:
                    user_coupon.calculated_discount = CouponService.calculate_discount(
                        user_coupon.coupon, order_amount
                    )
            except ValueError:
                pass
        
        return context


# API Views
@login_required
def validate_coupon_api(request):
    """쿠폰 유효성 검증 API"""
    if request.method == 'POST':
        data = json.loads(request.body)
        user_coupon_id = data.get('user_coupon_id')
        order_amount = float(data.get('order_amount', 0))
        
        try:
            user_coupon = UserCoupon.objects.get(
                id=user_coupon_id,
                user=request.user
            )
            
            is_valid, message = CouponService.validate_coupon_for_order(
                user_coupon, order_amount
            )
            
            return JsonResponse({
                'valid': is_valid,
                'message': message
            })
            
        except UserCoupon.DoesNotExist:
            return JsonResponse({
                'valid': False,
                'message': '쿠폰을 찾을 수 없습니다.'
            })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def calculate_discount_api(request):
    """쿠폰 할인 금액 계산 API"""
    if request.method == 'POST':
        data = json.loads(request.body)
        user_coupon_id = data.get('user_coupon_id')
        order_amount = float(data.get('order_amount', 0))
        
        try:
            user_coupon = UserCoupon.objects.get(
                id=user_coupon_id,
                user=request.user
            )
            
            discount = CouponService.calculate_discount(
                user_coupon.coupon, order_amount
            )
            
            return JsonResponse({
                'discount': float(discount),
                'final_amount': float(order_amount - discount)
            })
            
        except UserCoupon.DoesNotExist:
            return JsonResponse({
                'error': '쿠폰을 찾을 수 없습니다.'
            }, status=404)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)