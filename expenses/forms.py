from django import forms


class ExpenseCreateForm(forms.Form):
    amount = forms.DecimalField(
        min_value=0.01,
        max_digits=10,
        decimal_places=2
    )

    date = forms.DateField(
        input_formats=["%Y-%m-%d"]
    )

    category_id = forms.IntegerField()

    description = forms.CharField(
        required=False,
        max_length=255
    )
