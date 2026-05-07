import time
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QAbstractItemView, QDialog, QGroupBox,
    QFormLayout, QComboBox, QSpinBox, QDateEdit, QMessageBox, QLabel, QFileDialog, QSizePolicy
)
from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtCore import Qt, QDate, QDateTime, Signal
from sqlalchemy import text

from database_manager import DatabaseManager

DIALOG_STYLE = """
    QDialog { background-color: #ffffff; }
    QGroupBox {
        font-weight: 600; font-size: 13px;
        border: 1px solid #E2E8F0; border-radius: 6px;
        margin-top: 15px; padding-top: 15px;
        background-color: #F8FAFC;
    }
    QGroupBox::title {
        subcontrol-origin: margin; left: 10px; padding: 0 5px;
        color: #0F172A;
    }
    QLabel { color: #334155; font-size: 12px; font-weight: 500;}
    QComboBox, QSpinBox, QDateEdit, QTextEdit {
        color: #0F172A;
        border: 1px solid #CBD5E1; border-radius: 4px;
        padding: 6px 10px; background-color: #ffffff;
        font-size: 13px; min-height: 24px;
    }
    QComboBox:focus, QSpinBox:focus, QDateEdit:focus, QTextEdit:focus {
        border: 1px solid #3B82F6; outline: none;
    }
    QComboBox::drop-down, QDateEdit::drop-down {
        border: none; width: 24px;
    }
    QComboBox::down-arrow, QDateEdit::down-arrow {
        image: none; border-top: 5px solid #64748B;
        border-left: 4px solid transparent; border-right: 4px solid transparent;
        border-bottom: none; width: 0; height: 0;
    }
    QSpinBox::up-button, QSpinBox::down-button { border: none; background: transparent; }
    QPushButton {
        border: none; border-radius: 6px;
        padding: 10px 20px; font-weight: bold; font-size: 13px;
        background-color: #F1F5F9; color: #334155;
    }
    QPushButton:hover { background-color: #E2E8F0; }
    QPushButton#okButton { background-color: #10B981; color: white; }
    QPushButton#okButton:hover { background-color: #059669; }
    QPushButton#cancelButton { background-color: #F1F5F9; color: #334155; }
    QPushButton#cancelButton:hover { background-color: #E2E8F0; }
"""


