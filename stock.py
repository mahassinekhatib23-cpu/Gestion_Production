import sys
import textwrap
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QTableWidget, QTableWidgetItem, QLabel, QFrame, 
                             QHeaderView, QPushButton, QMessageBox, QTabWidget,
                             QComboBox, QLineEdit, QDateEdit, QFormLayout, QGroupBox,
                             QTextEdit, QSpinBox, QDialog, QFileDialog, QAbstractItemView, QSizePolicy)
from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtCore import Qt, QDate, Signal

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from database_manager import DatabaseManager

DIALOG_STYLE = """
    QDialog { background-color: #ffffff; font-family: 'Segoe UI'; }
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
    QComboBox::drop-down, QDateEdit::drop-down { border: none; width: 24px; }
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

TABLE_STYLE = """
    QTableWidget {
        background-color: white; 
        alternate-background-color: #F8FAFC;
        gridline-color: #E2E8F0;
        border: none; 
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
    
    QTableWidget::item:selected { background-color: #E0F2FE; color: #0F172A; font-weight: bold; }
    QTableWidget::item:hover { background-color: #F1F5F9; color: #0F172A; }
    QTableWidget::item:selected:hover { background-color: #BAE6FD; color: #0F172A; }
    
    QScrollBar:vertical { border: none; background: #F1F5F9; width: 10px; border-radius: 5px; }
    QScrollBar::handle:vertical { background: #CBD5E1; min-height: 20px; border-radius: 5px; }
    QScrollBar::handle:vertical:hover { background: #94A3B8; }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { border: none; background: none; }
"""

class AddMovementDialog(QDialog):
    movement_added = Signal()
    
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Ajouter un mouvement de stock")
        self.resize(450, 400)
        self.setStyleSheet(DIALOG_STYLE)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        
        form_group = QGroupBox("Détails du mouvement")
        form_layout = QFormLayout(form_group)
        form_layout.setLabelAlignment(Qt.AlignRight)
        form_layout.setVerticalSpacing(15)
        
        self.cmb_type = QComboBox()
        self.cmb_type.addItems(['Entrée Réception', 'Sortie Production', 'Entrée Production', 'Sortie Expédition'])
        form_layout.addRow("Type d'opération:", self.cmb_type)
        
        self.cmb_article = QComboBox()
        self.load_articles()
        form_layout.addRow("Article concerné:", self.cmb_article)
        
        self.spn_quantite = QSpinBox()
        self.spn_quantite.setMinimum(1)
        self.spn_quantite.setMaximum(10000)
        form_layout.addRow("Quantité:", self.spn_quantite)
        
        self.txt_commentaire = QTextEdit()
        self.txt_commentaire.setMaximumHeight(50)
        self.txt_commentaire.setPlaceholderText("Optionnel: n° de lot, référence...")
        form_layout.addRow("Commentaire:", self.txt_commentaire)
        
        self.date_mvt = QDateEdit()
        self.date_mvt.setDate(QDate.currentDate())
        self.date_mvt.setCalendarPopup(True)
        self.date_mvt.setDisplayFormat("dd/MM/yyyy")
        
        cal = self.date_mvt.calendarWidget()
        cal.setStyleSheet("""
            QCalendarWidget { background-color: white; color: black; }
            QCalendarWidget QAbstractItemView:enabled { color: black; background-color: white; selection-background-color: #3B82F6; selection-color: white; }
            QCalendarWidget QWidget#qt_calendar_navigationbar { background-color: #F8FAFC; color: black; }
            QCalendarWidget QToolButton { color: black; background-color: transparent; font-weight: bold; }
            QCalendarWidget QMenu { color: black; background-color: white; }
        """)
        
        form_layout.addRow("Date du mouvement:", self.date_mvt)
        
        layout.addWidget(form_group)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_cancel = QPushButton("✕ Annuler")
        self.btn_cancel.setObjectName("cancelButton")
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_ok = QPushButton("✓ Valider")
        self.btn_ok.setObjectName("okButton")
        self.btn_ok.clicked.connect(self.accept_movement)
        
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_ok)
        layout.addLayout(btn_layout)
    
    def load_articles(self):
        try:
            query = text("SELECT id_Article, libelle FROM Article ORDER BY libelle")
            with self.db.engine.connect() as conn:
                articles = conn.execute(query).fetchall()
                self.cmb_article.clear()
                for art in articles:
                    self.cmb_article.addItem(str(art[1]), art[0]) 
        except Exception as e:
            print(f"Erreur chargement articles: {e}")
    
    def accept_movement(self):
        try:
            article_id = self.cmb_article.currentData()
            type_mvt = self.cmb_type.currentText()
            quantite = self.spn_quantite.value()
            date_str = self.date_mvt.date().toString("yyyy-MM-dd")
            
            if not article_id:
                QMessageBox.warning(self, "Attention", "Veuillez sélectionner un article")
                return
            
            if type_mvt in ['Sortie Production', 'Sortie Expédition']:
                with self.db.engine.connect() as conn:
                    res = conn.execute(text("SELECT stock_Actuel FROM Article WHERE id_Article = :id"), {"id": article_id}).fetchone()
                    stock_actuel = res[0] if res else 0
                
                if stock_actuel < quantite:
                    QMessageBox.warning(self, "Stock Insuffisant", f"Opération impossible !\n\nVous essayez de sortir : {quantite}\nStock disponible : {stock_actuel}")
                    return

            query_insert = text("INSERT INTO Mouvement_Stock (type_Mvt, Qté, id_Article, date_Mvt) VALUES (:type, :qte, :article, :date_mvt)")
            
            if type_mvt in ['Entrée Réception', 'Entrée Production']:
                query_update = text("UPDATE Article SET stock_Actuel = stock_Actuel + :qte WHERE id_Article = :article")
            else:
                query_update = text("UPDATE Article SET stock_Actuel = stock_Actuel - :qte WHERE id_Article = :article")

            with self.db.engine.begin() as conn:
                conn.execute(query_insert, {"type": type_mvt, "qte": quantite, "article": article_id, "date_mvt": date_str})
                conn.execute(query_update, {"qte": quantite, "article": article_id})
            
            QMessageBox.information(self, "Succès", "Mouvement enregistré et stock mis à jour !")
            self.movement_added.emit()
            self.accept()
            
        except SQLAlchemyError as e:
            QMessageBox.critical(self, "Erreur Base de Données", f"Détail : {str(e)}")


class StockManagementWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.setWindowTitle("ERP PRO - Gestion des Stocks")
        self.resize(1400, 850)
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        self.setStyleSheet("""
            QWidget { background-color: #F8FAFC; font-family: 'Segoe UI', sans-serif; }
            QTabWidget::pane { border: 1px solid #CBD5E1; background-color: white; border-radius: 8px; border-top-left-radius: 0px; }
            QTabBar::tab { background-color: #E2E8F0; padding: 12px 25px; margin-right: 4px; border-top-left-radius: 6px; border-top-right-radius: 6px; color: #475569; font-weight: 600; font-size: 13px; }
            QTabBar::tab:selected { background-color: white; border-bottom: 3px solid #3B82F6; color: #0F172A; font-weight: bold; }
            QTabBar::tab:hover:!selected { background-color: #CBD5E1; }
            QComboBox { border: 1px solid #CBD5E1; border-radius: 4px; padding: 6px 10px; background-color: white; font-size: 13px; min-width: 150px; }
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(25)
        
        header_layout = QHBoxLayout()
        lbl_title = QLabel("Gestion des Stocks")
        lbl_title.setStyleSheet("font-size: 28px; font-weight: 800; color: #0F172A;")
        lbl_title.setMinimumWidth(300)
        lbl_title.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        header_layout.addWidget(lbl_title)
        
        header_layout.addStretch()
        
        btns_layout = QHBoxLayout()
        btns_layout.setSpacing(12)
        
        self.btn_add_movement = QPushButton("+ Nouveau Mouvement")
        self.btn_add_movement.setCursor(Qt.PointingHandCursor)
        self.btn_add_movement.setStyleSheet("QPushButton { background-color: #10B981; color: white; padding: 10px 18px; border-radius: 6px; font-weight: bold; border: none; font-size: 13px; } QPushButton:hover { background-color: #059669; }")
        self.btn_add_movement.clicked.connect(self.open_add_movement_dialog)
        
        self.btn_refresh = QPushButton("⟳ Actualiser")
        self.btn_refresh.setCursor(Qt.PointingHandCursor)
        self.btn_refresh.setStyleSheet("QPushButton { background-color: #1E293B; color: white; padding: 10px 18px; border-radius: 6px; font-weight: bold; border: none; font-size: 13px; } QPushButton:hover { background-color: #0F172A; }")
        self.btn_refresh.clicked.connect(self.load_data)
        
        self.btn_export = QPushButton("⤓ Exporter Excel")
        self.btn_export.setCursor(Qt.PointingHandCursor)
        self.btn_export.setStyleSheet("QPushButton { background-color: #1E293B; color: white; padding: 10px 18px; border-radius: 6px; font-weight: bold; border: none; font-size: 13px; } QPushButton:hover { background-color: #0F172A; }")
        self.btn_export.clicked.connect(self.export_excel)

        self.btn_export_pdf = QPushButton("📄 Exporter PDF")
        self.btn_export_pdf.setCursor(Qt.PointingHandCursor)
        self.btn_export_pdf.setStyleSheet("QPushButton { background-color: #EF4444; color: white; padding: 10px 18px; border-radius: 6px; font-weight: bold; border: none; font-size: 13px; } QPushButton:hover { background-color: #DC2626; }")
        self.btn_export_pdf.clicked.connect(self.export_pdf)
        
        btns_layout.addWidget(self.btn_add_movement)
        btns_layout.addWidget(self.btn_refresh)
        btns_layout.addWidget(self.btn_export)
        btns_layout.addWidget(self.btn_export_pdf) 
        
        header_layout.addLayout(btns_layout)
        main_layout.addLayout(header_layout)
        
        self.tabs = QTabWidget()
        
        self.tab_stock = QWidget()
        self.setup_stock_tab()
        self.tabs.addTab(self.tab_stock, "État des Stocks")
        
        self.tab_movements = QWidget()
        self.setup_movements_tab()
        self.tabs.addTab(self.tab_movements, "Historique Mouvements")
        
        self.tab_charts = QWidget()
        self.setup_charts_tab()
        self.tabs.addTab(self.tab_charts, "Statistiques Visuelles")
        
        self.tab_orders = QWidget()
        self.setup_orders_tab()
        self.tabs.addTab(self.tab_orders, "Ordres de Fabrication liés")
        
        main_layout.addWidget(self.tabs)
        
        self.status_label = QLabel("Prêt")
        self.status_label.setStyleSheet("color: #64748B; font-size: 12px; font-weight: 500;")
        main_layout.addWidget(self.status_label)
    
    def apply_table_settings(self, table):
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(50)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setFocusPolicy(Qt.NoFocus)
        table.setStyleSheet(TABLE_STYLE)

    def setup_stock_tab(self):
        layout = QVBoxLayout(self.tab_stock)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        filter_layout = QHBoxLayout()
        lbl_filter = QLabel("Filtrer par type :")
        lbl_filter.setStyleSheet("font-weight: bold; color: #334155; font-size: 13px;")
        filter_layout.addWidget(lbl_filter)
        
        self.cmb_type_filter = QComboBox()
        self.cmb_type_filter.addItems(["Tous", "Matière Première", "Produit Fini"])
        self.cmb_type_filter.currentTextChanged.connect(self.load_data)
        filter_layout.addWidget(self.cmb_type_filter)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        self.table_stock = QTableWidget(0, 7)
        self.table_stock.setHorizontalHeaderLabels(["Référence", "Libellé", "Type", "Stock actuel", "Stock min", "Statut", "Différence"])
        self.apply_table_settings(self.table_stock)
        layout.addWidget(self.table_stock)
        
        summary_layout = QHBoxLayout()
        self.lbl_total = QLabel("Articles: 0")
        self.lbl_critical = QLabel("Critiques: 0")
        self.lbl_normal = QLabel("Normaux: 0")
        
        for lbl in [self.lbl_total, self.lbl_critical, self.lbl_normal]:
            lbl.setStyleSheet("background-color: #F1F5F9; border: 1px solid #E2E8F0; padding: 8px 15px; border-radius: 6px; font-weight: bold; color: #334155;")
            summary_layout.addWidget(lbl)
        
        summary_layout.addStretch()
        layout.addLayout(summary_layout)
    
    def setup_movements_tab(self):
        layout = QVBoxLayout(self.tab_movements)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        filter_layout = QHBoxLayout()
        lbl_filter = QLabel("Type de mouvement :")
        lbl_filter.setStyleSheet("font-weight: bold; color: #334155; font-size: 13px;")
        filter_layout.addWidget(lbl_filter)
        
        self.cmb_movement_type = QComboBox()
        self.cmb_movement_type.addItems(["Tous", "Entrée Réception", "Sortie Production", "Entrée Production", "Sortie Expédition"])
        self.cmb_movement_type.currentTextChanged.connect(self.load_movements)
        filter_layout.addWidget(self.cmb_movement_type)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        self.table_movements = QTableWidget(0, 5)
        self.table_movements.setHorizontalHeaderLabels(["Date", "Type", "Article", "Quantité", "Info"])
        self.apply_table_settings(self.table_movements)
        layout.addWidget(self.table_movements)
    
    def setup_charts_tab(self):
        layout = QHBoxLayout(self.tab_charts)
        layout.setContentsMargins(20, 20, 20, 20)
        self.figure, (self.ax1, self.ax2) = plt.subplots(1, 2, figsize=(10, 5))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
    
    def setup_orders_tab(self):
        layout = QVBoxLayout(self.tab_orders)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.table_orders = QTableWidget(0, 6)
        self.table_orders.setHorizontalHeaderLabels(["Num OF", "Produit", "Qté Prévue", "Statut", "Date Prévue", "Qté Produite"])
        self.apply_table_settings(self.table_orders)
        layout.addWidget(self.table_orders)
    
    def load_data(self):
        try:
            stocks = self.db.get_stock_status()
            type_filter = self.cmb_type_filter.currentText()
            filtered_stocks = [s for s in stocks if type_filter == "Tous" or s['type_Article'] == type_filter]
            
            self.table_stock.setRowCount(len(filtered_stocks))
            critique = 0; normal = 0
            
            for i, stock in enumerate(filtered_stocks):
                s_actuel = stock['stock_Actuel'] or 0
                s_min = stock['stock_min'] or 0
                
                if s_actuel <= s_min:
                    statut, color_statut = "CRITIQUE", "#EF4444"
                    critique += 1
                else:
                    statut, color_statut = "NORMAL", "#10B981"
                    normal += 1
                
                diff = s_actuel - s_min
                
                vals = [str(stock['reference']), str(stock['libelle']), str(stock['type_Article']), str(s_actuel), str(s_min)]
                for col_idx, val in enumerate(vals):
                    item = QTableWidgetItem(val)
                    item.setTextAlignment(Qt.AlignCenter)
                    self.table_stock.setItem(i, col_idx, item)
                
                item_statut = QTableWidgetItem(statut)
                item_statut.setForeground(QColor(color_statut))
                item_statut.setFont(QFont("Segoe UI", 10, QFont.Bold))
                item_statut.setTextAlignment(Qt.AlignCenter)
                self.table_stock.setItem(i, 5, item_statut)
                
                item_diff = QTableWidgetItem(f"{diff:+d}")
                item_diff.setForeground(QColor(color_statut))
                item_diff.setFont(QFont("Segoe UI", 10, QFont.Bold))
                item_diff.setTextAlignment(Qt.AlignCenter)
                self.table_stock.setItem(i, 6, item_diff)
            
            self.lbl_total.setText(f"Articles: {len(filtered_stocks)}")
            self.lbl_critical.setText(f"Critiques: {critique}")
            self.lbl_normal.setText(f"Normaux: {normal}")
            
            self.load_movements()
            self.load_orders()
            self.update_charts(filtered_stocks)
            
            self.status_label.setText(f"Dernière mise à jour : {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}")
            
        except Exception as e:
            self.status_label.setText("Erreur de chargement")
            print(f"Erreur load_data: {e}")

    def load_movements(self):
        try:
            movements = self.db.get_movement_history()
            filter_txt = self.cmb_movement_type.currentText()
            filtered = [m for m in movements if filter_txt == "Tous" or m['type_Mvt'] == filter_txt]
            
            self.table_movements.setRowCount(len(filtered))
            for i, mvt in enumerate(filtered):
                vals = [str(mvt['date_Mvt']), str(mvt['type_Mvt']), str(mvt['libelle']), str(mvt['Qté']), "Manuel"]
                for col_idx, val in enumerate(vals):
                    item = QTableWidgetItem(val)
                    item.setTextAlignment(Qt.AlignCenter)
                    self.table_movements.setItem(i, col_idx, item)
        except Exception as e:
            print(f"Erreur load_movements: {e}")

    def load_orders(self):
        try:
            orders = self.db.get_all_orders()
            self.table_orders.setRowCount(len(orders))
            for i, o in enumerate(orders):
                vals = [str(o['num_OF']), str(o['libelle']), str(o['Qte_prévue'])]
                for col_idx, val in enumerate(vals):
                    item = QTableWidgetItem(val)
                    item.setTextAlignment(Qt.AlignCenter)
                    self.table_orders.setItem(i, col_idx, item)
                
                status_txt = o['statut']
                item_status = QTableWidgetItem(status_txt)
                if status_txt == "En cours": item_status.setForeground(QColor("#F59E0B"))
                elif status_txt == "Terminé": item_status.setForeground(QColor("#10B981"))
                elif status_txt == "Annulé": item_status.setForeground(QColor("#EF4444"))
                else: item_status.setForeground(QColor("#64748B"))
                
                item_status.setFont(QFont("Segoe UI", 10, QFont.Bold))
                item_status.setTextAlignment(Qt.AlignCenter)
                self.table_orders.setItem(i, 3, item_status)
                
                item_date = QTableWidgetItem(str(o['date_prévue']))
                item_date.setTextAlignment(Qt.AlignCenter)
                self.table_orders.setItem(i, 4, item_date)
                
                item_qty = QTableWidgetItem(str(o.get('Qte_produite', 0)))
                item_qty.setTextAlignment(Qt.AlignCenter)
                self.table_orders.setItem(i, 5, item_qty)
        except Exception as e:
            print(f"Erreur load_orders: {e}")

    def update_charts(self, stocks):
        """Mise à jour graphique (Étiquettes tronquées + Donut propre)"""
        try:
            self.ax1.clear()
            self.ax2.clear()

            if not stocks:
                self.ax1.text(0.5, 0.5, "Aucune donnée disponible", ha='center', va='center')
                self.ax2.text(0.5, 0.5, "Aucune donnée", ha='center', va='center')
                self.canvas.draw()
                return

            labels = [(s['libelle'][:14] + '...') if len(s['libelle']) > 14 else s['libelle'] for s in stocks]
            
            qtys = [s['stock_Actuel'] for s in stocks]
            mins = [s['stock_min'] for s in stocks]
            colors_list = ['#EF4444' if q <= m else '#10B981' for q, m in zip(qtys, mins)]

            # Graphe à barres
            bars = self.ax1.bar(labels, qtys, color=colors_list, width=0.5, edgecolor='none', zorder=3)
            self.ax1.set_title("Niveaux de stock par article", fontsize=14, fontweight='bold', color='#1E293B', pad=20)
            self.ax1.set_ylabel("Quantité", fontsize=11, color='#475569', fontweight='bold')
            self.ax1.spines['top'].set_visible(False)
            self.ax1.spines['right'].set_visible(False)
            self.ax1.spines['left'].set_color('#CBD5E1')
            self.ax1.spines['bottom'].set_color('#CBD5E1')
            self.ax1.grid(axis='y', linestyle='--', alpha=0.7, color='#CBD5E1', zorder=0)
            
            self.ax1.set_xticks(range(len(labels)))
            self.ax1.set_xticklabels(labels, rotation=45, ha='right', fontsize=9, color='#475569')
            self.ax1.tick_params(axis='y', labelsize=10, colors='#475569')

            max_qty = max(qtys) if qtys else 0
            for bar in bars:
                height = bar.get_height()
                self.ax1.text(bar.get_x() + bar.get_width()/2., height + (max_qty * 0.02),
                              f'{int(height)}', 
                              ha='center', va='bottom', fontsize=9, fontweight='bold', color='#1E293B')

            crit = sum(1 for q, m in zip(qtys, mins) if q <= m)
            norm = len(stocks) - crit

            if len(stocks) > 0:
                wedges, texts, autotexts = self.ax2.pie(
                    [crit, norm], 
                    colors=['#EF4444', '#10B981'],
                    autopct=lambda p: f'{p:.1f}%\n({int(round(p*len(stocks)/100.0))})' if p > 0 else '', 
                    startangle=90, 
                    pctdistance=0.72, 
                    wedgeprops=dict(width=0.55, edgecolor='white', linewidth=2) 
                )
                
                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontsize(10) 
                    autotext.set_fontweight('bold')

                self.ax2.text(0, 0, f"Critique: {crit}\nNormal: {norm}", 
                              ha='center', va='center', fontsize=12, fontweight='bold', color='#1E293B')
                self.ax2.set_title("État global", fontsize=14, fontweight='bold', color='#1E293B', pad=20)

            self.figure.patch.set_facecolor('#ffffff')
            self.ax1.set_facecolor('#ffffff')
            self.ax2.set_facecolor('#ffffff')
            
            self.figure.tight_layout(pad=2.0)
            self.canvas.draw()
            
        except Exception as e:
            print(f"Erreur lors de la mise à jour des graphiques : {e}")

    def open_add_movement_dialog(self):
        dialog = AddMovementDialog(self.db, self)
        dialog.movement_added.connect(self.load_data)
        dialog.exec()

    def export_excel(self):
        try:
            stocks = self.db.get_stock_status()
            data = [{'Ref': s['reference'], 'Libelle': s['libelle'], 'Type': s['type_Article'], 'Stock': s['stock_Actuel'], 'Seuil': s['stock_min']} for s in stocks]
            df = pd.DataFrame(data)
            
            file_name, _ = QFileDialog.getSaveFileName(self, "Exporter Excel", f"export_stock_{datetime.now().strftime('%Y%m%d')}.xlsx", "Excel Files (*.xlsx)")
            if file_name:
                df.to_excel(file_name, index=False)
                QMessageBox.information(self, "Export réussi", f"Fichier Excel sauvegardé :\n{file_name}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur Excel", f"Échec de l'export : {str(e)}")

    def export_pdf(self):
        """Génère un rapport PDF des stocks avec ReportLab"""
        try:
            stocks = self.db.get_stock_status()
            if not stocks:
                QMessageBox.warning(self, "Attention", "Aucune donnée à exporter.")
                return

            file_name, _ = QFileDialog.getSaveFileName(self, "Exporter PDF", f"rapport_stock_{datetime.now().strftime('%Y%m%d')}.pdf", "PDF Files (*.pdf)")
            if not file_name: return

            doc = SimpleDocTemplate(file_name, pagesize=landscape(A4), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
            elements = []
            styles = getSampleStyleSheet()
            
            title_style = ParagraphStyle(
                'Titre',
                parent=styles['Heading1'],
                fontSize=18,
                textColor=colors.HexColor("#0F172A"),
                alignment=1, 
                spaceAfter=20
            )
            elements.append(Paragraph(f"Rapport d'État des Stocks", title_style))
            elements.append(Paragraph(f"Généré le : {datetime.now().strftime('%d/%m/%Y à %H:%M')}", styles['Normal']))
            elements.append(Spacer(1, 0.2 * inch))

            table_data = [["Référence", "Libellé", "Type", "Stock actuel", "Stock min", "Statut"]]
            
            for stock in stocks:
                s_actuel = stock['stock_Actuel'] or 0
                s_min = stock['stock_min'] or 0
                statut = "CRITIQUE" if s_actuel <= s_min else "NORMAL"
                table_data.append([
                    stock['reference'], 
                    stock['libelle'][:35], 
                    stock['type_Article'], 
                    str(s_actuel), 
                    str(s_min), 
                    statut
                ])

            pdf_table = Table(table_data, colWidths=[1.2*inch, 2.8*inch, 1.8*inch, 1.2*inch, 1.2*inch, 1.2*inch])
            
            style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1E293B")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('TOPPADDING', (0, 0), (-1, 0), 10),
                
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#E2E8F0")),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
            ])

            for i, row in enumerate(table_data[1:], start=1):
                bg_color = colors.white if i % 2 == 0 else colors.HexColor("#F8FAFC")
                style.add('BACKGROUND', (0, i), (-1, i), bg_color)
                
                if row[5] == "CRITIQUE":
                    style.add('TEXTCOLOR', (5, i), (5, i), colors.HexColor("#EF4444"))
                    style.add('FONTNAME', (5, i), (5, i), 'Helvetica-Bold')
                else:
                    style.add('TEXTCOLOR', (5, i), (5, i), colors.HexColor("#10B981"))
                    style.add('FONTNAME', (5, i), (5, i), 'Helvetica-Bold')

            pdf_table.setStyle(style)
            elements.append(pdf_table)

            doc.build(elements)
            QMessageBox.information(self, "Export réussi", f"Fichier PDF sauvegardé avec succès :\n{file_name}")

        except Exception as e:
            QMessageBox.critical(self, "Erreur PDF", f"Échec de l'export PDF : {str(e)}")

PremiumStockDashboard = StockManagementWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StockManagementWindow()
    window.show()
    sys.exit(app.exec())