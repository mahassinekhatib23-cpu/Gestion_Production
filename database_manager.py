from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import os
import urllib.parse

class DatabaseManager:
    def __init__(self):
        # --- CONFIGURATION DE LA CONNEXION ---
        USER = "root"
        RAW_PASSWORD = os.getenv("DB_PASSWORD", "")
        PASSWORD = urllib.parse.quote_plus(RAW_PASSWORD)
        HOST = "localhost"
        PORT = 3306
        DB_NAME = "gestion_production"

        self.db_url = f"mysql+pymysql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}?charset=utf8mb4"
        self.engine = None

        try:
            self.engine = create_engine(self.db_url, echo=False, pool_pre_ping=True)
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("✅ Connexion MySQL réussie")
        except Exception as e:
            print(f"❌ Erreur connexion MySQL : {e}")

    def get_stock_status(self):
        """Récupère l'état des stocks sous forme de dictionnaire"""
        query = text("SELECT reference, libelle, type_Article, stock_Actuel, stock_min FROM Article")
        try:
            with self.engine.connect() as conn:
                # .mappings() 
                return conn.execute(query).mappings().fetchall()
        except SQLAlchemyError as e:
            print(f"❌ Erreur SQL (stock) : {e}")
            return []

    def get_movement_history(self):
        query = text("""
            SELECT m.date_Mvt, m.type_Mvt, a.libelle, m.Qté 
            FROM Mouvement_Stock m 
            JOIN Article a ON m.id_Article = a.id_Article 
            ORDER BY m.date_Mvt DESC
        """)
        try:
            with self.engine.connect() as conn:
                return conn.execute(query).mappings().fetchall()
        except SQLAlchemyError as e:
            print(f"❌ Erreur SQL (mouvements) : {e}")
            return []

    def get_all_orders(self):
        query = text("""
            SELECT o.num_OF, a.libelle, o.Qte_prévue, o.statut, o.date_prévue 
            FROM Ordre_de_fabrication o 
            JOIN Article a ON o.id_Article_Produit = a.id_Article
        """)
        try:
            with self.engine.connect() as conn:
                return conn.execute(query).mappings().fetchall()
        except SQLAlchemyError as e:
            print(f"❌ Erreur SQL (OF) : {e}")
            return []