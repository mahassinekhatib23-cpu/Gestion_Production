from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from database_manager import DatabaseManager


THEME_STYLE = """
    QWidget { background-color: #F5F7FA; font-family: 'Segoe UI', sans-serif; }
    
    /* TITRES DES PAGES */
    QLabel.page-title { 
        font-size: 26px; font-weight: 800; color: #1F2937; margin-bottom: 15px; 
    }
    
    /* TABLEAUX */
    QTableWidget { 
        border: 1px solid #D4D4D4; background-color: white; 
        alternate-background-color: #F8F9FA; border-radius: 4px; 
        selection-background-color: #E3F2FD; selection-color: #000;
    }
    QHeaderView::section { 
        background-color: #222D41; color: white; padding: 12px; 
        border: none; font-weight: bold; font-size: 13px;
    }
    
    /* BOUTONS D'ACTION */
    QPushButton.action-btn { 
        background-color: #222D41; color: white; border: none; 
        padding: 10px 20px; border-radius: 6px; font-weight: 600; 
    }
    QPushButton.action-btn:hover { background-color: #2F3B52; }
    
    /* CARTES KPI (Tableau de bord) */
    QFrame.kpi-card { 
        background-color: white; border-radius: 10px; border: 1px solid #E5E7EB; 
    }
    QLabel.kpi-value { font-size: 32px; font-weight: bold; color: #222D41; }
    QLabel.kpi-label { font-size: 13px; color: #6B7280; text-transform: uppercase; letter-spacing: 1px; }
"""

class BaseModule(QWidget):

    def __init__(self, title):
        super().__init__()
        self.db = DatabaseManager() 
        self.setStyleSheet(THEME_STYLE)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(30, 30, 30, 30)
        self.main_layout.setSpacing(20)
        
        self.lbl_title = QLabel(title)
        self.lbl_title.setProperty("class", "page-title")
        self.main_layout.addWidget(self.lbl_title)

    def refresh_data(self):
        pass