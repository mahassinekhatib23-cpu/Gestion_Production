import time
from datetime import datetime
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
                               QPushButton, QGridLayout, QSizePolicy)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QCursor

from database_manager import DatabaseManager

class ClickableCard(QFrame):
    clicked = Signal()

    def __init__(self, title, value, color, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QFrame {{ 
                background-color: white; 
                border: 1px solid #CBD5E1; 
                border-radius: 8px; 
                border-left: 6px solid {color}; 
            }}
            QFrame:hover {{ 
                background-color: #F8FAFC; 
                border: 1px solid #94A3B8; 
                border-left: 6px solid {color}; 
            }}
        """)
        self.setFixedHeight(130)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 20, 25, 20)
        
        self.lbl_value = QLabel(value)
        self.lbl_value.setStyleSheet("font-size: 42px; font-weight: 800; color: #0F172A; border: none; background: transparent; font-family: 'Segoe UI';")
        
        self.lbl_title = QLabel(title.upper())
        self.lbl_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #64748B; letter-spacing: 1px; border: none; background: transparent; font-family: 'Segoe UI';")
        
        layout.addWidget(self.lbl_value)
        layout.addWidget(self.lbl_title)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
    
    def update_value(self, new_value):
        self.lbl_value.setText(str(new_value))


class HomeDashboard(QWidget):
    navigate_requested = Signal(int)

    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.setup_ui()
        self.refresh_data()

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        
        self.main_layout.setContentsMargins(40, 40, 40, 40)
        self.main_layout.setSpacing(25)

        header_layout = QHBoxLayout()
        
        lbl_title = QLabel("Tableau de Bord")
        lbl_title.setStyleSheet("font-size: 28px; font-weight: 800; color: #0F172A; font-family: 'Segoe UI';")
        lbl_title.setMinimumWidth(320)
        lbl_title.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        header_layout.addWidget(lbl_title)
        
        header_layout.addStretch()

        btn_refresh = QPushButton("⟳ Actualiser")
        btn_refresh.setMinimumWidth(120)
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.setStyleSheet("QPushButton { background-color: #1E293B; color: white; padding: 10px 18px; border-radius: 6px; font-weight: bold; border: none; font-size: 13px; } QPushButton:hover { background-color: #0F172A; }")
        btn_refresh.clicked.connect(self.refresh_data)
        
        header_layout.addWidget(btn_refresh)
        self.main_layout.addLayout(header_layout)

        self.kpi_layout = QGridLayout()
        self.kpi_layout.setSpacing(25)
        
        self.card_stock = ClickableCard("Articles en Stock", "0", "#3B82F6") # Bleu
        self.card_stock.clicked.connect(lambda: self.navigate_requested.emit(4))
        
        self.card_prod = ClickableCard("Ordres en Cours", "0", "#F59E0B") # Orange
        self.card_prod.clicked.connect(lambda: self.navigate_requested.emit(1))
        
        self.card_load = ClickableCard("Réceptions", "0", "#10B981") # Vert
        self.card_load.clicked.connect(lambda: self.navigate_requested.emit(2))
        
        self.card_unload = ClickableCard("Expéditions", "0", "#EF4444") # Rouge
        self.card_unload.clicked.connect(lambda: self.navigate_requested.emit(3))

        self.kpi_layout.addWidget(self.card_stock, 0, 0)
        self.kpi_layout.addWidget(self.card_prod, 0, 1)
        self.kpi_layout.addWidget(self.card_load, 1, 0)
        self.kpi_layout.addWidget(self.card_unload, 1, 1)
        
        self.main_layout.addLayout(self.kpi_layout)
        self.main_layout.addStretch()

        self.status_label = QLabel("Prêt")
        self.status_label.setStyleSheet("color: #64748B; font-size: 12px; font-weight: 500;")
        self.main_layout.addWidget(self.status_label)

    def refresh_data(self):
        try:
            stocks = self.db.get_stock_status()
            orders = self.db.get_all_orders()
            movements = self.db.get_movement_history()

            self.card_stock.update_value(len(stocks))
            self.card_prod.update_value(sum(1 for o in orders if o['statut'] == 'En cours'))
            self.card_load.update_value(sum(1 for m in movements if "Entrée" in m['type_Mvt']))
            self.card_unload.update_value(sum(1 for m in movements if "Sortie" in m['type_Mvt']))
            
            current_time = datetime.now().strftime('%d/%m/%Y à %H:%M:%S')
            self.status_label.setText(f"Dernière mise à jour : {current_time}")
            
        except Exception as e:
            print(f"Erreur refresh home: {e}")
            self.status_label.setText("Erreur de chargement des données")