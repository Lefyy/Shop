from django import forms

class CheckoutForm(forms.Form):
    full_name = forms.CharField(max_length=255)
    email = forms.EmailField()
    address = forms.CharField(widget=forms.Textarea, required=False)