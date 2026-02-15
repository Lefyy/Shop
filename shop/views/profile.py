from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.db.models import Sum, Count, F, ExpressionWrapper, DecimalField

from ..models import Orders


@login_required
def profile(request):
    user = request.user
    customer = getattr(user, 'customer', None)

    # 1. Получаем заказы пользователя (если профиль покупателя существует)
    if customer:
        orders = (
            Orders.objects
            .filter(customer=customer)
            .select_related('status')
            .prefetch_related('orderitem_set__product')
            .annotate(
                total_items=Sum('orderitem__quantity'),
                unique_items=Count('orderitem__product', distinct=True),
                total_price=ExpressionWrapper(
                    Sum(F('orderitem__quantity') * F('orderitem__unit_price')),
                    output_field=DecimalField()
                )
            )
            .order_by('-created_date')
        )
    else:
        orders = Orders.objects.none()

    # 2. Обновление данных профиля
    if request.method == 'POST' and 'save_profile' in request.POST:
        if customer:  # Проверка, чтобы избежать ошибки, если customer == None
            customer.phone_number = request.POST.get('phone_number', '').strip()
            customer.address = request.POST.get('address', '').strip()
            customer.save(update_fields=['phone_number', 'address'])
        return redirect('shop:profile')

    # 3. Форма смены пароля
    if request.method == 'POST' and 'change_password' in request.POST:
        pwd_form = PasswordChangeForm(user=user, data=request.POST)
    else:
        pwd_form = PasswordChangeForm(user=user)

    # Добавляем CSS-классы и плейсхолдеры для красивого отображения в шаблоне
    for field_name, field in pwd_form.fields.items():
        field.widget.attrs['class'] = 'form-control'
    
    if 'old_password' in pwd_form.fields:
        pwd_form.fields['old_password'].widget.attrs['placeholder'] = 'Введите текущий пароль'
    if 'new_password1' in pwd_form.fields:
        pwd_form.fields['new_password1'].widget.attrs['placeholder'] = 'Введите новый пароль'
    if 'new_password2' in pwd_form.fields:
        pwd_form.fields['new_password2'].widget.attrs['placeholder'] = 'Повторите новый пароль'

    pwd_message = None

    # 4. Обработка сохранения нового пароля
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