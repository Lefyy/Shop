from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.core.validators import MinLengthValidator
from phonenumber_field.formfields import PhoneNumberField
from .models import Product, Customer
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class CheckoutForm(forms.Form):
    address = forms.CharField(
        label='Адрес доставки',
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите адрес доставки'
        })
    )

class CustomUserCreationForm(UserCreationForm):
    full_name = forms.CharField(
        label='ФИО',
        required=True,
        max_length=150,
        widget=forms.TextInput(attrs={'placeholder': 'Введите ваше полное имя'})
    )
    email = forms.EmailField(
        label='Email',
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Введите ваш email'})
    )
    phone_number = PhoneNumberField(
        label='Телефон',
        region='RU',
        required=True,
        widget=forms.TextInput(attrs={'placeholder': '+7XXXXXXXXXX'})
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "full_name", "phone_number", "password1", "password2")
        labels = {'username': 'Логин'}
        widgets = {'username': forms.TextInput(attrs={'placeholder': 'Введите логин'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = "Логин"
        self.fields['password1'].label = "Пароль"
        self.fields['password2'].label = "Подтверждение пароля"
        self.fields['password1'].help_text = "Пароль должен содержать не менее 4 символов."
        self.fields['password1'].validators = [MinLengthValidator(4)]
        self.fields['password2'].help_text = None
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Введённые пароли не совпадают.")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get('email', '').strip()
        user.first_name = self.cleaned_data.get('full_name', '').strip()
        if commit:
            user.save()
            Customer.objects.update_or_create(
                user=user,
                defaults={
                    'phone_number': str(self.cleaned_data.get('phone_number', '')),
                }
            )
        return user
    
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'price', 'quantity', 'category', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].empty_label = "Категория не выбрана"