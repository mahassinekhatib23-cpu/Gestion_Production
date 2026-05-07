from django.db import models
from django.utils import timezone


class Article(models.Model):
    TYPE_CHOICES = [
        ("Matière Première", "Matière Première"),
        ("Produit Fini", "Produit Fini"),
    ]
    reference = models.CharField(max_length=100, unique=True)
    libelle = models.CharField(max_length=255)
    type_article = models.CharField(max_length=32, choices=TYPE_CHOICES)
    stock_actuel = models.IntegerField(default=0)
    stock_min = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.reference} - {self.libelle}"


class Fournisseur(models.Model):
    nom = models.CharField(max_length=255)

    def __str__(self):
        return self.nom


class Client(models.Model):
    nom = models.CharField(max_length=255)

    def __str__(self):
        return self.nom


class OrdreFabrication(models.Model):
    STATUTS = [("En attente", "En attente"), ("En cours", "En cours"), ("Terminé", "Terminé"), ("Annulé", "Annulé")]
    num_of = models.CharField(max_length=64, unique=True)
    article_produit = models.ForeignKey(Article, on_delete=models.CASCADE, related_name="ofs")
    qte_prevue = models.IntegerField()
    qte_produite = models.IntegerField(default=0)
    date_prevue = models.DateField()
    date_fin = models.DateTimeField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUTS, default="En attente")
    num_lot = models.CharField(max_length=64, blank=True)

    def __str__(self):
        return self.num_of


class Reception(models.Model):
    num_bon_rec = models.CharField(max_length=64, unique=True)
    date_rec = models.DateField(default=timezone.now)
    fournisseur = models.ForeignKey(Fournisseur, on_delete=models.CASCADE)


class ConcerneRec(models.Model):
    reception = models.ForeignKey(Reception, on_delete=models.CASCADE, related_name="lignes")
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    qte = models.IntegerField()


class Expedition(models.Model):
    num_bon_exp = models.CharField(max_length=64, unique=True)
    date_exp = models.DateField(default=timezone.now)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)


class ConcerneExp(models.Model):
    expedition = models.ForeignKey(Expedition, on_delete=models.CASCADE, related_name="lignes")
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    qte = models.IntegerField()


class MouvementStock(models.Model):
    type_mvt = models.CharField(max_length=64)
    qte = models.IntegerField()
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    of = models.ForeignKey(OrdreFabrication, null=True, blank=True, on_delete=models.SET_NULL)
    rec = models.ForeignKey(Reception, null=True, blank=True, on_delete=models.SET_NULL)
    exp = models.ForeignKey(Expedition, null=True, blank=True, on_delete=models.SET_NULL)
    date_mvt = models.DateTimeField(default=timezone.now)


class Consomme(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    of = models.ForeignKey(OrdreFabrication, on_delete=models.CASCADE)
    qte_consommee = models.IntegerField()
    date_creation = models.DateTimeField(default=timezone.now)
