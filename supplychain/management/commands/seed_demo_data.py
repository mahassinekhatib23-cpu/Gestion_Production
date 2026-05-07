from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from supplychain.models import (
    Article,
    Client,
    ConcerneExp,
    ConcerneRec,
    Consomme,
    Expedition,
    Fournisseur,
    MouvementStock,
    OrdreFabrication,
    Reception,
)


class Command(BaseCommand):
    help = "Injecte des donnees de test realistes (petit volume) pour l'application supply chain."

    @transaction.atomic
    def handle(self, *args, **options):
        # Reset minimal pour eviter les doublons et garder un dataset coherent.
        ConcerneExp.objects.all().delete()
        ConcerneRec.objects.all().delete()
        Consomme.objects.all().delete()
        MouvementStock.objects.all().delete()
        Expedition.objects.all().delete()
        Reception.objects.all().delete()
        OrdreFabrication.objects.all().delete()
        Article.objects.all().delete()
        Client.objects.all().delete()
        Fournisseur.objects.all().delete()

        # 5 articles (3 matieres + 2 produits finis)
        acier = Article.objects.create(
            reference="MAT-001",
            libelle="Acier Inox 304",
            type_article="Matière Première",
            stock_actuel=320,
            stock_min=120,
        )
        alu = Article.objects.create(
            reference="MAT-002",
            libelle="Aluminium Serie 6061",
            type_article="Matière Première",
            stock_actuel=250,
            stock_min=100,
        )
        vis = Article.objects.create(
            reference="MAT-003",
            libelle="Vis M8 Renforcee",
            type_article="Matière Première",
            stock_actuel=900,
            stock_min=300,
        )
        pompe = Article.objects.create(
            reference="PF-001",
            libelle="Pompe Industrielle P100",
            type_article="Produit Fini",
            stock_actuel=45,
            stock_min=20,
        )
        vanne = Article.objects.create(
            reference="PF-002",
            libelle="Vanne Haute Pression V50",
            type_article="Produit Fini",
            stock_actuel=30,
            stock_min=15,
        )

        # 5 partenaires commerciaux (3 fournisseurs + 2 clients)
        f1 = Fournisseur.objects.create(nom="MetalNord SARL")
        f2 = Fournisseur.objects.create(nom="AluTech Distribution")
        f3 = Fournisseur.objects.create(nom="Fixation Pro")

        c1 = Client.objects.create(nom="HydroBat Industrie")
        c2 = Client.objects.create(nom="Process Engineering SA")

        # 3 OF (en attente, en cours, termine)
        of1 = OrdreFabrication.objects.create(
            num_of="OF-2026001",
            article_produit=pompe,
            qte_prevue=40,
            qte_produite=0,
            date_prevue=date.today() + timedelta(days=10),
            statut="En attente",
        )
        of2 = OrdreFabrication.objects.create(
            num_of="OF-2026002",
            article_produit=vanne,
            qte_prevue=35,
            qte_produite=0,
            date_prevue=date.today() + timedelta(days=6),
            statut="En cours",
        )
        of3 = OrdreFabrication.objects.create(
            num_of="OF-2026003",
            article_produit=pompe,
            qte_prevue=20,
            qte_produite=20,
            date_prevue=date.today() - timedelta(days=7),
            date_fin=timezone.now() - timedelta(days=2),
            statut="Terminé",
            num_lot="LOT-20260505-3",
        )

        # 3 receptions
        rec1 = Reception.objects.create(num_bon_rec="REC-2026001", date_rec=date.today() - timedelta(days=8), fournisseur=f1)
        rec2 = Reception.objects.create(num_bon_rec="REC-2026002", date_rec=date.today() - timedelta(days=6), fournisseur=f2)
        rec3 = Reception.objects.create(num_bon_rec="REC-2026003", date_rec=date.today() - timedelta(days=3), fournisseur=f3)

        ConcerneRec.objects.create(reception=rec1, article=acier, qte=120)
        ConcerneRec.objects.create(reception=rec2, article=alu, qte=90)
        ConcerneRec.objects.create(reception=rec3, article=vis, qte=300)

        # 2 expeditions
        exp1 = Expedition.objects.create(num_bon_exp="EXP-2026001", date_exp=date.today() - timedelta(days=1), client=c1)
        exp2 = Expedition.objects.create(num_bon_exp="EXP-2026002", date_exp=date.today(), client=c2)

        ConcerneExp.objects.create(expedition=exp1, article=pompe, qte=10)
        ConcerneExp.objects.create(expedition=exp2, article=vanne, qte=8)

        # 3 consommations matieres
        Consomme.objects.create(article=acier, of=of2, qte_consommee=40)
        Consomme.objects.create(article=alu, of=of2, qte_consommee=28)
        Consomme.objects.create(article=vis, of=of3, qte_consommee=120)

        # 8 mouvements de stock (coherents pour test)
        MouvementStock.objects.create(type_mvt="Entrée Réception", qte=120, article=acier, rec=rec1, date_mvt=timezone.now() - timedelta(days=8))
        MouvementStock.objects.create(type_mvt="Entrée Réception", qte=90, article=alu, rec=rec2, date_mvt=timezone.now() - timedelta(days=6))
        MouvementStock.objects.create(type_mvt="Entrée Réception", qte=300, article=vis, rec=rec3, date_mvt=timezone.now() - timedelta(days=3))
        MouvementStock.objects.create(type_mvt="Sortie Production", qte=40, article=acier, of=of2, date_mvt=timezone.now() - timedelta(days=2))
        MouvementStock.objects.create(type_mvt="Sortie Production", qte=28, article=alu, of=of2, date_mvt=timezone.now() - timedelta(days=2))
        MouvementStock.objects.create(type_mvt="Sortie Production", qte=120, article=vis, of=of3, date_mvt=timezone.now() - timedelta(days=4))
        MouvementStock.objects.create(type_mvt="Sortie Expédition", qte=10, article=pompe, exp=exp1, date_mvt=timezone.now() - timedelta(days=1))
        MouvementStock.objects.create(type_mvt="Sortie Expédition", qte=8, article=vanne, exp=exp2, date_mvt=timezone.now())

        self.stdout.write(self.style.SUCCESS("Donnees de test injectees avec succes."))
        self.stdout.write("Resume:")
        self.stdout.write(f"- Articles: {Article.objects.count()}")
        self.stdout.write(f"- Fournisseurs: {Fournisseur.objects.count()}")
        self.stdout.write(f"- Clients: {Client.objects.count()}")
        self.stdout.write(f"- OF: {OrdreFabrication.objects.count()}")
        self.stdout.write(f"- Receptions: {Reception.objects.count()}")
        self.stdout.write(f"- Expeditions: {Expedition.objects.count()}")
        self.stdout.write(f"- Mouvements: {MouvementStock.objects.count()}")
