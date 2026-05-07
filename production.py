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
    QComboBox, QSpinBox, QDateEdit {
        color: #0F172A;
        border: 1px solid #CBD5E1; border-radius: 4px;
        padding: 6px 10px; background-color: #ffffff;
        font-size: 13px; min-height: 24px;
    }
    QComboBox:focus, QSpinBox:focus, QDateEdit:focus {
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

class AddOrderDialog(QDialog):
    order_created = Signal()
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Créer un Ordre de Fabrication")
        self.resize(480, 340)
        self.setModal(True)
        self.setStyleSheet(DIALOG_STYLE)
        self.setup_ui()
        self.load_products()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        
        group = QGroupBox("Détails de l'Ordre")
        form = QFormLayout(group)
        form.setLabelAlignment(Qt.AlignRight)
        form.setVerticalSpacing(15)
        
        self.cmb_article = QComboBox()
        form.addRow("Produit :", self.cmb_article)

        self.spin_qte = QSpinBox()
        self.spin_qte.setRange(1, 99999)
        form.addRow("Quantité prévue :", self.spin_qte)

        self.date_prevue = QDateEdit()
        self.date_prevue.setDate(QDate.currentDate().addDays(7))
        self.date_prevue.setCalendarPopup(True)
        self.date_prevue.setDisplayFormat("dd/MM/yyyy")
        
        cal = self.date_prevue.calendarWidget()
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
        
        form.addRow("Date de fin prévue :", self.date_prevue)
        layout.addWidget(group)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_cancel = QPushButton("✕ Annuler")
        self.btn_cancel.setObjectName("cancelButton")
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_ok = QPushButton("✓ Créer l'OF")
        self.btn_ok.setObjectName("okButton")
        self.btn_ok.clicked.connect(self.accept_order)
        
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_ok)
        layout.addLayout(btn_layout)

    def load_products(self):
        try:
            with self.db.engine.connect() as conn:
                rows = conn.execute(text("SELECT id_Article, libelle FROM Article WHERE type_Article = 'Produit Fini'")).fetchall()
                for r in rows:
                    self.cmb_article.addItem(r[1], r[0])
        except Exception as e:
            print(e)

    def accept_order(self):
        art_id = self.cmb_article.currentData()
        qte = self.spin_qte.value()
        date_str = self.date_prevue.date().toString("yyyy-MM-dd")
        num_of = f"OF-{int(time.time())}"

        try:
            with self.db.engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO Ordre_de_fabrication (num_OF, id_Article_Produit, Qte_prévue, date_prévue, statut)
                    VALUES (:num, :id_art, :qte, :date_p, 'En attente')
                """), {"num": num_of, "id_art": art_id, "qte": qte, "date_p": date_str})
            self.order_created.emit()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

class ChangeStatusDialog(QDialog):
    def __init__(self, current_status, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Changer le statut")
        self.resize(320, 200)
        self.setStyleSheet(DIALOG_STYLE)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        
        group = QGroupBox("Nouveau Statut")
        form = QFormLayout(group)
        self.cmb_status = QComboBox()
        self.cmb_status.addItems(["En attente", "En cours", "Terminé", "Annulé"])
        self.cmb_status.setCurrentText(current_status)
        form.addRow("Statut :", self.cmb_status)
        layout.addWidget(group)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_cancel = QPushButton("✕ Annuler")
        self.btn_cancel.setObjectName("cancelButton")
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_ok = QPushButton("✓ Valider")
        self.btn_ok.setObjectName("okButton")
        self.btn_ok.clicked.connect(self.accept)
        
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_ok)
        layout.addLayout(btn_layout)

    def get_new_status(self):
        return self.cmb_status.currentText()

class AddConsommationDialog(QDialog):
    consommation_added = Signal()
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Consommer Matière pour Production")
        self.resize(500, 360)
        self.setModal(True)
        self.setStyleSheet(DIALOG_STYLE)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        
        group = QGroupBox("Saisie Consommation")
        form = QFormLayout(group)
        form.setLabelAlignment(Qt.AlignRight)
        form.setVerticalSpacing(15)
        
        self.cmb_of = QComboBox()
        self.load_ofs()
        form.addRow("Ordre de Fab. :", self.cmb_of)

        self.cmb_matiere = QComboBox()
        self.load_matieres()
        form.addRow("Matière :", self.cmb_matiere)

        self.spin_qte = QSpinBox()
        self.spin_qte.setRange(1, 99999)
        form.addRow("Qté consommée :", self.spin_qte)

        layout.addWidget(group)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_cancel = QPushButton("✕ Annuler")
        self.btn_cancel.setObjectName("cancelButton")
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_ok = QPushButton("✓ Valider")
        self.btn_ok.setObjectName("okButton")
        self.btn_ok.clicked.connect(self.save_consommation)
        
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_ok)
        layout.addLayout(btn_layout)

    def load_ofs(self):
        try:
            query = text("SELECT id_OF, num_OF, statut FROM Ordre_de_fabrication WHERE statut IN ('En cours', 'En attente')")
            with self.db.engine.connect() as conn:
                for r in conn.execute(query).fetchall():
                    self.cmb_of.addItem(f"{r[1]} ({r[2]})", r[0])
        except Exception as e:
            pass

    def load_matieres(self):
        try:
            query = text("SELECT id_Article, CONCAT(reference, ' - ', libelle), stock_Actuel FROM Article WHERE type_Article = 'Matière Première'")
            with self.db.engine.connect() as conn:
                for r in conn.execute(query).fetchall():
                    self.cmb_matiere.addItem(f"{r[1]} (Stock: {r[2]})", r[0])
        except Exception as e:
            pass

    def save_consommation(self):
        id_of = self.cmb_of.currentData()
        id_art = self.cmb_matiere.currentData()
        qte = self.spin_qte.value()
        if not id_of or not id_art: return

        try:
            with self.db.engine.begin() as conn:
                conn.execute(text("INSERT INTO CONSOMME (id_Article, id_OF, Qte_consommée) VALUES (:art, :of, :qte)"), {"of": id_of, "art": id_art, "qte": qte})
                conn.execute(text("UPDATE Article SET stock_Actuel = stock_Actuel - :qte WHERE id_Article = :art"), {"qte": qte, "art": id_art})
                conn.execute(text("INSERT INTO Mouvement_Stock (type_Mvt, Qté, id_Article, id_OF, date_Mvt) VALUES ('Sortie Production', :qte, :art, :of, NOW())"), {"qte": qte, "art": id_art, "of": id_of})
            self.consommation_added.emit()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))


class ProductionWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.setWindowTitle("Gestion de la Production")
        self.resize(1200, 700)
        self.setup_ui()
        self.refresh_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(25)

        header_layout = QHBoxLayout()
        
        lbl_title = QLabel("Gestion de la Production")
        lbl_title.setStyleSheet("font-size: 28px; font-weight: 800; color: #0F172A; font-family: 'Segoe UI';")
        lbl_title.setMinimumWidth(320)
        lbl_title.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        header_layout.addWidget(lbl_title)
        
        header_layout.addStretch()

        btns_layout = QHBoxLayout()
        btns_layout.setSpacing(12) 

        btn_create = QPushButton("+ Créer OF")
        btn_create.setMinimumWidth(110)
        btn_create.setCursor(Qt.PointingHandCursor)
        btn_create.setStyleSheet("QPushButton { background-color: #10B981; color: white; padding: 10px 18px; border-radius: 6px; font-weight: bold; border: none; font-size: 13px; } QPushButton:hover { background-color: #059669; }")
        btn_create.clicked.connect(self.open_create_dialog)

        btn_conso = QPushButton("- Consommer")
        btn_conso.setMinimumWidth(120)
        btn_conso.setCursor(Qt.PointingHandCursor)
        btn_conso.setStyleSheet("QPushButton { background-color: #F59E0B; color: white; padding: 10px 18px; border-radius: 6px; font-weight: bold; border: none; font-size: 13px; } QPushButton:hover { background-color: #D97706; }")
        btn_conso.clicked.connect(self.open_conso_dialog)

        btn_status = QPushButton("✎ Modifier Statut")
        btn_status.setMinimumWidth(140)
        btn_status.setObjectName("statusButton")
        btn_status.setCursor(Qt.PointingHandCursor)
        btn_status.setStyleSheet("""
            QPushButton#statusButton {
                background-color: #64748B; color: white; padding: 10px 18px;
                border-radius: 6px; font-weight: bold; border: none; font-size: 13px;
            }
            QPushButton#statusButton:hover { background-color: #475569; }
        """)
        btn_status.clicked.connect(self.change_status)

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

        btns_layout.addWidget(btn_create)
        btns_layout.addWidget(btn_conso)
        btns_layout.addWidget(btn_status)
        btns_layout.addWidget(btn_refresh)
        btns_layout.addWidget(btn_export)

        header_layout.addLayout(btns_layout)
        main_layout.addLayout(header_layout)

        
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["N° OF", "Produit", "Qté Prévue", "Date Prévue", "Statut"])
        
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
            
            /* État survolé (corrige le gris très foncé moche de Windows) */
            QTableWidget::item:hover {
                background-color: #8fafcf;
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

    def open_create_dialog(self):
        dialog = AddOrderDialog(self.db, self)
        dialog.order_created.connect(self.refresh_data)
        dialog.exec()

    def open_conso_dialog(self):
        dialog = AddConsommationDialog(self.db, self)
        dialog.consommation_added.connect(self.refresh_data)
        dialog.exec()

    def change_status(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Attention", "Sélectionnez un ordre de fabrication dans la liste.")
            return

        num_of = self.table.item(row, 0).text()
        current_status = self.table.item(row, 4).text()

        dialog = ChangeStatusDialog(current_status, self)
        if dialog.exec():
            new_status = dialog.get_new_status()
            if new_status == current_status:
                return

            try:
                with self.db.engine.begin() as conn:
                    if new_status == "Terminé":
                        of_data = conn.execute(
                            text("SELECT id_OF, id_Article_Produit, Qte_prévue FROM Ordre_de_fabrication WHERE num_OF = :num"),
                            {"num": num_of}
                        ).fetchone()
                        
                        id_of, id_art, qte_produite = of_data[0], of_data[1], of_data[2]
                        num_lot = f"LOT-{time.strftime('%Y%m%d')}-{id_of}"

                        conn.execute(text("UPDATE Ordre_de_fabrication SET statut = :st, date_fin = NOW(), Qte_produite = :qte, num_lot = :lot WHERE num_OF = :num"), {"st": new_status, "qte": qte_produite, "lot": num_lot, "num": num_of})
                        conn.execute(text("UPDATE Article SET stock_Actuel = stock_Actuel + :qte WHERE id_Article = :id_art"), {"qte": qte_produite, "id_art": id_art})
                        conn.execute(text("INSERT INTO Mouvement_Stock (type_Mvt, Qté, id_Article, id_OF, date_Mvt) VALUES ('Entrée Production', :qte, :id_art, :id_of, NOW())"), {"qte": qte_produite, "id_art": id_art, "id_of": id_of})
                        QMessageBox.information(self, "Succès", f"OF Clôturé ! Lot {num_lot} généré. Stock mis à jour.")
                    else:
                        conn.execute(text("UPDATE Ordre_de_fabrication SET statut = :st WHERE num_OF = :num"), {"st": new_status, "num": num_of})
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(self, "Erreur SQL", str(e))

    def export_data(self):
        try:
            data = []
            for row in range(self.table.rowCount()):
                row_data = []
                for col in range(5):
                    item = self.table.item(row, col)
                    row_data.append(item.text() if item else "")
                data.append(row_data)

            import pandas as pd
            df = pd.DataFrame(data, columns=["N° OF", "Produit", "Qté Prévue", "Date Prévue", "Statut"])

            file_name, _ = QFileDialog.getSaveFileName(
                self, "Exporter Excel",
                f"ordres_fabrication_{QDate.currentDate().toString('yyyyMMdd')}.xlsx",
                "Excel Files (*.xlsx)"
            )
            if file_name:
                df.to_excel(file_name, index=False)
                QMessageBox.information(self, "Export réussi", f"Fichier sauvegardé :\n{file_name}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Échec de l'export : {str(e)}")

    def refresh_data(self):
        try:
            orders = self.db.get_all_orders()
            self.table.setRowCount(len(orders))
            for i, o in enumerate(orders):
                
                vals = [str(o['num_OF']), str(o['libelle']), str(o['Qte_prévue']), str(o['date_prévue'])]
                for col, v in enumerate(vals):
                    item = QTableWidgetItem(v)
                    item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(i, col, item)

                item_statut = QTableWidgetItem(o['statut'])
                item_statut.setTextAlignment(Qt.AlignCenter)
                item_statut.setFont(QFont("Segoe UI", 10, QFont.Bold))

                if o['statut'] == "En cours": item_statut.setForeground(QColor("#F59E0B"))
                elif o['statut'] == "Terminé": item_statut.setForeground(QColor("#10B981"))
                elif o['statut'] == "Annulé": item_statut.setForeground(QColor("#EF4444"))
                else: item_statut.setForeground(QColor("#64748B"))

                self.table.setItem(i, 4, item_statut)
            
            maintenant = QDateTime.currentDateTime().toString('dd/MM/yyyy à HH:mm:ss')
            self.status_label.setText(f"Dernière mise à jour : {maintenant}")
            
        except Exception as e:
            print(e)
            self.status_label.setText("Erreur de chargement")
            
            self.status_label.setText(f"Dernière mise à jour : {QDate.currentDate().toString('dd/MM/yyyy')}")
        except Exception as e:
            print(e)
            self.status_label.setText("Erreur de chargement")