class AddReceptionDialog(QDialog):
    reception_added = Signal()

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Nouvelle Réception (Achat)")
        self.resize(500, 420)
        self.setModal(True)
        self.setStyleSheet(DIALOG_STYLE)
        self.setup_ui()
        self.load_fournisseurs()
        self.load_articles()
        self.update_stock_info()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)

        group = QGroupBox("Détails du Bon de Réception")
        form = QFormLayout(group)
        form.setLabelAlignment(Qt.AlignRight)
        form.setVerticalSpacing(15)

        # Fournisseur
        self.cmb_fournisseur = QComboBox()
        self.cmb_fournisseur.setEditable(True)
        self.cmb_fournisseur.setInsertPolicy(QComboBox.NoInsert)
        form.addRow("Fournisseur :", self.cmb_fournisseur)

        # Article à recevoir
        self.cmb_article = QComboBox()
        self.cmb_article.setEditable(True)
        self.cmb_article.setInsertPolicy(QComboBox.NoInsert)
        self.cmb_article.currentIndexChanged.connect(self.update_stock_info)
        form.addRow("Article :", self.cmb_article)

        # Stock actuel 
        self.lbl_stock = QLabel("—")
        self.lbl_stock.setStyleSheet("color: #64748B; font-style: italic;")
        form.addRow("Stock actuel :", self.lbl_stock)

        # Quantité
        self.spin_qte = QSpinBox()
        self.spin_qte.setRange(1, 999999)
        self.spin_qte.setSuffix(" unités")
        form.addRow("Quantité :", self.spin_qte)

        self.date_rec = QDateEdit()
        self.date_rec.setDate(QDate.currentDate())
        self.date_rec.setCalendarPopup(True)
        self.date_rec.setDisplayFormat("dd/MM/yyyy")

        cal = self.date_rec.calendarWidget()
        cal.setStyleSheet("""
            QCalendarWidget { background-color: white; color: black; }
            QCalendarWidget QAbstractItemView:enabled {
                color: black; background-color: white;
                selection-background-color: #3B82F6; selection-color: white;
            }
            QCalendarWidget QWidget#qt_calendar_navigationbar { background-color: #F8FAFC; color: black; }
            QCalendarWidget QToolButton { color: black; background-color: transparent; font-weight: bold; }
            QCalendarWidget QMenu { color: black; background-color: white; }
        """)

        form.addRow("Date réception :", self.date_rec)
        layout.addWidget(group)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_cancel = QPushButton("✕ Annuler")
        self.btn_cancel.setObjectName("cancelButton")
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_ok = QPushButton("✓ Confirmer")
        self.btn_ok.setObjectName("okButton")
        self.btn_ok.clicked.connect(self.accept_reception)

        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_ok)
        layout.addLayout(btn_layout)

    def load_fournisseurs(self):
        """Charge la liste des fournisseurs"""
        try:
            query = text("SELECT id_Fournisseur, Nom FROM Fournisseur ORDER BY Nom")
            with self.db.engine.connect() as conn:
                rows = conn.execute(query).fetchall()
                self.cmb_fournisseur.clear()
                for r in rows:
                    self.cmb_fournisseur.addItem(str(r[1]), r[0])
        except Exception as e:
            print(f"Erreur chargement fournisseurs: {e}")

    def load_articles(self):
        """Charge la liste des articles (tous types)"""
        try:
            query = text("""
                SELECT id_Article, CONCAT(reference, ' - ', libelle) AS display, stock_Actuel
                FROM Article
                ORDER BY libelle
            """)
            with self.db.engine.connect() as conn:
                rows = conn.execute(query).fetchall()
                self.cmb_article.clear()
                for r in rows:
                    self.cmb_article.addItem(r[1], r[0])
        except Exception as e:
            print(f"Erreur chargement articles: {e}")

    def update_stock_info(self):
        """Affiche le stock de l'article sélectionné"""
        art_id = self.cmb_article.currentData()
        if not art_id:
            self.lbl_stock.setText("—")
            return
        try:
            with self.db.engine.connect() as conn:
                res = conn.execute(
                    text("SELECT stock_Actuel FROM Article WHERE id_Article = :id"),
                    {"id": art_id}
                ).fetchone()
                stock = res[0] if res else 0
                self.lbl_stock.setText(f"{stock} unités")
        except:
            self.lbl_stock.setText("erreur")

    def accept_reception(self):
        """Valide et enregistre la réception"""
        id_fourn = self.cmb_fournisseur.currentData()
        id_art = self.cmb_article.currentData()
        qte = self.spin_qte.value()

        if not id_fourn or not id_art:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un fournisseur et un article.")
            return

        # Génération d'un numéro de bon unique
        num_bon = f"REC-{int(time.time())}"
        date_str = self.date_rec.date().toString("yyyy-MM-dd")

        try:
            with self.db.engine.begin() as conn:
                #  Créer la réception
                conn.execute(
                    text("""
                        INSERT INTO Reception (num_bon_rec, date_Rec, id_Fournisseur)
                        VALUES (:num, :date_rec, :fid)
                    """),
                    {"num": num_bon, "date_rec": date_str, "fid": id_fourn}
                )

                # Récupérer l'ID généré
                id_rec = conn.execute(
                    text("SELECT id_Rec FROM Reception WHERE num_bon_rec = :num"),
                    {"num": num_bon}
                ).scalar()

                #  Lier l'article (table CONCERNE_REC)
                conn.execute(
                    text("""
                        INSERT INTO CONCERNE_REC (id_Article, id_Rec, Qte)
                        VALUES (:aid, :rid, :qte)
                    """),
                    {"aid": id_art, "rid": id_rec, "qte": qte}
                )

                #  Mettre à jour le stock
                conn.execute(
                    text("UPDATE Article SET stock_Actuel = stock_Actuel + :qte WHERE id_Article = :aid"),
                    {"qte": qte, "aid": id_art}
                )

                # Enregistrer le mouvement de stock
                conn.execute(
                    text("""
                        INSERT INTO Mouvement_Stock (type_Mvt, Qté, id_Article, id_Rec, date_Mvt)
                        VALUES ('Entrée Réception', :qte, :aid, :rid, NOW())
                    """),
                    {"qte": qte, "aid": id_art, "rid": id_rec}
                )

            QMessageBox.information(self, "Succès", f"Réception {num_bon} enregistrée.")
            self.reception_added.emit()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur base de données : {str(e)}")



class ReceptionWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.setWindowTitle("Module de Chargement (Réception)")
        self.resize(1200, 700)
        self.setup_ui()
        self.refresh_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(25)

        header_layout = QHBoxLayout()
        
        lbl_title = QLabel("Gestion des Réceptions")
        lbl_title.setStyleSheet("font-size: 28px; font-weight: 800; color: #0F172A; font-family: 'Segoe UI';")
        lbl_title.setMinimumWidth(340) 
        lbl_title.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        header_layout.addWidget(lbl_title)
        
        header_layout.addStretch()

        btns_layout = QHBoxLayout()
        btns_layout.setSpacing(12) 

        btn_add = QPushButton("+ Nouvelle Réception")
        btn_add.setMinimumWidth(170)
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.setStyleSheet("QPushButton { background-color: #10B981; color: white; padding: 10px 18px; border-radius: 6px; font-weight: bold; border: none; font-size: 13px; } QPushButton:hover { background-color: #059669; }")
        btn_add.clicked.connect(self.open_add_dialog)

        btn_refresh = QPushButton("⟳ Actualiser")
        btn_refresh.setMinimumWidth(120)
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.setStyleSheet("QPushButton { background-color: #1E293B; color: white; padding: 10px 18px; border-radius: 6px; font-weight: bold; border: none; font-size: 13px; } QPushButton:hover { background-color: #0F172A; }")
        btn_refresh.clicked.connect(self.refresh_data)

        btn_export = QPushButton("⤓ Exporter Excel")
        btn_export.setMinimumWidth(140)
        btn_export.setCursor(Qt.PointingHandCursor)
        btn_export.setStyleSheet("QPushButton { background-color: #1E293B; color: white; padding: 10px 18px; border-radius: 6px; font-weight: bold; border: none; font-size: 13px; } QPushButton:hover { background-color: #0F172A; }")
        btn_export.clicked.connect(self.export_data)

        btns_layout.addWidget(btn_add)
        btns_layout.addWidget(btn_refresh)
        btns_layout.addWidget(btn_export)

        header_layout.addLayout(btns_layout)
        main_layout.addLayout(header_layout)

       
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["N° Bon", "Date", "Fournisseur", "Article", "Quantité"])
        
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(50) 
        
        
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setFocusPolicy(Qt.NoFocus)
        
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white; 
                alternate-background-color: #F8FAFC;
                gridline-color: #E2E8F0;
                border: 1px solid #CBD5E1; 
                border-radius: 8px;
                font-family: 'Segoe UI';
                font-size: 14px;
                color: #334155;
            }
            QHeaderView::section {
                background-color: #1E293B; 
                color: #F8FAFC; 
                padding: 12px;
                font-weight: 600; font-size: 13px;
                border: none; 
                border-right: 1px solid #334155;
            }
            QHeaderView::section:last { border-right: none; }
            
            /* État sélectionné */
            QTableWidget::item:selected {
                background-color: #E0F2FE;
                color: #0F172A;
                font-weight: bold;
            }
            
            /* État survolé */
            QTableWidget::item:hover {
                background-color: #F1F5F9;
                color: #0F172A;
            }
            
            /* État survolé QUAND il est déjà sélectionné */
            QTableWidget::item:selected:hover {
                background-color: #BAE6FD;
                color: #0F172A;
            }
            
            /* Scrollbar style moderne */
            QScrollBar:vertical {
                border: none; background: #F1F5F9; width: 10px; border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #CBD5E1; min-height: 20px; border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover { background: #94A3B8; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { border: none; background: none; }
        """)

        main_layout.addWidget(self.table)

        
        self.status_label = QLabel("Prêt")
        self.status_label.setStyleSheet("color: #64748B; font-size: 12px; font-weight: 500;")
        main_layout.addWidget(self.status_label)

    def open_add_dialog(self):
        dialog = AddReceptionDialog(self.db, self)
        dialog.reception_added.connect(self.refresh_data)
        dialog.exec()

    def export_data(self):
        """Exporte les données des réceptions vers un fichier Excel"""
        try:
            data = []
            for row in range(self.table.rowCount()):
                row_data = []
                for col in range(5):
                    item = self.table.item(row, col)
                    row_data.append(item.text() if item else "")
                data.append(row_data)

            import pandas as pd
            df = pd.DataFrame(data, columns=["N° Bon", "Date", "Fournisseur", "Article", "Quantité"])

            file_name, _ = QFileDialog.getSaveFileName(
                self, "Exporter Excel",
                f"receptions_{QDate.currentDate().toString('yyyyMMdd')}.xlsx",
                "Excel Files (*.xlsx)"
            )
            if file_name:
                df.to_excel(file_name, index=False)
                QMessageBox.information(self, "Export réussi", f"Fichier sauvegardé :\n{file_name}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Échec de l'export : {str(e)}")

    def refresh_data(self):
        """Charge et affiche les réceptions depuis la base"""
        try:
            query = text("""
                SELECT r.num_bon_rec, r.date_Rec, f.Nom, a.libelle, cr.Qte
                FROM Reception r
                JOIN Fournisseur f ON r.id_Fournisseur = f.id_Fournisseur
                JOIN CONCERNE_REC cr ON r.id_Rec = cr.id_Rec
                JOIN Article a ON cr.id_Article = a.id_Article
                ORDER BY r.date_Rec DESC
            """)

            with self.db.engine.connect() as conn:
                rows = conn.execute(query).fetchall()

            self.table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                for col, val in enumerate(row[:4]):
                    item = QTableWidgetItem(str(val))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(i, col, item)

                qte_item = QTableWidgetItem(f"+ {row[4]}")
                qte_item.setTextAlignment(Qt.AlignCenter)
                qte_item.setForeground(QColor("#10B981"))  
                qte_item.setFont(QFont("Segoe UI", 10, QFont.Bold))
                self.table.setItem(i, 4, qte_item)
            maintenant = QDateTime.currentDateTime().toString('dd/MM/yyyy à HH:mm:ss')
            self.status_label.setText(f"Dernière mise à jour : {maintenant}")
        except Exception as e:
            print(f"Erreur refresh réceptions : {e}")
            self.status_label.setText("Erreur de chargement")