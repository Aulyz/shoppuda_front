from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, UserChangeForm
from django.core.exceptions import ValidationError
from .models import User, ShippingAddress
import re


class CustomLoginForm(AuthenticationForm):
    """커스텀 로그인 폼"""
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': '아이디 또는 이메일'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': '비밀번호'
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'
        })
    )


class CustomSignUpForm(UserCreationForm):
    """커스텀 회원가입 폼"""
    # 필수 정보
    username = forms.CharField(
        label='아이디',
        help_text='영문, 숫자 조합 4-20자',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': '아이디를 입력하세요'
        })
    )
    
    email = forms.EmailField(
        label='이메일',
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'example@email.com'
        })
    )
    
    first_name = forms.CharField(
        label='이름',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': '홍길동'
        })
    )
    
    phone_number = forms.CharField(
        label='전화번호',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': '010-0000-0000'
        })
    )
    
    # 선택 정보
    birth_date = forms.DateField(
        label='생년월일',
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
        })
    )
    
    gender = forms.ChoiceField(
        label='성별',
        choices=[('', '선택하세요')] + User.GENDER_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
        })
    )
    
    # 주소 정보
    postal_code = forms.CharField(
        label='우편번호',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': '우편번호',
            'readonly': 'readonly'
        })
    )
    
    address = forms.CharField(
        label='주소',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': '기본 주소',
            'readonly': 'readonly'
        })
    )
    
    detail_address = forms.CharField(
        label='상세주소',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': '상세 주소를 입력하세요'
        })
    )
    
    # 약관 동의
    terms_agreed = forms.BooleanField(
        label='이용약관 동의',
        widget=forms.CheckboxInput(attrs={
            'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'
        })
    )
    
    privacy_agreed = forms.BooleanField(
        label='개인정보처리방침 동의',
        widget=forms.CheckboxInput(attrs={
            'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'
        })
    )
    
    marketing_agreed = forms.BooleanField(
        label='마케팅 정보 수신 동의',
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'
        })
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password1', 'password2', 'first_name',
            'phone_number', 'birth_date', 'gender', 'postal_code', 
            'address', 'detail_address', 'terms_agreed', 'privacy_agreed', 
            'marketing_agreed'
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': '비밀번호 (8자 이상)'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': '비밀번호 확인'
        })
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not re.match(r'^[a-zA-Z0-9]{4,20}$', username):
            raise ValidationError('아이디는 영문, 숫자 조합 4-20자여야 합니다.')
        return username
    
    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        # 숫자만 추출
        phone_number = re.sub(r'[^0-9]', '', phone_number)
        
        if not re.match(r'^01[0-9]{8,9}$', phone_number):
            raise ValidationError('올바른 전화번호 형식이 아닙니다.')
        
        # 하이픈 추가하여 저장
        if len(phone_number) == 10:
            return f"{phone_number[:3]}-{phone_number[3:6]}-{phone_number[6:]}"
        else:
            return f"{phone_number[:3]}-{phone_number[3:7]}-{phone_number[7:]}"
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('이미 사용 중인 이메일입니다.')
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('terms_agreed'):
            raise ValidationError('이용약관에 동의해주세요.')
        if not cleaned_data.get('privacy_agreed'):
            raise ValidationError('개인정보처리방침에 동의해주세요.')
        return cleaned_data


class UserUpdateForm(UserChangeForm):
    """회원정보 수정 폼"""
    password = None  # 비밀번호 필드 제거
    
    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'phone_number', 
            'birth_date', 'gender', 'postal_code', 'address', 
            'detail_address', 'marketing_agreed', 'profile_image'
        ]
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'birth_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'gender': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'readonly': 'readonly'
            }),
            'address': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'readonly': 'readonly'
            }),
            'detail_address': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'marketing_agreed': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'
            }),
            'profile_image': forms.FileInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            })
        }


class ShippingAddressForm(forms.ModelForm):
    """배송지 폼"""
    class Meta:
        model = ShippingAddress
        fields = [
            'nickname', 'recipient_name', 'phone_number',
            'postal_code', 'address', 'detail_address', 'is_default'
        ]
        widgets = {
            'nickname': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': '예: 집, 회사'
            }),
            'recipient_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': '010-0000-0000'
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'readonly': 'readonly'
            }),
            'address': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'readonly': 'readonly'
            }),
            'detail_address': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'is_default': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'
            })
        }