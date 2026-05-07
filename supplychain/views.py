import time

from django.contrib import messages
from django.db import transaction
from django.db.models import F
from django.shortcuts import redirect, render
from django.utils import timezone

from .forms import ConsommationForm, CreateOFForm, ExpeditionForm, MovementForm, ReceptionForm, UpdateOFStatusForm
from .models import Article, ConcerneExp, ConcerneRec, Consomme, Expedition, MouvementStock, OrdreFabrication, Reception


def dashboard(request):
    stocks = Article.objects.count()
    orders = OrdreFabrication.objects.filter(statut="En cours").count()
    movs = MouvementStock.objects.all()
    receptions = movs.filter(type_mvt__icontains="Entrée").count()
    expeditions = movs.filter(type_mvt__icontains="Sortie").count()
    return render(request, "supplychain/dashboard.html", {"stocks": stocks, "orders": orders, "receptions": receptions, "expeditions": expeditions})


def production(request):
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "create_of":
            form = CreateOFForm(request.POST)
            if form.is_valid():
                OrdreFabrication.objects.create(
                    num_of=f"OF-{int(time.time())}",
                    article_produit=form.cleaned_data["article"],
                    qte_prevue=form.cleaned_data["qte"],
                    date_prevue=form.cleaned_data["date_prevue"],
                )
                messages.success(request, "Ordre de fabrication créé.")
                return redirect("production")
        elif action == "consume":
            form = ConsommationForm(request.POST)
            if form.is_valid():
                of = form.cleaned_data["of"]
                article = form.cleaned_data["article"]
                qte = form.cleaned_data["qte"]
                if article.stock_actuel < qte:
                    messages.error(request, "Stock insuffisant pour la consommation.")
                else:
                    with transaction.atomic():
                        Consomme.objects.create(of=of, article=article, qte_consommee=qte)
                        article.stock_actuel = F("stock_actuel") - qte
                        article.save(update_fields=["stock_actuel"])
                        MouvementStock.objects.create(type_mvt="Sortie Production", qte=qte, article=article, of=of)
                    messages.success(request, "Consommation enregistrée.")
                return redirect("production")
        elif action == "status":
            of_id = request.POST.get("of_id")
            form = UpdateOFStatusForm(request.POST)
            of = OrdreFabrication.objects.get(id=of_id)
            if form.is_valid():
                new_status = form.cleaned_data["statut"]
                if new_status == "Terminé" and of.statut != "Terminé":
                    with transaction.atomic():
                        of.statut = new_status
                        of.qte_produite = of.qte_prevue
                        of.date_fin = timezone.now()
                        of.num_lot = f"LOT-{timezone.now().strftime('%Y%m%d')}-{of.id}"
                        of.save()
                        art = of.article_produit
                        art.stock_actuel = F("stock_actuel") + of.qte_prevue
                        art.save(update_fields=["stock_actuel"])
                        MouvementStock.objects.create(type_mvt="Entrée Production", qte=of.qte_prevue, article=art, of=of)
                else:
                    of.statut = new_status
                    of.save(update_fields=["statut"])
                messages.success(request, "Statut mis à jour.")
                return redirect("production")

    ofs = OrdreFabrication.objects.select_related("article_produit").order_by("-id")
    return render(
        request,
        "supplychain/production.html",
        {"ofs": ofs, "create_form": CreateOFForm(), "consume_form": ConsommationForm(), "status_form": UpdateOFStatusForm()},
    )


def reception(request):
    if request.method == "POST":
        form = ReceptionForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                rec = Reception.objects.create(
                    num_bon_rec=f"REC-{int(time.time())}",
                    date_rec=form.cleaned_data["date_rec"],
                    fournisseur=form.cleaned_data["fournisseur"],
                )
                art = form.cleaned_data["article"]
                qte = form.cleaned_data["qte"]
                ConcerneRec.objects.create(reception=rec, article=art, qte=qte)
                art.stock_actuel = F("stock_actuel") + qte
                art.save(update_fields=["stock_actuel"])
                MouvementStock.objects.create(type_mvt="Entrée Réception", qte=qte, article=art, rec=rec)
            messages.success(request, "Réception enregistrée.")
            return redirect("reception")

    rows = ConcerneRec.objects.select_related("reception", "reception__fournisseur", "article").order_by("-id")
    return render(request, "supplychain/reception.html", {"rows": rows, "form": ReceptionForm()})


def expedition(request):
    if request.method == "POST":
        form = ExpeditionForm(request.POST)
        if form.is_valid():
            art = form.cleaned_data["article"]
            qte = form.cleaned_data["qte"]
            if art.stock_actuel < qte:
                messages.error(request, "Stock insuffisant pour cette expédition.")
            else:
                with transaction.atomic():
                    exp = Expedition.objects.create(
                        num_bon_exp=f"EXP-{int(time.time())}",
                        date_exp=form.cleaned_data["date_exp"],
                        client=form.cleaned_data["client"],
                    )
                    ConcerneExp.objects.create(expedition=exp, article=art, qte=qte)
                    art.stock_actuel = F("stock_actuel") - qte
                    art.save(update_fields=["stock_actuel"])
                    MouvementStock.objects.create(type_mvt="Sortie Expédition", qte=qte, article=art, exp=exp)
                messages.success(request, "Expédition enregistrée.")
            return redirect("expedition")

    rows = ConcerneExp.objects.select_related("expedition", "expedition__client", "article").order_by("-id")
    return render(request, "supplychain/expedition.html", {"rows": rows, "form": ExpeditionForm()})


def stock(request):
    if request.method == "POST":
        form = MovementForm(request.POST)
        if form.is_valid():
            t = form.cleaned_data["type_mvt"]
            art = form.cleaned_data["article"]
            qte = form.cleaned_data["qte"]
            if "Sortie" in t and art.stock_actuel < qte:
                messages.error(request, "Stock insuffisant.")
            else:
                with transaction.atomic():
                    if "Entrée" in t:
                        art.stock_actuel = F("stock_actuel") + qte
                    else:
                        art.stock_actuel = F("stock_actuel") - qte
                    art.save(update_fields=["stock_actuel"])
                    MouvementStock.objects.create(type_mvt=t, qte=qte, article=art)
                messages.success(request, "Mouvement enregistré.")
            return redirect("stock")

    articles = Article.objects.all().order_by("libelle")
    movements = MouvementStock.objects.select_related("article").order_by("-date_mvt")[:100]
    return render(request, "supplychain/stock.html", {"articles": articles, "movements": movements, "form": MovementForm()})
