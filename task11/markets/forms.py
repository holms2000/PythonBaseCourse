# markets/forms.py

from django import forms

class SearchMarketsForm(forms.Form):
    """
    Форма для простого поиска по городу и штату.
    """
    city = forms.CharField(
        max_length=100,
        required=False,
        label="Город",
        widget=forms.TextInput(attrs={'placeholder': 'Город'})
    )
    state = forms.CharField(
        max_length=50,
        required=False,
        label="Штат",
        widget=forms.TextInput(attrs={'placeholder': 'Штат'})
    )

class ReviewForm(forms.Form):
    """
    Форма для добавления или редактирования отзыва.
    """
    rating = forms.IntegerField(
        label="Рейтинг",
        min_value=1,
        max_value=5,
        widget=forms.NumberInput(attrs={'min': 1, 'max': 5})
    )
    comment = forms.CharField(
        label="Комментарий",
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Ваш отзыв...'})
    )