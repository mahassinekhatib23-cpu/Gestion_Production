from django.contrib import admin

from .models import Article, Client, ConcerneExp, ConcerneRec, Consomme, Expedition, Fournisseur, MouvementStock, OrdreFabrication, Reception


admin.site.register(Article)
admin.site.register(Fournisseur)
admin.site.register(Client)
admin.site.register(OrdreFabrication)
admin.site.register(Reception)
admin.site.register(ConcerneRec)
admin.site.register(Expedition)
admin.site.register(ConcerneExp)
admin.site.register(MouvementStock)
admin.site.register(Consomme)
