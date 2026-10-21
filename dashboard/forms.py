import json
from decimal import Decimal, InvalidOperation
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Customer, InventoryItem, Order, Payment, Product

class StyledFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"field-control {existing}".strip()
            if field.help_text:
                field.widget.attrs["aria-describedby"] = f"hint-{field.label.lower().replace(' ', '-') }"

class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Username", widget=forms.TextInput(attrs={"autocomplete": "username", "placeholder": "Your staff username"}))
    password = forms.CharField(label="Password", strip=False, widget=forms.PasswordInput(attrs={"autocomplete": "current-password", "placeholder": "Your password"}))

class ProductForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "category", "description", "price", "is_available"]
        widgets = {"description": forms.TextInput(attrs={"placeholder": "Short menu description"}), "price": forms.NumberInput(attrs={"step": "0.01", "min": "0.01"})}

class CustomerForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Customer
        fields = ["name", "phone", "email", "notes"]
        widgets = {"name": forms.TextInput(attrs={"placeholder": "Full name"}), "phone": forms.TextInput(attrs={"placeholder": "+254 ..."}), "email": forms.EmailInput(attrs={"placeholder": "name@example.com"})}

class InventoryAdjustForm(StyledFormMixin, forms.Form):
    transaction_type = forms.ChoiceField(choices=[])
    quantity = forms.DecimalField(min_value=Decimal("0.01"), max_digits=10, decimal_places=2)
    reason = forms.CharField(max_length=240, widget=forms.TextInput(attrs={"placeholder": "Why is stock changing?"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["transaction_type"].choices = [("IN", "Stock in"), ("OUT", "Stock out"), ("ADJUST", "Adjustment")]

class OrderForm(StyledFormMixin, forms.Form):
    customer = forms.ModelChoiceField(queryset=Customer.objects.order_by("name"), required=False, empty_label="Walk-in customer")
    items_json = forms.CharField(widget=forms.HiddenInput())
    payment_method = forms.ChoiceField(choices=Payment.Methods.choices)
    payment_status = forms.ChoiceField(choices=Payment.Status.choices, initial=Payment.Status.PAID)
    payment_amount = forms.DecimalField(required=False, min_value=Decimal("0.01"), max_digits=10, decimal_places=2)
    payment_reference = forms.CharField(required=False, max_length=80, widget=forms.TextInput(attrs={"placeholder": "Optional till / receipt reference"}))
    notes = forms.CharField(required=False, max_length=240, widget=forms.TextInput(attrs={"placeholder": "Optional order note"}))

    def clean_items_json(self):
        raw = self.cleaned_data["items_json"]
        try:
            items = json.loads(raw)
        except (TypeError, json.JSONDecodeError) as exc:
            raise forms.ValidationError("Add at least one valid product to the order.") from exc
        if not isinstance(items, list) or not items:
            raise forms.ValidationError("Add at least one product to the order.")
        clean = []
        for item in items:
            try:
                product_id = int(item["product_id"])
                quantity = int(item["quantity"])
            except (KeyError, TypeError, ValueError) as exc:
                raise forms.ValidationError("Each order line must have a product and quantity.") from exc
            if quantity < 1 or quantity > 100:
                raise forms.ValidationError("Quantities must be between 1 and 100.")
            clean.append({"product_id": product_id, "quantity": quantity})
        return clean
