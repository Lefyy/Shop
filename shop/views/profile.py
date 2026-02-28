from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash

from ..selectors.profile_selectors import get_profile_orders, get_empty_orders

@login_required
def profile(request):
    user = request.user
    customer = getattr(user, 'customer', None)

    if customer:
        orders = get_profile_orders(customer)
    else:
        orders = get_empty_orders()

    if request.method == 'POST' and 'save_profile' in request.POST:
        if customer:
            customer.phone_number = request.POST.get('phone_number', '').strip()
            customer.address = request.POST.get('address', '').strip()
            customer.save(update_fields=['phone_number', 'address'])
        return redirect('shop:profile')

    if request.method == 'POST' and 'change_password' in request.POST:
        pwd_form = PasswordChangeForm(user=user, data=request.POST)
    else:
        pwd_form = PasswordChangeForm(user=user)

    for field_name, field in pwd_form.fields.items():
        field.widget.attrs['class'] = 'form-control'
    
    if 'old_password' in pwd_form.fields:
        pwd_form.fields['old_password'].widget.attrs['placeholder'] = 'Введите текущий пароль'
    if 'new_password1' in pwd_form.fields:
        pwd_form.fields['new_password1'].widget.attrs['placeholder'] = 'Введите новый пароль'
    if 'new_password2' in pwd_form.fields:
        pwd_form.fields['new_password2'].widget.attrs['placeholder'] = 'Повторите новый пароль'

    pwd_message = None

    if request.method == 'POST' and 'change_password' in request.POST:
        if pwd_form.is_valid():
            pwd_form.save()
            update_session_auth_hash(request, pwd_form.user)
            pwd_message = 'Пароль успешно изменён.'
        else:
            pwd_message = 'Ошибка при изменении пароля. Проверьте введенные данные.'

    return render(request, 'shop/profile.html', {
        'orders': orders,
        'customer': customer,
        'pwd_form': pwd_form,
        'pwd_message': pwd_message,
    })