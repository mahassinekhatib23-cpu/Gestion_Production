from django import forms

from .models import Article, Client, Fournisseur, OrdreFabrication


class CreateOFForm(forms.Form):
    article = forms.ModelChoiceField(queryset=Article.objects.filter(type_article="Produit Fini"))
    qte = forms.IntegerField(min_value=1)
    date_prevue = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))


class UpdateOFStatusForm(forms.Form):
    statut = forms.ChoiceField(choices=OrdreFabrication.STATUTS)


class ConsommationForm(forms.Form):
    of = forms.ModelChoiceField(queryset=OrdreFabrication.objects.exclude(statut__in=["Terminé", "Annulé"]))
    article = forms.ModelChoiceField(queryset=Article.objects.filter(type_article="Matière Première"))
    qte = forms.IntegerField(min_value=1)


class ReceptionForm(forms.Form):
    fournisseur = forms.ModelChoiceField(queryset=Fournisseur.objects.all())
    article = forms.ModelChoiceField(queryset=Article.objects.all())
    qte = forms.IntegerField(min_value=1)
    date_rec = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))


class ExpeditionForm(forms.Form):
    client = forms.ModelChoiceField(queryset=Client.objects.all())
    article = forms.ModelChoiceField(queryset=Article.objects.filter(type_article="Produit Fini"))
    qte = forms.IntegerField(min_value=1)
    date_exp = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))


class MovementForm(forms.Form):
    type_mvt = forms.ChoiceField(
        choices=[
            ("Entrée Réception", "Entrée Réception"),
            ("Sortie Production", "Sortie Production"),
            ("Entrée Production", "Entrée Production"),
            ("Sortie Expédition", "Sortie Expédition"),
        ]
    )
    article = forms.ModelChoiceField(queryset=Article.objects.all())
    qte = forms.IntegerField(min_value=1)
