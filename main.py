import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, 
                             QVBoxLayout, QPushButton, QStackedWidget, QLabel, QFrame)
from PySide6.QtCore import Qt, QCoreApplication

try:
    from stock import StockManagementWindow
    from acceuil import HomeDashboard
    from production import ProductionWindow
    from reception import ReceptionWindow
    from expedition import ExpeditionWindow
except ImportError as e:
    print(f"ERREUR : Un fichier module est manquant.\nDétail: {e}")
    sys.exit(1)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestion de Stock - Supply Chain (Projet Capstone)")
        
        self.resize(1300, 800)
        self.setMinimumSize(1024, 768) 
        
        self.setStyleSheet("""
            QMainWindow { background-color: #F8FAFC; } 
            
            /* SIDEBAR : Bleu Nuit Profond */
            QFrame#Sidebar { background-color: #1E293B; border-radius: 0px; }
            
            /* LOGO (Ajusté : police plus petite pour rentrer dans 220px) */
            QLabel#LogoTitle { 
                color: #FFFFFF; font-family: 'Segoe UI'; 
                font-size: 20px; /* Réduit de 22 à 20px */
                font-weight: 800; padding: 30px 10px 5px 10px; 
            }
            QLabel#LogoSub { 
                color: #94A3B8; font-size: 10px; padding-left: 12px; 
                margin-bottom: 30px; font-weight: 600; text-transform: uppercase; letter-spacing: 2px; 
            }
            
            /* BOUTONS MENU NAVIGATION STANDARD */
            QFrame#Sidebar QPushButton[activeMenu="true"] {
                background-color: transparent;
                color: #94A3B8;
                text-align: left;
                padding: 12px 15px;
                border: none;
                font-family: 'Segoe UI';
                font-size: 14px;
                font-weight: 600;
                margin: 4px 12px;
                border-radius: 6px;
            }
            QFrame#Sidebar QPushButton[activeMenu="true"]:hover {
                background-color: #334155;
                color: #FFFFFF;
            }
            /* CHANGEMENT COULEUR SELECTION ICI (#c2d8ed) */
            QFrame#Sidebar QPushButton[activeMenu="true"]:checked {
                background-color: #c2d8ed; 
                color: #1E293B; /* Texte foncé nécessaire pour le contraste */
                font-weight: bold;
                padding-left: 20px;
            }

            /* BOUTON QUITTER SPÉCIFIQUE (ROUGE) */
            QPushButton#QuitButton {
                background-color: #EF4444; /* Rouge moderne */
                color: white;
                text-align: center;
                padding: 12px 15px;
                border: none; font-family: 'Segoe UI'; font-size: 14px; font-weight: bold;
                margin: 20px 12px 4px 12px; /* Marge haute pour séparer du menu */
                border-radius: 6px;
            }
            QPushButton#QuitButton:hover { background-color: #DC2626; }
            
            QLabel#Footer { color: #64748B; padding: 15px; font-size: 11px; text-align: center; }
        """)
        self.setup_ui()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QHBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        #  SIDEBAR
        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(220) 
        
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        
        sidebar_layout.addWidget(QLabel("Gestion Logistique", objectName="LogoTitle"))
        sidebar_layout.addWidget(QLabel("PROJET CAPSTONE", objectName="LogoSub"))

        self.btn_home = self.create_nav_btn("Accueil", 0)
        self.btn_prod = self.create_nav_btn("Production", 1)
        self.btn_load = self.create_nav_btn("Chargement", 2)
        self.btn_unload = self.create_nav_btn("Déchargement", 3)
        self.btn_stock = self.create_nav_btn("Stocks", 4)

        sidebar_layout.addWidget(self.btn_home)
        sidebar_layout.addWidget(self.btn_prod)
        sidebar_layout.addWidget(self.btn_load)
        sidebar_layout.addWidget(self.btn_unload)
        sidebar_layout.addWidget(self.btn_stock)
        
        sidebar_layout.addStretch()

        self.btn_quit = QPushButton("Quitter")
        self.btn_quit.setObjectName("QuitButton")
        self.btn_quit.setCursor(Qt.PointingHandCursor)
        self.btn_quit.clicked.connect(QCoreApplication.instance().quit)
        sidebar_layout.addWidget(self.btn_quit)
        
        sidebar_layout.addWidget(QLabel("© 2026 Supply Chain", objectName="Footer"))

        self.main_layout.addWidget(self.sidebar)

        self.content_stack = QStackedWidget()
        self.main_layout.addWidget(self.content_stack)

        self.page_home = HomeDashboard()
        self.page_home.navigate_requested.connect(self.switch_by_index)

        self.page_prod = ProductionWindow()
        self.page_load = ReceptionWindow()
        self.page_unload = ExpeditionWindow()
        self.page_stock = StockManagementWindow()

        self.content_stack.addWidget(self.page_home)   # 0
        self.content_stack.addWidget(self.page_prod)   # 1
        self.content_stack.addWidget(self.page_load)   # 2
        self.content_stack.addWidget(self.page_unload) # 3
        self.content_stack.addWidget(self.page_stock)  # 4

        self.btn_home.setChecked(True)
        self.content_stack.setCurrentIndex(0)

    def create_nav_btn(self, text, index):
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setProperty("activeMenu", True) 
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda: self.switch_page(index, btn))
        return btn

    def get_button_by_index(self, index):
        """Retourne le bouton correspondant à l'index donné"""
        mapping = {0: self.btn_home, 1: self.btn_prod, 2: self.btn_load, 3: self.btn_unload, 4: self.btn_stock}
        return mapping.get(index, self.btn_home)

    def switch_by_index(self, index):
        """Méthode appelée par le signal navigate_requested de HomeDashboard"""
        btn = self.get_button_by_index(index)
        self.switch_page(index, btn)
    
    def switch_page(self, index, active_btn):
        self.content_stack.setCurrentIndex(index)
        for btn in [self.btn_home, self.btn_prod, self.btn_load, self.btn_unload, self.btn_stock]:
            btn.setChecked(False)
        active_btn.setChecked(True)
        
        if hasattr(self.content_stack.currentWidget(), "refresh_data"):
            self.content_stack.currentWidget().refresh_data()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    app.setStyleSheet("""
        QMessageBox { background-color: white; }
        QMessageBox QLabel { color: #1E293B; font-size: 13px; }
        QMessageBox QPushButton {
            background-color: #10B981; color: white; border: none;
            padding: 6px 18px; border-radius: 4px; font-weight: bold; min-width: 80px;
        }
        QMessageBox QPushButton:hover { background-color: #059669; }
    """)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())