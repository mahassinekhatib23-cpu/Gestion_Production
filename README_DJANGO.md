# Migration vers Django (SQLite)

Ce dossier contient maintenant une version Django du projet, en conservant les memes modules fonctionnels:

- Accueil
- Production
- Chargement (Receptions)
- Dechargement (Expeditions)
- Stocks

## 1) Installation

```bash
python -m pip install -r requirements.txt
```

## 2) Initialisation de la base SQLite

```bash
python manage.py makemigrations supplychain
python manage.py migrate
```

La base est creee ici:

- `db.sqlite3`

## 3) Lancer l'application

```bash
python manage.py runserver
```

Puis ouvrir:

- `http://127.0.0.1:8000/`

## 4) Ouvrir le fichier SQLite

Tu peux ouvrir `db.sqlite3` avec:

- **DB Browser for SQLite**: `Open Database` puis selectionner `db.sqlite3`
- **DBeaver**: nouvelle connexion SQLite puis choisir `db.sqlite3`
- **VS Code extension SQLite**: ouvrir la base depuis l'explorateur

## 5) Notes importantes

- L'ancienne application desktop PySide6 est conservee dans les fichiers Python existants.
- La nouvelle version web Django est operationnelle avec SQLite.
