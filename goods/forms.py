from django import forms

class ProductFilterForm(forms.Form):
    name = forms.CharField(required=False)
    min_price = forms.DecimalField(required=False)
    max_price = forms.DecimalField(required=False)
