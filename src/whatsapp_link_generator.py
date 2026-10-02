import os
import sys
import urllib.parse

from PyQt5.QtCore import QByteArray, QSettings, Qt, QUrl
from PyQt5.QtGui import QDesktopServices, QFont, QPalette, QColor
from PyQt5.QtWidgets import (
    QAction, QApplication, QCheckBox, QComboBox, QDockWidget, QFrame,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox,
    QPushButton, QTabWidget, QTextEdit, QVBoxLayout, QWidget
)


class WhatsAppLinkGenerator(QMainWindow):
    SETTINGS_FILENAME = "setting_wa.ini"
    APP_STATE_VERSION = 1
    DEFAULT_SIZE = (980, 720)

    THEMES = {
        "dark": {
            "label": "Dark",
            "window": "#202124",
            "panel": "#292a2d",
            "field": "#171717",
            "text": "#f1f3f4",
            "muted": "#b0b3b8",
            "border": "#4a4d52",
            "accent": "#25D366",
            "accent_hover": "#1fb95a",
            "selection_text": "#101010",
        },
        "blue": {
            "label": "Blue",
            "window": "#eaf3ff",
            "panel": "#ffffff",
            "field": "#f7fbff",
            "text": "#17324d",
            "muted": "#58738f",
            "border": "#a8c7e8",
            "accent": "#1976D2",
            "accent_hover": "#125ca5",
            "selection_text": "#ffffff",
        },
        "red": {
            "label": "Red",
            "window": "#fff0f0",
            "panel": "#ffffff",
            "field": "#fff8f8",
            "text": "#4b2020",
            "muted": "#805757",
            "border": "#e3b0b0",
            "accent": "#D32F2F",
            "accent_hover": "#a82424",
            "selection_text": "#ffffff",
        },
        "orange": {
            "label": "Orange",
            "window": "#fff5e8",
            "panel": "#ffffff",
            "field": "#fffaf3",
            "text": "#4f331b",
            "muted": "#826443",
            "border": "#e7c59b",
            "accent": "#F57C00",
            "accent_hover": "#c46100",
            "selection_text": "#ffffff",
        },
        "green": {
            "label": "Green",
            "window": "#edf8f0",
            "panel": "#ffffff",
            "field": "#f7fcf8",
            "text": "#1f432b",
            "muted": "#54725d",
            "border": "#acd0b6",
            "accent": "#2E7D32",
            "accent_hover": "#225f26",
            "selection_text": "#ffffff",
        },
        "purple": {
            "label": "Purple",
            "window": "#f5efff",
            "panel": "#ffffff",
            "field": "#fbf8ff",
            "text": "#3d2855",
            "muted": "#705887",
            "border": "#cbb5df",
            "accent": "#7B1FA2",
            "accent_hover": "#5e177c",
            "selection_text": "#ffffff",
        },
    }

    def __init__(self):
        super().__init__()
        self.languages = self.load_languages()
        self.settings = self.load_settings()
        self.current_language = self.settings.get("language", "English")
        if self.current_language not in self.languages:
            self.current_language = "English"
        self.current_theme = self.settings.get("theme", "dark")
        if self.current_theme not in self.THEMES:
            self.current_theme = "dark"
        self.wa_format = bool(self.settings.get("wa_format", True))
        self.preview_link = ""
        self._restored_geometry = False
        self.initUI()
        self.restore_window_layout()
        self.restore_last_session()
        self.update_preview()

    @classmethod
    def settings_file_path(cls):
        """Return setting_wa.ini beside the script or packaged executable."""
        if getattr(sys, "frozen", False):
            base_directory = os.path.dirname(os.path.abspath(sys.executable))
        else:
            base_directory = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_directory, cls.SETTINGS_FILENAME)

    @classmethod
    def create_settings_store(cls):
        """Create an INI-backed QSettings object using UTF-8 when supported."""
        store = QSettings(cls.settings_file_path(), QSettings.IniFormat)
        if hasattr(store, "setIniCodec"):
            store.setIniCodec("UTF-8")
        return store

    def load_settings(self):
        """Load preferences, UI state, and last session from setting_wa.ini."""
        defaults = {
            "theme": "dark",
            "language": "English",
            "wa_format": True,
            "geometry": None,
            "window_state": None,
            "tab_index": 0,
            "preview_visible": True,
            "phone_input": "",
            "message_input": "",
            "simple_result": "",
            "multiple_numbers_input": "",
            "advanced_message_input": "",
            "advanced_result": "",
            "use_web": False,
        }

        store = self.create_settings_store()
        values = defaults.copy()
        values["theme"] = str(store.value("appearance/theme", defaults["theme"]))
        values["language"] = str(store.value("appearance/language", defaults["language"]))
        values["wa_format"] = store.value("link/default_wa_format", defaults["wa_format"], type=bool)
        values["geometry"] = store.value("window/geometry", None)
        values["window_state"] = store.value("window/state", None)
        values["tab_index"] = store.value("window/active_tab", defaults["tab_index"], type=int)
        values["preview_visible"] = store.value(
            "window/preview_visible", defaults["preview_visible"], type=bool
        )
        values["phone_input"] = str(store.value("last_input/phone", ""))
        values["message_input"] = str(store.value("last_input/message", ""))
        values["simple_result"] = str(store.value("last_input/simple_result", ""))
        values["multiple_numbers_input"] = str(
            store.value("last_input/multiple_numbers", "")
        )
        values["advanced_message_input"] = str(
            store.value("last_input/advanced_message", "")
        )
        values["advanced_result"] = str(store.value("last_input/advanced_result", ""))
        values["use_web"] = store.value("last_input/use_web", False, type=bool)

        if store.status() != QSettings.NoError:
            print(f"Warning: could not fully read {self.settings_file_path()}")
        return values

    def save_settings(self, show_error=True):
        """Persist all preferences, layout, position, size, and last session."""
        self.wa_format = self.include_country_code.isChecked()

        try:
            store = self.create_settings_store()
            store.setValue("meta/version", self.APP_STATE_VERSION)
            store.setValue("appearance/theme", self.current_theme)
            store.setValue("appearance/language", self.current_language)
            store.setValue("link/default_wa_format", self.wa_format)

            store.setValue("window/geometry", self.saveGeometry())
            store.setValue("window/state", self.saveState(self.APP_STATE_VERSION))
            store.setValue("window/active_tab", self.tabs.currentIndex())
            # The live preview is a permanent part of the interface.
            store.setValue("window/preview_visible", True)

            store.setValue("last_input/phone", self.phone_input.text())
            store.setValue("last_input/message", self.message_input.toPlainText())
            store.setValue("last_input/simple_result", self.result_output.toPlainText())
            store.setValue(
                "last_input/multiple_numbers", self.multiple_numbers_input.toPlainText()
            )
            store.setValue(
                "last_input/advanced_message", self.advanced_message_input.toPlainText()
            )
            store.setValue(
                "last_input/advanced_result", self.advanced_result_output.toPlainText()
            )
            store.setValue("last_input/use_web", self.use_web.isChecked())
            store.sync()

            if store.status() != QSettings.NoError:
                raise OSError(f"QSettings status: {store.status()}")
            return True
        except (OSError, TypeError, ValueError) as exc:
            print(f"Error saving settings: {exc}")
            if show_error:
                QMessageBox.warning(
                    self,
                    "Save Error",
                    f"Could not save settings to:\n{self.settings_file_path()}\n\n{exc}",
                )
            return False

    def load_languages(self):
        """Load all language translations"""
        return {
            "English": {
                "window_title": "WhatsApp Link Generator",
                "theme_btn_dark": "Switch to Light Theme",
                "theme_btn_light": "Switch to Dark Theme",
                "simple_tab": "Simple Generator",
                "advanced_tab": "Advanced Generator",
                "about_tab": "About",
                "phone_number": "Phone Number",
                "phone_help": "Enter phone number with country code (e.g., 1234567890 for US)",
                "phone_placeholder": "e.g., 1234567890",
                "message": "Message (Optional)",
                "message_placeholder": "Enter your message here...",
                "wa_format": "Use wa.me format (recommended)",
                "generate_btn": "Generate WhatsApp Link",
                "generated_link": "Generated Link",
                "copy_btn": "Copy to Clipboard",
                "multiple_numbers": "Multiple Phone Numbers",
                "multiple_numbers_help": "Enter multiple phone numbers (one per line) with country code",
                "multiple_numbers_placeholder": "1234567890\n1987654321\n1555666777",
                "message_options": "Message Options",
                "quick_insert": "Quick insert:",
                "name_btn": "{name}",
                "date_btn": "{date}",
                "company_btn": "{company}",
                "advanced_options": "Advanced Options",
                "use_web": "Use web.whatsapp.com (desktop)",
                "generate_multiple": "Generate Multiple Links",
                "generated_links": "Generated Links",
                "links_placeholder": "Generated links will appear here...",
                "copy_all": "Copy All Links",
                "input_error": "Input Error",
                "enter_phone": "Please enter a phone number",
                "valid_phone": "Please enter a valid phone number (digits only)",
                "enter_numbers": "Please enter at least one phone number",
                "no_valid_numbers": "No valid phone numbers found",
                "invalid_numbers": "Invalid Numbers",
                "numbers_skipped": "The following numbers were invalid and skipped:\n",
                "success": "Success",
                "copied_clipboard": "Link copied to clipboard!",
                "all_copied": "All links copied to clipboard!",
                "error": "Error",
                "no_link_copy": "No link to copy. Please generate a link first.",
                "no_links_copy": "No links to copy. Please generate links first.",
                "save_settings": "Save Current Settings",
                "settings_saved": "Settings saved successfully!",
                "reset_settings": "Reset to Defaults",
                "settings_reset": "Settings reset to defaults!",
                "about_title": "WhatsApp Link Generator",
                "about_description": "This tool helps you create WhatsApp links with pre-filled messages.",
                "features": "Features:",
                "feature1": "Generate individual WhatsApp links",
                "feature2": "Create multiple links at once",
                "feature3": "Customize messages with variables",
                "feature4": "Copy links to clipboard",
                "feature5": "No external dependencies required",
                "feature6": "Dark/Light theme support",
                "feature7": "Multilingual interface (15 languages)",
                "feature8": "Settings, layout, and last input saved in setting_wa.ini",
                "usage_tips": "Usage Tips:",
                "tip1": "Always include country code without '+' or '00' (e.g., 1234567890 for US)",
                "tip2": "Messages are URL-encoded automatically",
                "tip3": "Use {name}, {date}, {company} as placeholders in advanced mode",
                "tip4": "Phone numbers should contain only digits",
                "link_formats": "Link Formats:",
                "wa_format_example": "wa.me format: https://wa.me/1234567890?text=Hello",
                "api_format_example": "API format: https://api.whatsapp.com/send?phone=1234567890&text=Hello",
                "created_by": "Created By:",
                "copyright": "Copyright © ECOMTECH 2025 - All Right Reserved",
                "note": "Note: This tool doesn't store any data and runs locally on your computer."
            },
            "Indonesian": {
                "window_title": "Generator Tautan WhatsApp",
                "theme_btn_dark": "Beralih ke Tema Terang",
                "theme_btn_light": "Beralih ke Tema Gelap",
                "simple_tab": "Generator Sederhana",
                "advanced_tab": "Generator Lanjutan",
                "about_tab": "Tentang",
                "phone_number": "Nomor Telepon",
                "phone_help": "Masukkan nomor telepon dengan kode negara (contoh: 628123456789 untuk Indonesia)",
                "phone_placeholder": "contoh: 628123456789",
                "message": "Pesan (Opsional)",
                "message_placeholder": "Masukkan pesan Anda di sini...",
                "wa_format": "Gunakan format wa.me (direkomendasikan)",
                "generate_btn": "Buat Tautan WhatsApp",
                "generated_link": "Tautan yang Dihasilkan",
                "copy_btn": "Salin ke Clipboard",
                "multiple_numbers": "Banyak Nomor Telepon",
                "multiple_numbers_help": "Masukkan banyak nomor telepon (satu per baris) dengan kode negara",
                "multiple_numbers_placeholder": "628123456789\n628987654321\n628555666777",
                "message_options": "Opsi Pesan",
                "quick_insert": "Sisipkan cepat:",
                "name_btn": "{nama}",
                "date_btn": "{tanggal}",
                "company_btn": "{perusahaan}",
                "advanced_options": "Opsi Lanjutan",
                "use_web": "Gunakan web.whatsapp.com (desktop)",
                "generate_multiple": "Buat Banyak Tautan",
                "generated_links": "Tautan yang Dihasilkan",
                "links_placeholder": "Tautan yang dihasilkan akan muncul di sini...",
                "copy_all": "Salin Semua Tautan",
                "input_error": "Kesalahan Input",
                "enter_phone": "Harap masukkan nomor telepon",
                "valid_phone": "Harap masukkan nomor telepon yang valid (hanya angka)",
                "enter_numbers": "Harap masukkan setidaknya satu nomor telepon",
                "no_valid_numbers": "Tidak ditemukan nomor telepon yang valid",
                "invalid_numbers": "Nomor Tidak Valid",
                "numbers_skipped": "Nomor berikut tidak valid dan dilewati:\n",
                "success": "Berhasil",
                "copied_clipboard": "Tautan disalin ke clipboard!",
                "all_copied": "Semua tautan disalin ke clipboard!",
                "error": "Kesalahan",
                "no_link_copy": "Tidak ada tautan untuk disalin. Harap buat tautan terlebih dahulu.",
                "no_links_copy": "Tidak ada tautan untuk disalin. Harap buat tautan terlebih dahulu.",
                "save_settings": "Simpan Pengaturan Saat Ini",
                "settings_saved": "Pengaturan berhasil disimpan!",
                "reset_settings": "Reset ke Default",
                "settings_reset": "Pengaturan direset ke default!",
                "about_title": "Generator Tautan WhatsApp",
                "about_description": "Alat ini membantu Anda membuat tautan WhatsApp dengan pesan yang sudah diisi.",
                "features": "Fitur:",
                "feature1": "Buat tautan WhatsApp individual",
                "feature2": "Buat banyak tautan sekaligus",
                "feature3": "Sesuaikan pesan dengan variabel",
                "feature4": "Salin tautan ke clipboard",
                "feature5": "Tidak memerlukan dependensi eksternal",
                "feature6": "Dukungan tema Gelap/Terang",
                "feature7": "Antarmuka multibahasa (15 bahasa)",
                "feature8": "Pengaturan, tata letak, dan input terakhir disimpan di setting_wa.ini",
                "usage_tips": "Tips Penggunaan:",
                "tip1": "Selalu sertakan kode negara tanpa '+' atau '00' (contoh: 628123456789 untuk Indonesia)",
                "tip2": "Pesan dikodekan URL secara otomatis",
                "tip3": "Gunakan {nama}, {tanggal}, {perusahaan} sebagai placeholder di mode lanjutan",
                "tip4": "Nomor telepon harus berisi hanya angka",
                "link_formats": "Format Tautan:",
                "wa_format_example": "Format wa.me: https://wa.me/628123456789?text=Halo",
                "api_format_example": "Format API: https://api.whatsapp.com/send?phone=628123456789&text=Halo",
                "created_by": "Dibuat Oleh:",
                "copyright": "Hak Cipta © ECOMTECH 2025 - Seluruh Hak Dilindungi",
                "note": "Catatan: Alat ini tidak menyimpan data apa pun dan berjalan lokal di komputer Anda."
            },
            "Spanish": {
                "window_title": "Generador de Enlaces WhatsApp",
                "theme_btn_dark": "Cambiar a Tema Claro",
                "theme_btn_light": "Cambiar a Tema Oscuro",
                "simple_tab": "Generador Simple",
                "advanced_tab": "Generador Avanzado",
                "about_tab": "Acerca de",
                "phone_number": "Número de Teléfono",
                "phone_help": "Ingrese número con código de país (ej: 521234567890 para México)",
                "phone_placeholder": "ej: 521234567890",
                "message": "Mensaje (Opcional)",
                "message_placeholder": "Ingrese su mensaje aquí...",
                "wa_format": "Usar formato wa.me (recomendado)",
                "generate_btn": "Generar Enlace WhatsApp",
                "generated_link": "Enlace Generado",
                "copy_btn": "Copiar al Portapapeles",
                "multiple_numbers": "Múltiples Números de Teléfono",
                "multiple_numbers_help": "Ingrese múltiples números (uno por línea) con código de país",
                "multiple_numbers_placeholder": "521234567890\n529876543210\n525556667777",
                "message_options": "Opciones de Mensaje",
                "quick_insert": "Insertar rápido:",
                "name_btn": "{nombre}",
                "date_btn": "{fecha}",
                "company_btn": "{empresa}",
                "advanced_options": "Opciones Avanzadas",
                "use_web": "Usar web.whatsapp.com (escritorio)",
                "generate_multiple": "Generar Múltiples Enlaces",
                "generated_links": "Enlaces Generados",
                "links_placeholder": "Los enlaces generados aparecerán aquí...",
                "copy_all": "Copiar Todos los Enlaces",
                "input_error": "Error de Entrada",
                "enter_phone": "Por favor ingrese un número de teléfono",
                "valid_phone": "Por favor ingrese un número válido (solo dígitos)",
                "enter_numbers": "Por favor ingrese al menos un número de teléfono",
                "no_valid_numbers": "No se encontraron números válidos",
                "invalid_numbers": "Números Inválidos",
                "numbers_skipped": "Los siguientes números eran inválidos y se omitieron:\n",
                "success": "Éxito",
                "copied_clipboard": "¡Enlace copiado al portapapeles!",
                "all_copied": "¡Todos los enlaces copiados al portapapeles!",
                "error": "Error",
                "no_link_copy": "No hay enlace para copiar. Por favor genere un enlace primero.",
                "no_links_copy": "No hay enlaces para copiar. Por favor genere enlaces primero.",
                "save_settings": "Guardar Configuración Actual",
                "settings_saved": "¡Configuración guardada exitosamente!",
                "reset_settings": "Restablecer a Valores Predeterminados",
                "settings_reset": "¡Configuración restablecida a valores predeterminados!",
                "about_title": "Generador de Enlaces WhatsApp",
                "about_description": "Esta herramienta ayuda a crear enlaces WhatsApp con mensajes predefinidos.",
                "features": "Características:",
                "feature1": "Generar enlaces WhatsApp individuales",
                "feature2": "Crear múltiples enlaces a la vez",
                "feature3": "Personalizar mensajes con variables",
                "feature4": "Copiar enlaces al portapapeles",
                "feature5": "No requiere dependencias externas",
                "feature6": "Soporte para tema Oscuro/Claro",
                "feature7": "Interfaz multilingüe (15 idiomas)",
                "feature8": "Configuración, diseño y última entrada guardados en setting_wa.ini",
                "usage_tips": "Consejos de Uso:",
                "tip1": "Siempre incluya código de país sin '+' o '00' (ej: 521234567890 para México)",
                "tip2": "Los mensajes se codifican en URL automáticamente",
                "tip3": "Use {nombre}, {fecha}, {empresa} como marcadores en modo avanzado",
                "tip4": "Los números deben contener solo dígitos",
                "link_formats": "Formatos de Enlace:",
                "wa_format_example": "Formato wa.me: https://wa.me/521234567890?text=Hola",
                "api_format_example": "Formato API: https://api.whatsapp.com/send?phone=521234567890&text=Hola",
                "created_by": "Creado Por:",
                "copyright": "Copyright © ECOMTECH 2025 - Todos los Derechos Reservados",
                "note": "Nota: Esta herramienta no almacena datos y se ejecuta localmente en su computadora."
            },
            "French": {
                "window_title": "Générateur de Liens WhatsApp",
                "theme_btn_dark": "Passer au Thème Clair",
                "theme_btn_light": "Passer au Thème Sombre",
                "simple_tab": "Générateur Simple",
                "advanced_tab": "Générateur Avancé",
                "about_tab": "À Propos",
                "phone_number": "Numéro de Téléphone",
                "phone_help": "Entrez le numéro avec l'indicatif pays (ex: 33123456789 pour la France)",
                "phone_placeholder": "ex: 33123456789",
                "message": "Message (Optionnel)",
                "message_placeholder": "Entrez votre message ici...",
                "wa_format": "Utiliser le format wa.me (recommandé)",
                "generate_btn": "Générer Lien WhatsApp",
                "generated_link": "Lien Généré",
                "copy_btn": "Copier dans le Presse-papiers",
                "multiple_numbers": "Plusieurs Numéros de Téléphone",
                "multiple_numbers_help": "Entrez plusieurs numéros (un par ligne) avec indicatif pays",
                "multiple_numbers_placeholder": "33123456789\n33987654321\n33555666777",
                "message_options": "Options de Message",
                "quick_insert": "Insertion rapide:",
                "name_btn": "{nom}",
                "date_btn": "{date}",
                "company_btn": "{entreprise}",
                "advanced_options": "Options Avancées",
                "use_web": "Utiliser web.whatsapp.com (bureau)",
                "generate_multiple": "Générer Plusieurs Liens",
                "generated_links": "Liens Générés",
                "links_placeholder": "Les liens générés apparaîtront ici...",
                "copy_all": "Copier Tous les Liens",
                "input_error": "Erreur de Saisie",
                "enter_phone": "Veuillez entrer un numéro de téléphone",
                "valid_phone": "Veuillez entrer un numéro valide (chiffres uniquement)",
                "enter_numbers": "Veuillez entrer au moins un numéro de téléphone",
                "no_valid_numbers": "Aucun numéro valide trouvé",
                "invalid_numbers": "Numéros Invalides",
                "numbers_skipped": "Les numéros suivants étaient invalides et ont été ignorés:\n",
                "success": "Succès",
                "copied_clipboard": "Lien copié dans le presse-papiers !",
                "all_copied": "Tous les liens copiés dans le presse-papiers !",
                "error": "Erreur",
                "no_link_copy": "Aucun lien à copier. Veuillez d'abord générer un lien.",
                "no_links_copy": "Aucun lien à copier. Veuillez d'abord générer des liens.",
                "save_settings": "Enregistrer les Paramètres Actuels",
                "settings_saved": "Paramètres enregistrés avec succès !",
                "reset_settings": "Réinitialiser aux Valeurs par Défaut",
                "settings_reset": "Paramètres réinitialisés aux valeurs par défaut !",
                "about_title": "Générateur de Liens WhatsApp",
                "about_description": "Cet outil aide à créer des liens WhatsApp avec messages pré-remplis.",
                "features": "Fonctionnalités:",
                "feature1": "Générer des liens WhatsApp individuels",
                "feature2": "Créer plusieurs liens à la fois",
                "feature3": "Personnaliser les messages avec variables",
                "feature4": "Copier les liens dans le presse-papiers",
                "feature5": "Aucune dépendance externe requise",
                "feature6": "Support thème Sombre/Clair",
                "feature7": "Interface multilingue (15 langues)",
                "feature8": "Paramètres, disposition et dernière saisie enregistrés dans setting_wa.ini",
                "usage_tips": "Conseils d'Utilisation:",
                "tip1": "Toujours inclure l'indicatif pays sans '+' ou '00' (ex: 33123456789 pour la France)",
                "tip2": "Les messages sont encodés URL automatiquement",
                "tip3": "Utilisez {nom}, {date}, {entreprise} comme variables en mode avancé",
                "tip4": "Les numéros doivent contenir uniquement des chiffres",
                "link_formats": "Formats de Lien:",
                "wa_format_example": "Format wa.me: https://wa.me/33123456789?text=Bonjour",
                "api_format_example": "Format API: https://api.whatsapp.com/send?phone=33123456789&text=Bonjour",
                "created_by": "Créé Par:",
                "copyright": "Copyright © ECOMTECH 2025 - Tous Droits Réservés",
                "note": "Note: Cet outil ne stocke aucune donnée et s'exécute localement sur votre ordinateur."
            },
            "Portuguese": {
                "window_title": "Gerador de Links WhatsApp",
                "theme_btn_dark": "Mudar para Tema Claro",
                "theme_btn_light": "Mudar para Tema Escuro",
                "simple_tab": "Gerador Simples",
                "advanced_tab": "Gerador Avançado",
                "about_tab": "Sobre",
                "phone_number": "Número de Telefone",
                "phone_help": "Digite número com código do país (ex: 5511999999999 para Brasil)",
                "phone_placeholder": "ex: 5511999999999",
                "message": "Mensagem (Opcional)",
                "message_placeholder": "Digite sua mensagem aqui...",
                "wa_format": "Usar formato wa.me (recomendado)",
                "generate_btn": "Gerar Link WhatsApp",
                "generated_link": "Link Gerado",
                "copy_btn": "Copiar para Área de Transferência",
                "multiple_numbers": "Múltiplos Números de Telefone",
                "multiple_numbers_help": "Digite múltiplos números (um por linha) com código do país",
                "multiple_numbers_placeholder": "5511999999999\n5511888888888\n5511777777777",
                "message_options": "Opções de Mensagem",
                "quick_insert": "Inserção rápida:",
                "name_btn": "{nome}",
                "date_btn": "{data}",
                "company_btn": "{empresa}",
                "advanced_options": "Opções Avançadas",
                "use_web": "Usar web.whatsapp.com (desktop)",
                "generate_multiple": "Gerar Múltiplos Links",
                "generated_links": "Links Gerados",
                "links_placeholder": "Links gerados aparecerão aqui...",
                "copy_all": "Copiar Todos os Links",
                "input_error": "Erro de Entrada",
                "enter_phone": "Por favor digite um número de telefone",
                "valid_phone": "Por favor digite um número válido (apenas dígitos)",
                "enter_numbers": "Por favor digite pelo menos um número de telefone",
                "no_valid_numbers": "Nenhum número válido encontrado",
                "invalid_numbers": "Números Inválidos",
                "numbers_skipped": "Os seguintes números eram inválidos e foram ignorados:\n",
                "success": "Sucesso",
                "copied_clipboard": "Link copiado para área de transferência!",
                "all_copied": "Todos os links copiados para área de transferência!",
                "error": "Erro",
                "no_link_copy": "Nenhum link para copiar. Por favor gere um link primeiro.",
                "no_links_copy": "Nenhum link para copiar. Por favor gere links primeiro.",
                "save_settings": "Salvar Configurações Atuais",
                "settings_saved": "Configurações salvas com sucesso!",
                "reset_settings": "Redefinir para Padrões",
                "settings_reset": "Configurações redefinidas para padrões!",
                "about_title": "Gerador de Links WhatsApp",
                "about_description": "Esta ferramenta ajuda a criar links WhatsApp com mensagens pré-preenchidas.",
                "features": "Características:",
                "feature1": "Gerar links WhatsApp individuais",
                "feature2": "Criar múltiplos links de uma vez",
                "feature3": "Personalizar mensagens com variáveis",
                "feature4": "Copiar links para área de transferência",
                "feature5": "Nenhuma dependência externa necessária",
                "feature6": "Suporte tema Escuro/Claro",
                "feature7": "Interface multilíngue (15 idiomas)",
                "feature8": "Configurações, layout e última entrada salvos em setting_wa.ini",
                "usage_tips": "Dicas de Uso:",
                "tip1": "Sempre inclua código do país sem '+' ou '00' (ex: 5511999999999 para Brasil)",
                "tip2": "Mensagens são codificadas URL automaticamente",
                "tip3": "Use {nome}, {data}, {empresa} como variáveis em modo avançado",
                "tip4": "Números devem conter apenas dígitos",
                "link_formats": "Formatos de Link:",
                "wa_format_example": "Formato wa.me: https://wa.me/5511999999999?text=Olá",
                "api_format_example": "Formato API: https://api.whatsapp.com/send?phone=5511999999999&text=Olá",
                "created_by": "Criado Por:",
                "copyright": "Copyright © ECOMTECH 2025 - Todos os Direitos Reservados",
                "note": "Nota: Esta ferramenta não armazena dados e executa localmente no seu computador."
            },
            "German": {
                "window_title": "WhatsApp-Link-Generator",
                "theme_btn_dark": "Zu Hell Thema wechseln",
                "theme_btn_light": "Zu Dunkel Thema wechseln",
                "simple_tab": "Einfacher Generator",
                "advanced_tab": "Erweiterter Generator",
                "about_tab": "Über",
                "phone_number": "Telefonnummer",
                "phone_help": "Nummer mit Ländervorwahl eingeben (z.B. 4915112345678 für Deutschland)",
                "phone_placeholder": "z.B. 4915112345678",
                "message": "Nachricht (Optional)",
                "message_placeholder": "Nachricht hier eingeben...",
                "wa_format": "wa.me-Format verwenden (empfohlen)",
                "generate_btn": "WhatsApp-Link generieren",
                "generated_link": "Generierter Link",
                "copy_btn": "In Zwischenablage kopieren",
                "multiple_numbers": "Mehrere Telefonnummern",
                "multiple_numbers_help": "Mehrere Nummern (eine pro Zeile) mit Ländervorwahl eingeben",
                "multiple_numbers_placeholder": "4915112345678\n4915098765432\n491555666777",
                "message_options": "Nachrichtenoptionen",
                "quick_insert": "Schnelleinfügung:",
                "name_btn": "{Name}",
                "date_btn": "{Datum}",
                "company_btn": "{Firma}",
                "advanced_options": "Erweiterte Optionen",
                "use_web": "web.whatsapp.com verwenden (Desktop)",
                "generate_multiple": "Mehrere Links generieren",
                "generated_links": "Generierte Links",
                "links_placeholder": "Generierte Links erscheinen hier...",
                "copy_all": "Alle Links kopieren",
                "input_error": "Eingabefehler",
                "enter_phone": "Bitte geben Sie eine Telefonnummer ein",
                "valid_phone": "Bitte geben Sie eine gültige Nummer ein (nur Ziffern)",
                "enter_numbers": "Bitte geben Sie mindestens eine Telefonnummer ein",
                "no_valid_numbers": "Keine gültigen Nummern gefunden",
                "invalid_numbers": "Ungültige Nummern",
                "numbers_skipped": "Folgende Nummern waren ungültig und wurden übersprungen:\n",
                "success": "Erfolg",
                "copied_clipboard": "Link in Zwischenablage kopiert!",
                "all_copied": "Alle Links in Zwischenablage kopiert!",
                "error": "Fehler",
                "no_link_copy": "Kein Link zum Kopieren. Bitte zuerst Link generieren.",
                "no_links_copy": "Keine Links zum Kopieren. Bitte zuerst Links generieren.",
                "save_settings": "Aktuelle Einstellungen speichern",
                "settings_saved": "Einstellungen erfolgreich gespeichert!",
                "reset_settings": "Auf Standardeinstellungen zurücksetzen",
                "settings_reset": "Einstellungen auf Standardwerte zurückgesetzt!",
                "about_title": "WhatsApp-Link-Generator",
                "about_description": "Dieses Tool erstellt WhatsApp-Links mit vorausgefüllten Nachrichten.",
                "features": "Funktionen:",
                "feature1": "Einzelne WhatsApp-Links generieren",
                "feature2": "Mehrere Links gleichzeitig erstellen",
                "feature3": "Nachrichten mit Variablen anpassen",
                "feature4": "Links in Zwischenablage kopieren",
                "feature5": "Keine externen Abhängigkeiten erforderlich",
                "feature6": "Dunkel/Hell Thema Unterstützung",
                "feature7": "Mehrsprachige Oberfläche (15 Sprachen)",
                "feature8": "Einstellungen, Layout und letzte Eingabe in setting_wa.ini gespeichert",
                "usage_tips": "Nutzungstipps:",
                "tip1": "Ländervorwahl ohne '+' oder '00' eingeben (z.B. 4915112345678 für Deutschland)",
                "tip2": "Nachrichten werden automatisch URL-codiert",
                "tip3": "{Name}, {Datum}, {Firma} als Platzhalter im erweiterten Modus verwenden",
                "tip4": "Telefonnummern sollten nur Ziffern enthalten",
                "link_formats": "Link-Formate:",
                "wa_format_example": "wa.me-Format: https://wa.me/4915112345678?text=Hallo",
                "api_format_example": "API-Format: https://api.whatsapp.com/send?phone=4915112345678&text=Hallo",
                "created_by": "Erstellt Von:",
                "copyright": "Copyright © ECOMTECH 2025 - Alle Rechte vorbehalten",
                "note": "Hinweis: Dieses Tool speichert keine Daten und läuft lokal auf Ihrem Computer."
            },
            "Chinese": {
                "window_title": "WhatsApp链接生成器",
                "theme_btn_dark": "切换到浅色主题",
                "theme_btn_light": "切换到深色主题",
                "simple_tab": "简单生成器",
                "advanced_tab": "高级生成器",
                "about_tab": "关于",
                "phone_number": "电话号码",
                "phone_help": "输入带国家代码的电话号码（例如：8613800138000为中国）",
                "phone_placeholder": "例如：8613800138000",
                "message": "消息（可选）",
                "message_placeholder": "在此输入您的消息...",
                "wa_format": "使用wa.me格式（推荐）",
                "generate_btn": "生成WhatsApp链接",
                "generated_link": "生成的链接",
                "copy_btn": "复制到剪贴板",
                "multiple_numbers": "多个电话号码",
                "multiple_numbers_help": "输入多个电话号码（每行一个）带国家代码",
                "multiple_numbers_placeholder": "8613800138000\n8613812345678\n8613955556666",
                "message_options": "消息选项",
                "quick_insert": "快速插入：",
                "name_btn": "{姓名}",
                "date_btn": "{日期}",
                "company_btn": "{公司}",
                "advanced_options": "高级选项",
                "use_web": "使用web.whatsapp.com（桌面版）",
                "generate_multiple": "生成多个链接",
                "generated_links": "生成的链接",
                "links_placeholder": "生成的链接将显示在这里...",
                "copy_all": "复制所有链接",
                "input_error": "输入错误",
                "enter_phone": "请输入电话号码",
                "valid_phone": "请输入有效的电话号码（仅数字）",
                "enter_numbers": "请至少输入一个电话号码",
                "no_valid_numbers": "未找到有效号码",
                "invalid_numbers": "无效号码",
                "numbers_skipped": "以下号码无效并已跳过：\n",
                "success": "成功",
                "copied_clipboard": "链接已复制到剪贴板！",
                "all_copied": "所有链接已复制到剪贴板！",
                "error": "错误",
                "no_link_copy": "没有链接可复制。请先生成链接。",
                "no_links_copy": "没有链接可复制。请先生成链接。",
                "save_settings": "保存当前设置",
                "settings_saved": "设置保存成功！",
                "reset_settings": "重置为默认值",
                "settings_reset": "设置已重置为默认值！",
                "about_title": "WhatsApp链接生成器",
                "about_description": "此工具帮助创建带有预填消息的WhatsApp链接。",
                "features": "功能：",
                "feature1": "生成单个WhatsApp链接",
                "feature2": "一次创建多个链接",
                "feature3": "使用变量自定义消息",
                "feature4": "复制链接到剪贴板",
                "feature5": "无需外部依赖",
                "feature6": "深色/浅色主题支持",
                "feature7": "多语言界面（15种语言）",
                "feature8": "设置、布局和上次输入保存在 setting_wa.ini 中",
                "usage_tips": "使用提示：",
                "tip1": "始终包含国家代码，不带'+'或'00'（例如：8613800138000为中国）",
                "tip2": "消息自动进行URL编码",
                "tip3": "在高级模式下使用{姓名}、{日期}、{公司}作为占位符",
                "tip4": "电话号码应仅包含数字",
                "link_formats": "链接格式：",
                "wa_format_example": "wa.me格式：https://wa.me/8613800138000?text=你好",
                "api_format_example": "API格式：https://api.whatsapp.com/send?phone=8613800138000&text=你好",
                "created_by": "创建者：",
                "copyright": "版权所有 © ECOMTECH 2025 - 保留所有权利",
                "note": "注意：此工具不存储任何数据，仅在您的计算机本地运行。"
            },
            "Japanese": {
                "window_title": "WhatsAppリンクジェネレーター",
                "theme_btn_dark": "ライトテーマに切り替え",
                "theme_btn_light": "ダークテーマに切り替え",
                "simple_tab": "シンプルジェネレーター",
                "advanced_tab": "アドバンストジェネレーター",
                "about_tab": "概要",
                "phone_number": "電話番号",
                "phone_help": "国番号付きで電話番号を入力（例：日本の場合は819012345678）",
                "phone_placeholder": "例：819012345678",
                "message": "メッセージ（任意）",
                "message_placeholder": "メッセージを入力してください...",
                "wa_format": "wa.me形式を使用（推奨）",
                "generate_btn": "WhatsAppリンクを生成",
                "generated_link": "生成されたリンク",
                "copy_btn": "クリップボードにコピー",
                "multiple_numbers": "複数の電話番号",
                "multiple_numbers_help": "複数の電話番号を国番号付きで入力（1行に1つ）",
                "multiple_numbers_placeholder": "819012345678\n819098765432\n8190555666777",
                "message_options": "メッセージオプション",
                "quick_insert": "クイック挿入：",
                "name_btn": "{名前}",
                "date_btn": "{日付}",
                "company_btn": "{会社}",
                "advanced_options": "詳細オプション",
                "use_web": "web.whatsapp.comを使用（デスクトップ）",
                "generate_multiple": "複数リンクを生成",
                "generated_links": "生成されたリンク",
                "links_placeholder": "生成されたリンクがここに表示されます...",
                "copy_all": "全てのリンクをコピー",
                "input_error": "入力エラー",
                "enter_phone": "電話番号を入力してください",
                "valid_phone": "有効な電話番号を入力してください（数字のみ）",
                "enter_numbers": "少なくとも1つの電話番号を入力してください",
                "no_valid_numbers": "有効な番号が見つかりません",
                "invalid_numbers": "無効な番号",
                "numbers_skipped": "以下の番号は無効でありスキップされました：\n",
                "success": "成功",
                "copied_clipboard": "リンクをクリップボードにコピーしました！",
                "all_copied": "全てのリンクをクリップボードにコピーしました！",
                "error": "エラー",
                "no_link_copy": "コピーするリンクがありません。最初にリンクを生成してください。",
                "no_links_copy": "コピーするリンクがありません。最初にリンクを生成してください。",
                "save_settings": "現在の設定を保存",
                "settings_saved": "設定が正常に保存されました！",
                "reset_settings": "デフォルトにリセット",
                "settings_reset": "設定がデフォルト値にリセットされました！",
                "about_title": "WhatsAppリンクジェネレーター",
                "about_description": "このツールは事前入力されたメッセージでWhatsAppリンクを作成します。",
                "features": "機能：",
                "feature1": "個々のWhatsAppリンクを生成",
                "feature2": "複数のリンクを一度に作成",
                "feature3": "変数でメッセージをカスタマイズ",
                "feature4": "リンクをクリップボードにコピー",
                "feature5": "外部依存関係なし",
                "feature6": "ダーク/ライトテーマ対応",
                "feature7": "多言語インターフェース（15言語）",
                "feature8": "設定、レイアウト、前回の入力を setting_wa.ini に保存",
                "usage_tips": "使用上のヒント：",
                "tip1": "国番号を'+'や'00'なしで入力（例：日本の場合は819012345678）",
                "tip2": "メッセージは自動的にURLエンコードされます",
                "tip3": "詳細モードで{名前}、{日付}、{会社}をプレースホルダーとして使用",
                "tip4": "電話番号は数字のみで入力",
                "link_formats": "リンク形式：",
                "wa_format_example": "wa.me形式：https://wa.me/819012345678?text=こんにちは",
                "api_format_example": "API形式：https://api.whatsapp.com/send?phone=819012345678&text=こんにちは",
                "created_by": "作成者：",
                "copyright": "著作権 © ECOMTECH 2025 - 全著作権所有",
                "note": "注：このツールはデータを保存せず、コンピューター上でローカルに実行されます。"
            },
            "Russian": {
                "window_title": "Генератор WhatsApp Ссылок",
                "theme_btn_dark": "Переключить на светлую тему",
                "theme_btn_light": "Переключить на темную тему",
                "simple_tab": "Простой генератор",
                "advanced_tab": "Продвинутый генератор",
                "about_tab": "О программе",
                "phone_number": "Номер телефона",
                "phone_help": "Введите номер с кодом страны (например: 79161234567 для России)",
                "phone_placeholder": "например: 79161234567",
                "message": "Сообщение (Необязательно)",
                "message_placeholder": "Введите ваше сообщение здесь...",
                "wa_format": "Использовать формат wa.me (рекомендуется)",
                "generate_btn": "Сгенерировать WhatsApp ссылку",
                "generated_link": "Сгенерированная ссылка",
                "copy_btn": "Скопировать в буфер обмена",
                "multiple_numbers": "Несколько номеров телефона",
                "multiple_numbers_help": "Введите несколько номеров (по одному в строке) с кодом страны",
                "multiple_numbers_placeholder": "79161234567\n79169876543\n791655566677",
                "message_options": "Опции сообщений",
                "quick_insert": "Быстрая вставка:",
                "name_btn": "{имя}",
                "date_btn": "{дата}",
                "company_btn": "{компания}",
                "advanced_options": "Расширенные опции",
                "use_web": "Использовать web.whatsapp.com (десктоп)",
                "generate_multiple": "Сгенерировать несколько ссылок",
                "generated_links": "Сгенерированные ссылки",
                "links_placeholder": "Сгенерированные ссылки появятся здесь...",
                "copy_all": "Скопировать все ссылки",
                "input_error": "Ошибка ввода",
                "enter_phone": "Пожалуйста, введите номер телефона",
                "valid_phone": "Пожалуйста, введите действительный номер (только цифры)",
                "enter_numbers": "Пожалуйста, введите хотя бы один номер телефона",
                "no_valid_numbers": "Действительные номера не найдены",
                "invalid_numbers": "Недействительные номера",
                "numbers_skipped": "Следующие номера были недействительными и пропущены:\n",
                "success": "Успех",
                "copied_clipboard": "Ссылка скопирована в буфер обмена!",
                "all_copied": "Все ссылки скопированы в буфер обмена!",
                "error": "Ошибка",
                "no_link_copy": "Нет ссылки для копирования. Пожалуйста, сначала сгенерируйте ссылку.",
                "no_links_copy": "Нет ссылок для копирования. Пожалуйста, сначала сгенерируйте ссылки.",
                "save_settings": "Сохранить текущие настройки",
                "settings_saved": "Настройки успешно сохранены!",
                "reset_settings": "Сбросить к значениям по умолчанию",
                "settings_reset": "Настройки сброшены к значениям по умолчанию!",
                "about_title": "Генератор WhatsApp Ссылок",
                "about_description": "Этот инструмент помогает создавать WhatsApp ссылки с предзаполненными сообщениями.",
                "features": "Функции:",
                "feature1": "Генерация отдельных WhatsApp ссылок",
                "feature2": "Создание нескольких ссылок одновременно",
                "feature3": "Настройка сообщений с переменными",
                "feature4": "Копирование ссылок в буфер обмена",
                "feature5": "Не требуются внешние зависимости",
                "feature6": "Поддержка темной/светлой темы",
                "feature7": "Многоязычный интерфейс (15 языков)",
                "feature8": "Настройки, макет и последний ввод сохранены в setting_wa.ini",
                "usage_tips": "Советы по использованию:",
                "tip1": "Всегда включайте код страны без '+' или '00' (например: 79161234567 для России)",
                "tip2": "Сообщения автоматически кодируются в URL",
                "tip3": "Используйте {имя}, {дата}, {компания} как заполнители в расширенном режиме",
                "tip4": "Номера телефонов должны содержать только цифры",
                "link_formats": "Форматы ссылок:",
                "wa_format_example": "Формат wa.me: https://wa.me/79161234567?text=Привет",
                "api_format_example": "API формат: https://api.whatsapp.com/send?phone=79161234567&text=Привет",
                "created_by": "Создано:",
                "copyright": "Авторские права © ECOMTECH 2025 - Все права защищены",
                "note": "Примечание: Этот инструмент не хранит данные и работает локально на вашем компьютере."
            },
            "Arabic": {
                "window_title": "مولد روابط واتساب",
                "theme_btn_dark": "التبديل إلى الوضع الفاتح",
                "theme_btn_light": "التبديل إلى الوضع الداكن",
                "simple_tab": "مولد بسيط",
                "advanced_tab": "مولد متقدم",
                "about_tab": "حول",
                "phone_number": "رقم الهاتف",
                "phone_help": "أدخل رقم الهاتف مع رمز الدولة (مثال: 966512345678 للسعودية)",
                "phone_placeholder": "مثال: 966512345678",
                "message": "الرسالة (اختياري)",
                "message_placeholder": "أدخل رسالتك هنا...",
                "wa_format": "استخدم تنسيق wa.me (مُوصى به)",
                "generate_btn": "إنشاء رابط واتساب",
                "generated_link": "الرابط المولد",
                "copy_btn": "نسخ إلى الحافظة",
                "multiple_numbers": "أرقام هواتف متعددة",
                "multiple_numbers_help": "أدخل أرقام هواتف متعددة (واحد في كل سطر) مع رمز الدولة",
                "multiple_numbers_placeholder": "966512345678\n966598765432\n966555666777",
                "message_options": "خيارات الرسالة",
                "quick_insert": "إدراج سريع:",
                "name_btn": "{الاسم}",
                "date_btn": "{التاريخ}",
                "company_btn": "{الشركة}",
                "advanced_options": "خيارات متقدمة",
                "use_web": "استخدم web.whatsapp.com (سطح المكتب)",
                "generate_multiple": "إنشاء روابط متعددة",
                "generated_links": "الروابط المولدة",
                "links_placeholder": "الروابط المولدة ستظهر هنا...",
                "copy_all": "نسخ جميع الروابط",
                "input_error": "خطأ في الإدخال",
                "enter_phone": "الرجاء إدخال رقم الهاتف",
                "valid_phone": "الرجاء إدخال رقم هاتف صالح (أرقام فقط)",
                "enter_numbers": "الرجاء إدخال رقم هاتف واحد على الأقل",
                "no_valid_numbers": "لم يتم العثور على أرقام صالحة",
                "invalid_numbers": "أرقام غير صالحة",
                "numbers_skipped": "تم تخطي الأرقام التالية لأنها غير صالحة:\n",
                "success": "نجاح",
                "copied_clipboard": "تم نسخ الرابط إلى الحافظة!",
                "all_copied": "تم نسخ جميع الروابط إلى الحافظة!",
                "error": "خطأ",
                "no_link_copy": "لا يوجد رابط للنسخ. الرجاء إنشاء رابط أولاً.",
                "no_links_copy": "لا توجد روابط للنسخ. الرجاء إنشاء روابط أولاً.",
                "save_settings": "حفظ الإعدادات الحالية",
                "settings_saved": "تم حفظ الإعدادات بنجاح!",
                "reset_settings": "إعادة التعيين إلى الافتراضي",
                "settings_reset": "تم إعادة تعيين الإعدادات إلى القيم الافتراضية!",
                "about_title": "مولد روابط واتساب",
                "about_description": "تساعد هذه الأداة في إنشاء روابط واتساب مع رسائل مملوءة مسبقًا.",
                "features": "الميزات:",
                "feature1": "إنشاء روابط واتساب فردية",
                "feature2": "إنشاء روابط متعددة في وقت واحد",
                "feature3": "تخصيص الرسائل باستخدام متغيرات",
                "feature4": "نسخ الروابط إلى الحافظة",
                "feature5": "لا تتطلب تبعيات خارجية",
                "feature6": "دعم الوضع الداكن/الفاتح",
                "feature7": "واجهة متعددة اللغات (15 لغة)",
                "feature8": "تُحفظ الإعدادات والتخطيط وآخر إدخال في setting_wa.ini",
                "usage_tips": "نصائح الاستخدام:",
                "tip1": "قم دائمًا بتضمين رمز الدولة بدون '+' أو '00' (مثال: 966512345678 للسعودية)",
                "tip2": "يتم ترميز الرسائل تلقائيًا لعنوان URL",
                "tip3": "استخدم {الاسم}، {التاريخ}، {الشركة} كعناصر نائبة في الوضع المتقدم",
                "tip4": "يجب أن تحتوي أرقام الهواتف على أرقام فقط",
                "link_formats": "تنسيقات الروابط:",
                "wa_format_example": "تنسيق wa.me: https://wa.me/966512345678?text=مرحبا",
                "api_format_example": "تنسيق API: https://api.whatsapp.com/send?phone=966512345678&text=مرحبا",
                "created_by": "تم الإنشاء بواسطة:",
                "copyright": "حقوق النشر © ECOMTECH 2025 - جميع الحقوق محفوظة",
                "note": "ملاحظة: لا تقوم هذه الأداة بتخزين أي بيانات وتعمل محليًا على جهاز الكمبيوتر الخاص بك."
            },
            "Hindi": {
                "window_title": "WhatsApp लिंक जनरेटर",
                "theme_btn_dark": "लाइट थीम पर स्विच करें",
                "theme_btn_light": "डार्क थीम पर स्विच करें",
                "simple_tab": "सरल जनरेटर",
                "advanced_tab": "उन्नत जनरेटर",
                "about_tab": "के बारे में",
                "phone_number": "फोन नंबर",
                "phone_help": "देश कोड के साथ फोन नंबर दर्ज करें (उदाहरण: भारत के लिए 919876543210)",
                "phone_placeholder": "उदाहरण: 919876543210",
                "message": "संदेश (वैकल्पिक)",
                "message_placeholder": "अपना संदेश यहाँ दर्ज करें...",
                "wa_format": "wa.me प्रारूप का उपयोग करें (अनुशंसित)",
                "generate_btn": "WhatsApp लिंक जनरेट करें",
                "generated_link": "जनरेट किया गया लिंक",
                "copy_btn": "क्लिपबोर्ड पर कॉपी करें",
                "multiple_numbers": "कई फोन नंबर",
                "multiple_numbers_help": "कई फोन नंबर दर्ज करें (एक प्रति पंक्ति) देश कोड के साथ",
                "multiple_numbers_placeholder": "919876543210\n919812345678\n919955566677",
                "message_options": "संदेश विकल्प",
                "quick_insert": "त्वरित सम्मिलन:",
                "name_btn": "{नाम}",
                "date_btn": "{तारीख}",
                "company_btn": "{कंपनी}",
                "advanced_options": "उन्नत विकल्प",
                "use_web": "web.whatsapp.com का उपयोग करें (डेस्कटॉप)",
                "generate_multiple": "कई लिंक जनरेट करें",
                "generated_links": "जनरेट किए गए लिंक",
                "links_placeholder": "जनरेट किए गए लिंक यहाँ दिखाई देंगे...",
                "copy_all": "सभी लिंक कॉपी करें",
                "input_error": "इनपुट त्रुटि",
                "enter_phone": "कृपया एक फोन नंबर दर्ज करें",
                "valid_phone": "कृपया एक वैध फोन नंबर दर्ज करें (केवल अंक)",
                "enter_numbers": "कृपया कम से कम एक फोन नंबर दर्ज करें",
                "no_valid_numbers": "कोई वैध नंबर नहीं मिला",
                "invalid_numbers": "अमान्य नंबर",
                "numbers_skipped": "निम्नलिखित नंबर अमान्य थे और छोड़ दिए गए:\n",
                "success": "सफलता",
                "copied_clipboard": "लिंक क्लिपबोर्ड पर कॉपी किया गया!",
                "all_copied": "सभी लिंक क्लिपबोर्ड पर कॉपी किए गए!",
                "error": "त्रुटि",
                "no_link_copy": "कॉपी करने के लिए कोई लिंक नहीं। कृपया पहले एक लिंक जनरेट करें।",
                "no_links_copy": "कॉपी करने के लिए कोई लिंक नहीं। कृपया पहले लिंक जनरेट करें।",
                "save_settings": "वर्तमान सेटिंग्स सहेजें",
                "settings_saved": "सेटिंग्स सफलतापूर्वक सहेजी गईं!",
                "reset_settings": "डिफ़ॉल्ट पर रीसेट करें",
                "settings_reset": "सेटिंग्स डिफ़ॉल्ट पर रीसेट हो गईं!",
                "about_title": "WhatsApp लिंक जनरेटर",
                "about_description": "यह टूल पूर्व-भरे हुए संदेशों के साथ WhatsApp लिंक बनाने में मदद करता है।",
                "features": "विशेषताएँ:",
                "feature1": "व्यक्तिगत WhatsApp लिंक जनरेट करें",
                "feature2": "एक साथ कई लिंक बनाएं",
                "feature3": "चर के साथ संदेश अनुकूलित करें",
                "feature4": "लिंक को क्लिपबोर्ड पर कॉपी करें",
                "feature5": "कोई बाहरी निर्भरता आवश्यक नहीं",
                "feature6": "डार्क/लाइट थीम समर्थन",
                "feature7": "बहुभाषी इंटरफ़ेस (15 भाषाएं)",
                "feature8": "सेटिंग, लेआउट और अंतिम इनपुट setting_wa.ini में सहेजे जाते हैं",
                "usage_tips": "उपयोग युक्तियाँ:",
                "tip1": "हमेशा देश कोड '+' या '00' के बिना शामिल करें (उदाहरण: भारत के लिए 919876543210)",
                "tip2": "संदेश स्वचालित रूप से URL-एन्कोडेड होते हैं",
                "tip3": "उन्नत मोड में प्लेसहोल्डर के रूप में {नाम}, {तारीख}, {कंपनी} का उपयोग करें",
                "tip4": "फोन नंबर में केवल अंक होने चाहिए",
                "link_formats": "लिंक प्रारूप:",
                "wa_format_example": "wa.me प्रारूप: https://wa.me/919876543210?text=नमस्ते",
                "api_format_example": "API प्रारूप: https://api.whatsapp.com/send?phone=919876543210&text=नमस्ते",
                "created_by": "द्वारा निर्मित:",
                "copyright": "कॉपीराइट © ECOMTECH 2025 - सभी अधिकार सुरक्षित",
                "note": "नोट: यह टूल कोई डेटा संग्रहीत नहीं करता है और आपके कंप्यूटर पर स्थानीय रूप से चलता है।"
            },
            "Turkish": {
                "window_title": "WhatsApp Bağlantı Oluşturucu",
                "theme_btn_dark": "Açık Tema'ya Geç",
                "theme_btn_light": "Koyu Tema'ya Geç",
                "simple_tab": "Basit Oluşturucu",
                "advanced_tab": "Gelişmiş Oluşturucu",
                "about_tab": "Hakkında",
                "phone_number": "Telefon Numarası",
                "phone_help": "Ülke kodu ile telefon numarası girin (örnek: Türkiye için 905551234567)",
                "phone_placeholder": "örnek: 905551234567",
                "message": "Mesaj (İsteğe Bağlı)",
                "message_placeholder": "Mesajınızı buraya girin...",
                "wa_format": "wa.me formatını kullan (tavsiye edilir)",
                "generate_btn": "WhatsApp Bağlantısı Oluştur",
                "generated_link": "Oluşturulan Bağlantı",
                "copy_btn": "Panoya Kopyala",
                "multiple_numbers": "Birden Fazla Telefon Numarası",
                "multiple_numbers_help": "Birden fazla telefon numarası girin (satır başına bir tane) ülke kodu ile",
                "multiple_numbers_placeholder": "905551234567\n905556789012\n905555666777",
                "message_options": "Mesaj Seçenekleri",
                "quick_insert": "Hızlı ekle:",
                "name_btn": "{isim}",
                "date_btn": "{tarih}",
                "company_btn": "{şirket}",
                "advanced_options": "Gelişmiş Seçenekler",
                "use_web": "web.whatsapp.com kullan (masaüstü)",
                "generate_multiple": "Birden Fazla Bağlantı Oluştur",
                "generated_links": "Oluşturulan Bağlantılar",
                "links_placeholder": "Oluşturulan bağlantılar burada görünecek...",
                "copy_all": "Tüm Bağlantıları Kopyala",
                "input_error": "Giriş Hatası",
                "enter_phone": "Lütfen bir telefon numarası girin",
                "valid_phone": "Lütfen geçerli bir telefon numarası girin (sadece rakam)",
                "enter_numbers": "Lütfen en az bir telefon numarası girin",
                "no_valid_numbers": "Geçerli numara bulunamadı",
                "invalid_numbers": "Geçersiz Numaralar",
                "numbers_skipped": "Aşağıdaki numaralar geçersizdi ve atlandı:\n",
                "success": "Başarılı",
                "copied_clipboard": "Bağlantı panoya kopyalandı!",
                "all_copied": "Tüm bağlantılar panoya kopyalandı!",
                "error": "Hata",
                "no_link_copy": "Kopyalanacak bağlantı yok. Lütfen önce bir bağlantı oluşturun.",
                "no_links_copy": "Kopyalanacak bağlantı yok. Lütfen önce bağlantı oluşturun.",
                "save_settings": "Mevcut Ayarları Kaydet",
                "settings_saved": "Ayarlar başarıyla kaydedildi!",
                "reset_settings": "Varsayılanlara Sıfırla",
                "settings_reset": "Ayarlar varsayılan değerlere sıfırlandı!",
                "about_title": "WhatsApp Bağlantı Oluşturucu",
                "about_description": "Bu araç, önceden doldurulmuş mesajlarla WhatsApp bağlantıları oluşturmanıza yardımcı olur.",
                "features": "Özellikler:",
                "feature1": "Bireysel WhatsApp bağlantıları oluşturun",
                "feature2": "Aynı anda birden fazla bağlantı oluşturun",
                "feature3": "Değişkenlerle mesajları özelleştirin",
                "feature4": "Bağlantıları panoya kopyalayın",
                "feature5": "Harici bağımlılık gerekmez",
                "feature6": "Koyu/Açık tema desteği",
                "feature7": "Çok dilli arayüz (15 dil)",
                "feature8": "Ayarlar, düzen ve son giriş setting_wa.ini içinde saklanır",
                "usage_tips": "Kullanım İpuçları:",
                "tip1": "Her zaman '+' veya '00' olmadan ülke kodunu ekleyin (örnek: Türkiye için 905551234567)",
                "tip2": "Mesajlar otomatik olarak URL kodlanır",
                "tip3": "Gelişmiş modda yer tutucu olarak {isim}, {tarih}, {şirket} kullanın",
                "tip4": "Telefon numaraları sadece rakam içermelidir",
                "link_formats": "Bağlantı Formatları:",
                "wa_format_example": "wa.me formatı: https://wa.me/905551234567?text=Merhaba",
                "api_format_example": "API formatı: https://api.whatsapp.com/send?phone=905551234567&text=Merhaba",
                "created_by": "Tarafından Oluşturuldu:",
                "copyright": "Telif Hakkı © ECOMTECH 2025 - Tüm Hakları Saklıdır",
                "note": "Not: Bu araç hiçbir veri depolamaz ve bilgisayarınızda yerel olarak çalışır."
            },
            "Italian": {
                "window_title": "Generatore Link WhatsApp",
                "theme_btn_dark": "Passa a Tema Chiaro",
                "theme_btn_light": "Passa a Tema Scuro",
                "simple_tab": "Generatore Semplice",
                "advanced_tab": "Generatore Avanzato",
                "about_tab": "Informazioni",
                "phone_number": "Numero di Telefono",
                "phone_help": "Inserisci numero con prefisso internazionale (es: 393331234567 per Italia)",
                "phone_placeholder": "es: 393331234567",
                "message": "Messaggio (Opzionale)",
                "message_placeholder": "Inserisci il tuo messaggio qui...",
                "wa_format": "Usa formato wa.me (consigliato)",
                "generate_btn": "Genera Link WhatsApp",
                "generated_link": "Link Generato",
                "copy_btn": "Copia negli Appunti",
                "multiple_numbers": "Più Numeri di Telefono",
                "multiple_numbers_help": "Inserisci più numeri (uno per riga) con prefisso internazionale",
                "multiple_numbers_placeholder": "393331234567\n393339876543\n393355566677",
                "message_options": "Opzioni Messaggio",
                "quick_insert": "Inserimento rapido:",
                "name_btn": "{nome}",
                "date_btn": "{data}",
                "company_btn": "{azienda}",
                "advanced_options": "Opzioni Avanzate",
                "use_web": "Usa web.whatsapp.com (desktop)",
                "generate_multiple": "Genera Più Link",
                "generated_links": "Link Generati",
                "links_placeholder": "I link generati appariranno qui...",
                "copy_all": "Copia Tutti i Link",
                "input_error": "Errore di Input",
                "enter_phone": "Per favore inserisci un numero di telefono",
                "valid_phone": "Per favore inserisci un numero valido (solo cifre)",
                "enter_numbers": "Per favore inserisci almeno un numero di telefono",
                "no_valid_numbers": "Nessun numero valido trovato",
                "invalid_numbers": "Numeri Non Validi",
                "numbers_skipped": "I seguenti numeri non erano validi e sono stati saltati:\n",
                "success": "Successo",
                "copied_clipboard": "Link copiato negli appunti!",
                "all_copied": "Tutti i link copiati negli appunti!",
                "error": "Errore",
                "no_link_copy": "Nessun link da copiare. Per favore genera prima un link.",
                "no_links_copy": "Nessun link da copiare. Per favore genera prima i link.",
                "save_settings": "Salva Impostazioni Correnti",
                "settings_saved": "Impostazioni salvate con successo!",
                "reset_settings": "Ripristina Predefiniti",
                "settings_reset": "Impostazioni ripristinate ai valori predefiniti!",
                "about_title": "Generatore Link WhatsApp",
                "about_description": "Questo strumento aiuta a creare link WhatsApp con messaggi precompilati.",
                "features": "Caratteristiche:",
                "feature1": "Genera singoli link WhatsApp",
                "feature2": "Crea più link contemporaneamente",
                "feature3": "Personalizza messaggi con variabili",
                "feature4": "Copia link negli appunti",
                "feature5": "Nessuna dipendenza esterna richiesta",
                "feature6": "Supporto tema Scuro/Chiaro",
                "feature7": "Interfaccia multilingue (15 lingue)",
                "feature8": "Impostazioni, layout e ultimo input salvati in setting_wa.ini",
                "usage_tips": "Suggerimenti d'Uso:",
                "tip1": "Includi sempre il prefisso internazionale senza '+' o '00' (es: 393331234567 per Italia)",
                "tip2": "I messaggi sono codificati URL automaticamente",
                "tip3": "Usa {nome}, {data}, {azienda} come segnaposto in modalità avanzata",
                "tip4": "I numeri di telefono devono contenere solo cifre",
                "link_formats": "Formati Link:",
                "wa_format_example": "Formato wa.me: https://wa.me/393331234567?text=Ciao",
                "api_format_example": "Formato API: https://api.whatsapp.com/send?phone=393331234567&text=Ciao",
                "created_by": "Creato Da:",
                "copyright": "Copyright © ECOMTECH 2025 - Tutti i Diritti Riservati",
                "note": "Nota: Questo strumento non memorizza dati e viene eseguito localmente sul tuo computer."
            },
            "Korean": {
                "window_title": "WhatsApp 링크 생성기",
                "theme_btn_dark": "밝은 테마로 전환",
                "theme_btn_light": "어두운 테마로 전환",
                "simple_tab": "단순 생성기",
                "advanced_tab": "고급 생성기",
                "about_tab": "정보",
                "phone_number": "전화번호",
                "phone_help": "국가 코드와 함께 전화번호 입력 (예: 한국의 경우 821012345678)",
                "phone_placeholder": "예: 821012345678",
                "message": "메시지 (선택사항)",
                "message_placeholder": "메시지를 입력하세요...",
                "wa_format": "wa.me 형식 사용 (권장)",
                "generate_btn": "WhatsApp 링크 생성",
                "generated_link": "생성된 링크",
                "copy_btn": "클립보드에 복사",
                "multiple_numbers": "여러 전화번호",
                "multiple_numbers_help": "여러 전화번호 입력 (한 줄에 하나씩) 국가 코드 포함",
                "multiple_numbers_placeholder": "821012345678\n821098765432\n8210555666777",
                "message_options": "메시지 옵션",
                "quick_insert": "빠른 삽입:",
                "name_btn": "{이름}",
                "date_btn": "{날짜}",
                "company_btn": "{회사}",
                "advanced_options": "고급 옵션",
                "use_web": "web.whatsapp.com 사용 (데스크톱)",
                "generate_multiple": "여러 링크 생성",
                "generated_links": "생성된 링크",
                "links_placeholder": "생성된 링크가 여기에 표시됩니다...",
                "copy_all": "모든 링크 복사",
                "input_error": "입력 오류",
                "enter_phone": "전화번호를 입력하세요",
                "valid_phone": "유효한 전화번호를 입력하세요 (숫자만)",
                "enter_numbers": "적어도 하나의 전화번호를 입력하세요",
                "no_valid_numbers": "유효한 번호를 찾을 수 없습니다",
                "invalid_numbers": "유효하지 않은 번호",
                "numbers_skipped": "다음 번호가 유효하지 않아 건너뛰었습니다:\n",
                "success": "성공",
                "copied_clipboard": "링크가 클립보드에 복사되었습니다!",
                "all_copied": "모든 링크가 클립보드에 복사되었습니다!",
                "error": "오류",
                "no_link_copy": "복사할 링크가 없습니다. 먼저 링크를 생성하세요.",
                "no_links_copy": "복사할 링크가 없습니다. 먼저 링크를 생성하세요.",
                "save_settings": "현재 설정 저장",
                "settings_saved": "설정이 성공적으로 저장되었습니다!",
                "reset_settings": "기본값으로 재설정",
                "settings_reset": "설정이 기본값으로 재설정되었습니다!",
                "about_title": "WhatsApp 링크 생성기",
                "about_description": "이 도구는 미리 채워진 메시지로 WhatsApp 링크를 만드는 데 도움이 됩니다.",
                "features": "기능:",
                "feature1": "개별 WhatsApp 링크 생성",
                "feature2": "한 번에 여러 링크 생성",
                "feature3": "변수로 메시지 사용자 정의",
                "feature4": "링크를 클립보드에 복사",
                "feature5": "외부 종속성 필요 없음",
                "feature6": "어두운/밝은 테마 지원",
                "feature7": "다국어 인터페이스 (15개 언어)",
                "feature8": "설정, 레이아웃 및 마지막 입력을 setting_wa.ini에 저장",
                "usage_tips": "사용 팁:",
                "tip1": "항상 '+' 또는 '00' 없이 국가 코드를 포함하세요 (예: 한국의 경우 821012345678)",
                "tip2": "메시지는 자동으로 URL 인코딩됩니다",
                "tip3": "고급 모드에서 {이름}, {날짜}, {회사}를 플레이스홀더로 사용하세요",
                "tip4": "전화번호는 숫자만 포함해야 합니다",
                "link_formats": "링크 형식:",
                "wa_format_example": "wa.me 형식: https://wa.me/821012345678?text=안녕하세요",
                "api_format_example": "API 형식: https://api.whatsapp.com/send?phone=821012345678&text=안녕하세요",
                "created_by": "제작자:",
                "copyright": "저작권 © ECOMTECH 2025 - 모든 권리 보유",
                "note": "참고: 이 도구는 데이터를 저장하지 않으며 컴퓨터에서 로컬로 실행됩니다."
            },
            "Vietnamese": {
                "window_title": "Trình Tạo Liên Kết WhatsApp",
                "theme_btn_dark": "Chuyển sang Chế độ Sáng",
                "theme_btn_light": "Chuyển sang Chế độ Tối",
                "simple_tab": "Trình Tạo Đơn Giản",
                "advanced_tab": "Trình Tạo Nâng Cao",
                "about_tab": "Thông Tin",
                "phone_number": "Số Điện Thoại",
                "phone_help": "Nhập số điện thoại với mã quốc gia (ví dụ: Việt Nam là 84912345678)",
                "phone_placeholder": "ví dụ: 84912345678",
                "message": "Tin Nhắn (Tùy chọn)",
                "message_placeholder": "Nhập tin nhắn của bạn tại đây...",
                "wa_format": "Sử dụng định dạng wa.me (đề xuất)",
                "generate_btn": "Tạo Liên Kết WhatsApp",
                "generated_link": "Liên Kết Đã Tạo",
                "copy_btn": "Sao chép vào Bộ nhớ tạm",
                "multiple_numbers": "Nhiều Số Điện Thoại",
                "multiple_numbers_help": "Nhập nhiều số điện thoại (mỗi dòng một số) với mã quốc gia",
                "multiple_numbers_placeholder": "84912345678\n84987654321\n849555666777",
                "message_options": "Tùy chọn Tin nhắn",
                "quick_insert": "Chèn nhanh:",
                "name_btn": "{tên}",
                "date_btn": "{ngày}",
                "company_btn": "{công ty}",
                "advanced_options": "Tùy chọn Nâng cao",
                "use_web": "Sử dụng web.whatsapp.com (máy tính)",
                "generate_multiple": "Tạo Nhiều Liên Kết",
                "generated_links": "Liên Kết Đã Tạo",
                "links_placeholder": "Liên kết đã tạo sẽ xuất hiện ở đây...",
                "copy_all": "Sao chép Tất cả Liên kết",
                "input_error": "Lỗi Nhập liệu",
                "enter_phone": "Vui lòng nhập số điện thoại",
                "valid_phone": "Vui lòng nhập số điện thoại hợp lệ (chỉ chữ số)",
                "enter_numbers": "Vui lòng nhập ít nhất một số điện thoại",
                "no_valid_numbers": "Không tìm thấy số hợp lệ",
                "invalid_numbers": "Số Không Hợp lệ",
                "numbers_skipped": "Các số sau không hợp lệ và đã bị bỏ qua:\n",
                "success": "Thành công",
                "copied_clipboard": "Đã sao chép liên kết vào bộ nhớ tạm!",
                "all_copied": "Đã sao chép tất cả liên kết vào bộ nhớ tạm!",
                "error": "Lỗi",
                "no_link_copy": "Không có liên kết để sao chép. Vui lòng tạo liên kết trước.",
                "no_links_copy": "Không có liên kết để sao chép. Vui lòng tạo liên kết trước.",
                "save_settings": "Lưu Cài đặt Hiện tại",
                "settings_saved": "Đã lưu cài đặt thành công!",
                "reset_settings": "Đặt lại về Mặc định",
                "settings_reset": "Đã đặt lại cài đặt về mặc định!",
                "about_title": "Trình Tạo Liên Kết WhatsApp",
                "about_description": "Công cụ này giúp tạo liên kết WhatsApp với tin nhắn được điền sẵn.",
                "features": "Tính năng:",
                "feature1": "Tạo liên kết WhatsApp riêng lẻ",
                "feature2": "Tạo nhiều liên kết cùng lúc",
                "feature3": "Tùy chỉnh tin nhắn với biến",
                "feature4": "Sao chép liên kết vào bộ nhớ tạm",
                "feature5": "Không cần phụ thuộc bên ngoài",
                "feature6": "Hỗ trợ chế độ Tối/Sáng",
                "feature7": "Giao diện đa ngôn ngữ (15 ngôn ngữ)",
                "feature8": "Cài đặt, bố cục và dữ liệu nhập cuối được lưu trong setting_wa.ini",
                "usage_tips": "Mẹo sử dụng:",
                "tip1": "Luôn bao gồm mã quốc gia không có '+' hoặc '00' (ví dụ: Việt Nam là 84912345678)",
                "tip2": "Tin nhắn được mã hóa URL tự động",
                "tip3": "Sử dụng {tên}, {ngày}, {công ty} làm trình giữ chỗ trong chế độ nâng cao",
                "tip4": "Số điện thoại chỉ nên chứa chữ số",
                "link_formats": "Định dạng Liên kết:",
                "wa_format_example": "Định dạng wa.me: https://wa.me/84912345678?text=Xin chào",
                "api_format_example": "Định dạng API: https://api.whatsapp.com/send?phone=84912345678&text=Xin chào",
                "created_by": "Được Tạo Bởi:",
                "copyright": "Bản quyền © ECOMTECH 2025 - Đã đăng ký bản quyền",
                "note": "Lưu ý: Công cụ này không lưu trữ dữ liệu và chạy cục bộ trên máy tính của bạn."
            },
            "Thai": {
                "window_title": "ตัวสร้างลิงก์ WhatsApp",
                "theme_btn_dark": "สลับเป็นธีมสว่าง",
                "theme_btn_light": "สลับเป็นธีมมืด",
                "simple_tab": "ตัวสร้างแบบง่าย",
                "advanced_tab": "ตัวสร้างขั้นสูง",
                "about_tab": "เกี่ยวกับ",
                "phone_number": "หมายเลขโทรศัพท์",
                "phone_help": "ป้อนหมายเลขโทรศัพท์พร้อมรหัสประเทศ (เช่น 66811234567 สำหรับไทย)",
                "phone_placeholder": "เช่น 66811234567",
                "message": "ข้อความ (ไม่จำเป็น)",
                "message_placeholder": "ป้อนข้อความของคุณที่นี่...",
                "wa_format": "ใช้รูปแบบ wa.me (แนะนำ)",
                "generate_btn": "สร้างลิงก์ WhatsApp",
                "generated_link": "ลิงก์ที่สร้าง",
                "copy_btn": "คัดลอกไปยังคลิปบอร์ด",
                "multiple_numbers": "หลายหมายเลขโทรศัพท์",
                "multiple_numbers_help": "ป้อนหลายหมายเลขโทรศัพท์ (หนึ่งหมายเลขต่อบรรทัด) พร้อมรหัสประเทศ",
                "multiple_numbers_placeholder": "66811234567\n66899876543\n668555666777",
                "message_options": "ตัวเลือกข้อความ",
                "quick_insert": "แทรกด่วน:",
                "name_btn": "{ชื่อ}",
                "date_btn": "{วันที่}",
                "company_btn": "{บริษัท}",
                "advanced_options": "ตัวเลือกขั้นสูง",
                "use_web": "ใช้ web.whatsapp.com (เดสก์ท็อป)",
                "generate_multiple": "สร้างหลายลิงก์",
                "generated_links": "ลิงก์ที่สร้าง",
                "links_placeholder": "ลิงก์ที่สร้างจะปรากฏที่นี่...",
                "copy_all": "คัดลอกทุกลิงก์",
                "input_error": "ข้อผิดพลาดในการป้อนข้อมูล",
                "enter_phone": "กรุณาป้อนหมายเลขโทรศัพท์",
                "valid_phone": "กรุณาป้อนหมายเลขโทรศัพท์ที่ถูกต้อง (ตัวเลขเท่านั้น)",
                "enter_numbers": "กรุณาป้อนหมายเลขโทรศัพท์อย่างน้อยหนึ่งหมายเลข",
                "no_valid_numbers": "ไม่พบหมายเลขที่ถูกต้อง",
                "invalid_numbers": "หมายเลขไม่ถูกต้อง",
                "numbers_skipped": "หมายเลขต่อไปนี้ไม่ถูกต้องและถูกข้าม:\n",
                "success": "สำเร็จ",
                "copied_clipboard": "คัดลอกลิงก์ไปยังคลิปบอร์ดแล้ว!",
                "all_copied": "คัดลอกทุกลิงก์ไปยังคลิปบอร์ดแล้ว!",
                "error": "ข้อผิดพลาด",
                "no_link_copy": "ไม่มีลิงก์ให้คัดลอก กรุณาสร้างลิงก์ก่อน",
                "no_links_copy": "ไม่มีลิงก์ให้คัดลอก กรุณาสร้างลิงก์ก่อน",
                "save_settings": "บันทึกการตั้งค่าปัจจุบัน",
                "settings_saved": "บันทึกการตั้งค่าเรียบร้อยแล้ว!",
                "reset_settings": "รีเซ็ตเป็นค่าเริ่มต้น",
                "settings_reset": "รีเซ็ตการตั้งค่าเป็นค่าเริ่มต้นแล้ว!",
                "about_title": "ตัวสร้างลิงก์ WhatsApp",
                "about_description": "เครื่องมือนี้ช่วยสร้างลิงก์ WhatsApp พร้อมข้อความที่กรอกไว้ล่วงหน้า",
                "features": "คุณสมบัติ:",
                "feature1": "สร้างลิงก์ WhatsApp แต่ละอัน",
                "feature2": "สร้างหลายลิงก์พร้อมกัน",
                "feature3": "ปรับแต่งข้อความด้วยตัวแปร",
                "feature4": "คัดลอกลิงก์ไปยังคลิปบอร์ด",
                "feature5": "ไม่ต้องพึ่งพาภายนอก",
                "feature6": "รองรับธีมมืด/สว่าง",
                "feature7": "อินเทอร์เฟซหลายภาษา (15 ภาษา)",
                "feature8": "บันทึกการตั้งค่า เลย์เอาต์ และข้อมูลล่าสุดใน setting_wa.ini",
                "usage_tips": "เคล็ดลับการใช้งาน:",
                "tip1": "ใส่รหัสประเทศโดยไม่มี '+' หรือ '00' เสมอ (เช่น 66811234567 สำหรับไทย)",
                "tip2": "ข้อความถูกเข้ารหัส URL อัตโนมัติ",
                "tip3": "ใช้ {ชื่อ}, {วันที่}, {บริษัท} เป็นตัวยึดในโหมดขั้นสูง",
                "tip4": "หมายเลขโทรศัพท์ควรมีเฉพาะตัวเลข",
                "link_formats": "รูปแบบลิงก์:",
                "wa_format_example": "รูปแบบ wa.me: https://wa.me/66811234567?text=สวัสดี",
                "api_format_example": "รูปแบบ API: https://api.whatsapp.com/send?phone=66811234567&text=สวัสดี",
                "created_by": "สร้างโดย:",
                "copyright": "ลิขสิทธิ์ © ECOMTECH 2025 - สงวนลิขสิทธิ์",
                "note": "หมายเหตุ: เครื่องมือนี้ไม่เก็บข้อมูลและทำงานในคอมพิวเตอร์ของคุณในเครื่อง"
            },
            "Dutch": {
                "window_title": "WhatsApp Link Generator",
                "theme_btn_dark": "Schakel naar Licht Thema",
                "theme_btn_light": "Schakel naar Donker Thema",
                "simple_tab": "Eenvoudige Generator",
                "advanced_tab": "Geavanceerde Generator",
                "about_tab": "Over",
                "phone_number": "Telefoonnummer",
                "phone_help": "Voer telefoonnummer in met landcode (bijv. 31612345678 voor Nederland)",
                "phone_placeholder": "bijv. 31612345678",
                "message": "Bericht (Optioneel)",
                "message_placeholder": "Voer uw bericht hier in...",
                "wa_format": "Gebruik wa.me formaat (aanbevolen)",
                "generate_btn": "Genereer WhatsApp Link",
                "generated_link": "Gegenereerde Link",
                "copy_btn": "Kopieer naar Klembord",
                "multiple_numbers": "Meerdere Telefoonnummers",
                "multiple_numbers_help": "Voer meerdere telefoonnummers in (één per regel) met landcode",
                "multiple_numbers_placeholder": "31612345678\n31698765432\n316555666777",
                "message_options": "Bericht Opties",
                "quick_insert": "Snel invoegen:",
                "name_btn": "{naam}",
                "date_btn": "{datum}",
                "company_btn": "{bedrijf}",
                "advanced_options": "Geavanceerde Opties",
                "use_web": "Gebruik web.whatsapp.com (desktop)",
                "generate_multiple": "Genereer Meerdere Links",
                "generated_links": "Gegenereerde Links",
                "links_placeholder": "Gegenereerde links verschijnen hier...",
                "copy_all": "Kopieer Alle Links",
                "input_error": "Invoerfout",
                "enter_phone": "Voer een telefoonnummer in",
                "valid_phone": "Voer een geldig telefoonnummer in (alleen cijfers)",
                "enter_numbers": "Voer minstens één telefoonnummer in",
                "no_valid_numbers": "Geen geldige nummers gevonden",
                "invalid_numbers": "Ongeldige Nummers",
                "numbers_skipped": "De volgende nummers waren ongeldig en overgeslagen:\n",
                "success": "Succes",
                "copied_clipboard": "Link gekopieerd naar klembord!",
                "all_copied": "Alle links gekopieerd naar klembord!",
                "error": "Fout",
                "no_link_copy": "Geen link om te kopiëren. Genereer eerst een link.",
                "no_links_copy": "Geen links om te kopiëren. Genereer eerst links.",
                "save_settings": "Huidige Instellingen Opslaan",
                "settings_saved": "Instellingen succesvol opgeslagen!",
                "reset_settings": "Reset naar Standaardwaarden",
                "settings_reset": "Instellingen gereset naar standaardwaarden!",
                "about_title": "WhatsApp Link Generator",
                "about_description": "Deze tool helpt bij het maken van WhatsApp links met vooringevulde berichten.",
                "features": "Functies:",
                "feature1": "Genereer individuele WhatsApp links",
                "feature2": "Creëer meerdere links tegelijk",
                "feature3": "Pas berichten aan met variabelen",
                "feature4": "Kopieer links naar klembord",
                "feature5": "Geen externe afhankelijkheden nodig",
                "feature6": "Donker/Licht thema ondersteuning",
                "feature7": "Meertalige interface (15 talen)",
                "feature8": "Instellingen, lay-out en laatste invoer opgeslagen in setting_wa.ini",
                "usage_tips": "Gebruikstips:",
                "tip1": "Voeg altijd landcode toe zonder '+' of '00' (bijv. 31612345678 voor Nederland)",
                "tip2": "Berichten worden automatisch URL-gecodeerd",
                "tip3": "Gebruik {naam}, {datum}, {bedrijf} als plaatshouders in geavanceerde modus",
                "tip4": "Telefoonnummers moeten alleen cijfers bevatten",
                "link_formats": "Link Formaten:",
                "wa_format_example": "wa.me formaat: https://wa.me/31612345678?text=Hallo",
                "api_format_example": "API formaat: https://api.whatsapp.com/send?phone=31612345678&text=Hallo",
                "created_by": "Gemaakt Door:",
                "copyright": "Copyright © ECOMTECH 2025 - Alle Rechten Voorbehouden",
                "note": "Opmerking: Deze tool slaat geen gegevens op en wordt lokaal op uw computer uitgevoerd."
            }
        }
        

    def initUI(self):
        self.setWindowTitle(self.languages[self.current_language]["window_title"])
        self.resize(*self.DEFAULT_SIZE)
        self.setMinimumSize(760, 600)

        self.create_menu_bar()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        top_layout = QHBoxLayout()
        self.language_label = QLabel("Language / Bahasa:")
        top_layout.addWidget(self.language_label)

        self.lang_combo = QComboBox()
        self.lang_combo.addItems(self.languages.keys())
        self.lang_combo.setCurrentText(self.current_language)
        self.lang_combo.currentTextChanged.connect(self.change_language)
        top_layout.addWidget(self.lang_combo)

        top_layout.addStretch()
        self.theme_label = QLabel("Theme:")
        top_layout.addWidget(self.theme_label)

        self.theme_combo = QComboBox()
        for key, theme in self.THEMES.items():
            self.theme_combo.addItem(theme["label"], key)
        self.theme_combo.setCurrentIndex(max(0, self.theme_combo.findData(self.current_theme)))
        self.theme_combo.currentIndexChanged.connect(self.change_theme_from_combo)
        top_layout.addWidget(self.theme_combo)
        main_layout.addLayout(top_layout)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.currentChanged.connect(self.update_preview)
        main_layout.addWidget(self.tabs, 1)

        self.create_simple_tab()
        self.create_advanced_tab()
        self.create_settings_tab()
        self.create_about_tab()
        self.create_preview_dock()

        self.apply_theme(self.current_theme)
        self.statusBar().showMessage("Ready")

    def create_menu_bar(self):
        help_menu = self.menuBar().addMenu("&Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about_tab)
        help_menu.addAction(about_action)

    def create_simple_tab(self):
        simple_tab = QWidget()
        layout = QVBoxLayout(simple_tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        self.phone_group = QGroupBox()
        phone_layout = QVBoxLayout(self.phone_group)
        self.phone_help_label = QLabel()
        self.phone_help_label.setObjectName("helpLabel")
        self.phone_help_label.setWordWrap(True)
        phone_layout.addWidget(self.phone_help_label)
        self.phone_input = QLineEdit()
        self.phone_input.setClearButtonEnabled(True)
        self.phone_input.textChanged.connect(self.update_preview)
        phone_layout.addWidget(self.phone_input)
        layout.addWidget(self.phone_group)

        self.message_group = QGroupBox()
        message_layout = QVBoxLayout(self.message_group)
        self.message_input = QTextEdit()
        self.message_input.setMaximumHeight(130)
        self.message_input.textChanged.connect(self.update_preview)
        message_layout.addWidget(self.message_input)
        layout.addWidget(self.message_group)

        self.include_country_code = QCheckBox()
        self.include_country_code.setChecked(self.wa_format)
        self.include_country_code.toggled.connect(self.sync_format_controls)
        self.include_country_code.toggled.connect(self.update_preview)
        layout.addWidget(self.include_country_code)

        self.generate_btn = QPushButton()
        self.generate_btn.setObjectName("primaryButton")
        self.generate_btn.clicked.connect(self.generate_simple_link)
        layout.addWidget(self.generate_btn)

        self.result_group = QGroupBox()
        result_layout = QVBoxLayout(self.result_group)
        self.result_output = QTextEdit()
        self.result_output.setMaximumHeight(90)
        self.result_output.setReadOnly(True)
        result_layout.addWidget(self.result_output)
        self.copy_btn = QPushButton()
        self.copy_btn.setObjectName("secondaryButton")
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        result_layout.addWidget(self.copy_btn)
        layout.addWidget(self.result_group)
        layout.addStretch()

        self.tabs.addTab(simple_tab, "")
        self.retranslate_simple_tab()

    def create_advanced_tab(self):
        advanced_tab = QWidget()
        layout = QVBoxLayout(advanced_tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        self.numbers_group = QGroupBox()
        numbers_layout = QVBoxLayout(self.numbers_group)
        self.numbers_help_label = QLabel()
        self.numbers_help_label.setObjectName("helpLabel")
        self.numbers_help_label.setWordWrap(True)
        numbers_layout.addWidget(self.numbers_help_label)
        self.multiple_numbers_input = QTextEdit()
        self.multiple_numbers_input.setMaximumHeight(130)
        self.multiple_numbers_input.textChanged.connect(self.update_preview)
        numbers_layout.addWidget(self.multiple_numbers_input)
        layout.addWidget(self.numbers_group)

        self.advanced_message_group = QGroupBox()
        message_layout = QVBoxLayout(self.advanced_message_group)
        self.advanced_message_input = QTextEdit()
        self.advanced_message_input.setMaximumHeight(110)
        self.advanced_message_input.textChanged.connect(self.update_preview)
        message_layout.addWidget(self.advanced_message_input)

        variables_layout = QHBoxLayout()
        self.quick_insert_label = QLabel()
        variables_layout.addWidget(self.quick_insert_label)
        self.name_btn = QPushButton()
        self.date_btn = QPushButton()
        self.company_btn = QPushButton()
        for button in (self.name_btn, self.date_btn, self.company_btn):
            button.setObjectName("smallButton")
            variables_layout.addWidget(button)
        variables_layout.addStretch()
        self.name_btn.clicked.connect(lambda: self.insert_variable(self.languages[self.current_language]["name_btn"]))
        self.date_btn.clicked.connect(lambda: self.insert_variable(self.languages[self.current_language]["date_btn"]))
        self.company_btn.clicked.connect(lambda: self.insert_variable(self.languages[self.current_language]["company_btn"]))
        message_layout.addLayout(variables_layout)
        layout.addWidget(self.advanced_message_group)

        self.advanced_options_group = QGroupBox()
        options_layout = QVBoxLayout(self.advanced_options_group)
        self.use_web = QCheckBox()
        self.use_web.toggled.connect(self.update_preview)
        options_layout.addWidget(self.use_web)
        layout.addWidget(self.advanced_options_group)

        self.generate_advanced_btn = QPushButton()
        self.generate_advanced_btn.setObjectName("primaryButton")
        self.generate_advanced_btn.clicked.connect(self.generate_advanced_links)
        layout.addWidget(self.generate_advanced_btn)

        self.advanced_result_group = QGroupBox()
        advanced_result_layout = QVBoxLayout(self.advanced_result_group)
        self.advanced_result_output = QTextEdit()
        self.advanced_result_output.setReadOnly(True)
        advanced_result_layout.addWidget(self.advanced_result_output)
        self.copy_all_btn = QPushButton()
        self.copy_all_btn.setObjectName("secondaryButton")
        self.copy_all_btn.clicked.connect(self.copy_all_links)
        advanced_result_layout.addWidget(self.copy_all_btn)
        layout.addWidget(self.advanced_result_group, 1)

        self.tabs.addTab(advanced_tab, "")
        self.retranslate_advanced_tab()

    def create_settings_tab(self):
        settings_tab = QWidget()
        layout = QVBoxLayout(settings_tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        settings_group = QGroupBox("Application Settings")
        settings_layout = QVBoxLayout(settings_group)

        language_row = QHBoxLayout()
        language_row.addWidget(QLabel("Language:"))
        self.settings_language_combo = QComboBox()
        self.settings_language_combo.addItems(self.languages.keys())
        self.settings_language_combo.setCurrentText(self.current_language)
        self.settings_language_combo.currentTextChanged.connect(self.change_language)
        language_row.addWidget(self.settings_language_combo, 1)
        settings_layout.addLayout(language_row)

        theme_row = QHBoxLayout()
        theme_row.addWidget(QLabel("Theme:"))
        self.settings_theme_combo = QComboBox()
        for key, theme in self.THEMES.items():
            self.settings_theme_combo.addItem(theme["label"], key)
        self.settings_theme_combo.setCurrentIndex(max(0, self.settings_theme_combo.findData(self.current_theme)))
        self.settings_theme_combo.currentIndexChanged.connect(self.change_theme_from_settings)
        theme_row.addWidget(self.settings_theme_combo, 1)
        settings_layout.addLayout(theme_row)

        format_row = QHBoxLayout()
        format_row.addWidget(QLabel("Default Link Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItem("wa.me (recommended)", True)
        self.format_combo.addItem("api.whatsapp.com", False)
        self.format_combo.setCurrentIndex(0 if self.wa_format else 1)
        self.format_combo.currentIndexChanged.connect(self.sync_format_checkbox)
        format_row.addWidget(self.format_combo, 1)
        settings_layout.addLayout(format_row)

        self.preview_status_label = QLabel("Live preview panel is always shown.")
        self.preview_status_label.setObjectName("helpLabel")
        settings_layout.addWidget(self.preview_status_label)

        self.save_btn = QPushButton()
        self.save_btn.setObjectName("primaryButton")
        self.save_btn.clicked.connect(self.save_current_settings)
        settings_layout.addWidget(self.save_btn)

        self.reset_btn = QPushButton()
        self.reset_btn.setObjectName("dangerButton")
        self.reset_btn.clicked.connect(self.reset_settings)
        settings_layout.addWidget(self.reset_btn)

        layout.addWidget(settings_group)
        info_text = QLabel(
            "All settings are saved in setting_wa.ini beside this application. "
            "This includes theme, language, link format, window size and position, "
            "active tab, preview panel layout, last inputs, options, and generated results."
        )
        info_text.setObjectName("helpLabel")
        info_text.setWordWrap(True)
        layout.addWidget(info_text)
        layout.addStretch()

        self.tabs.addTab(settings_tab, "Settings")
        self.save_btn.setText(self.languages[self.current_language]["save_settings"])
        self.reset_btn.setText(self.languages[self.current_language]["reset_settings"])

    def create_about_tab(self):
        about_tab = QWidget()
        layout = QVBoxLayout(about_tab)
        layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        layout.setContentsMargins(30, 24, 30, 24)
        layout.setSpacing(10)

        self.about_title_label = QLabel("WhatsApp Link Generator")
        self.about_title_label.setObjectName("aboutTitle")
        self.about_title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.about_title_label)

        about_body = QLabel(
            "Created by:<br>"
            "<b>rahfie27</b><br>"
            "<b>E-COMPUTER</b><br>"
            "<b>SERVICE KOMPUTER PANGGILAN BOGOR</b><br><br>"
            "Copyright © ECOMTECH 2026 - All Right Reserved"
        )
        about_body.setTextFormat(Qt.RichText)
        about_body.setAlignment(Qt.AlignCenter)
        about_body.setWordWrap(True)
        layout.addWidget(about_body)

        contact_label = QLabel(
            'Contact:<br><a href="mailto:e-com-tech@mail.com">e-com-tech@mail.com</a> / '
            '<a href="mailto:rahfie27@gmail.com">rahfie27@gmail.com</a>'
        )
        contact_label.setTextFormat(Qt.RichText)
        contact_label.setOpenExternalLinks(True)
        contact_label.setAlignment(Qt.AlignCenter)
        contact_label.setWordWrap(True)
        layout.addWidget(contact_label)

        copy_contact_btn = QPushButton("Copy Contact")
        copy_contact_btn.setObjectName("secondaryButton")
        copy_contact_btn.clicked.connect(self.copy_contact)
        layout.addWidget(copy_contact_btn, alignment=Qt.AlignHCenter)

        donation_label = QLabel('Donation:<br><a href="https://paypal.me/rahfie">paypal.me/rahfie</a>')
        donation_label.setTextFormat(Qt.RichText)
        donation_label.setOpenExternalLinks(True)
        donation_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(donation_label)

        copy_donation_btn = QPushButton("Copy Donation")
        copy_donation_btn.setObjectName("secondaryButton")
        copy_donation_btn.clicked.connect(self.copy_donation)
        layout.addWidget(copy_donation_btn, alignment=Qt.AlignHCenter)

        warning = QLabel("WARNING!<br>This software is provided as-is without warranty.")
        warning.setObjectName("warningLabel")
        warning.setTextFormat(Qt.RichText)
        warning.setAlignment(Qt.AlignCenter)
        warning.setWordWrap(True)
        layout.addWidget(warning)
        layout.addStretch()

        self.tabs.addTab(about_tab, self.languages[self.current_language]["about_tab"])

    def create_preview_dock(self):
        self.preview_dock = QDockWidget("Live Preview", self)
        self.preview_dock.setObjectName("LivePreviewDock")
        self.preview_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.preview_dock.setFeatures(
            QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable
        )

        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        self.preview_heading = QLabel("WhatsApp Preview")
        self.preview_heading.setObjectName("previewHeading")
        self.preview_heading.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.preview_heading)

        phone_card = QFrame()
        phone_card.setObjectName("phoneCard")
        phone_layout = QVBoxLayout(phone_card)
        self.preview_number_label = QLabel("No phone number")
        self.preview_number_label.setObjectName("previewNumber")
        self.preview_number_label.setAlignment(Qt.AlignCenter)
        phone_layout.addWidget(self.preview_number_label)

        self.preview_message_label = QLabel("Your message preview will appear here.")
        self.preview_message_label.setObjectName("previewBubble")
        self.preview_message_label.setWordWrap(True)
        self.preview_message_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        phone_layout.addWidget(self.preview_message_label)
        phone_layout.addStretch()
        layout.addWidget(phone_card, 1)

        self.preview_link_output = QLineEdit()
        self.preview_link_output.setReadOnly(True)
        self.preview_link_output.setPlaceholderText("Generated URL preview")
        layout.addWidget(self.preview_link_output)

        self.open_preview_btn = QPushButton("Open Preview Link")
        self.open_preview_btn.setObjectName("primaryButton")
        self.open_preview_btn.clicked.connect(self.open_preview_link)
        self.open_preview_btn.setEnabled(False)
        layout.addWidget(self.open_preview_btn)

        self.preview_dock.setWidget(panel)
        self.addDockWidget(Qt.RightDockWidgetArea, self.preview_dock)
        self.preview_dock.setVisible(True)

    def restore_window_layout(self):
        geometry = self.settings.get("geometry")
        if geometry:
            try:
                self._restored_geometry = self.restoreGeometry(QByteArray(geometry))
            except (TypeError, ValueError):
                self._restored_geometry = False

        if not self._restored_geometry:
            self.resize(*self.DEFAULT_SIZE)
            self.center_window()

        state = self.settings.get("window_state")
        if state:
            try:
                self.restoreState(QByteArray(state), self.APP_STATE_VERSION)
            except (TypeError, ValueError):
                pass

        tab_index = int(self.settings.get("tab_index", 0))
        self.tabs.setCurrentIndex(max(0, min(tab_index, self.tabs.count() - 1)))
        # Saved layouts from older versions may have hidden the dock.
        # Always show it after restoring geometry and dock state.
        self.preview_dock.setVisible(True)

        # Guard against a saved position that is no longer visible after monitor changes.
        if not self.is_window_on_screen():
            self.center_window()

    def restore_last_session(self):
        """Restore all editable fields, options, and generated results."""
        self.phone_input.setText(self.settings.get("phone_input", ""))
        self.message_input.setPlainText(self.settings.get("message_input", ""))
        self.result_output.setPlainText(self.settings.get("simple_result", ""))
        self.multiple_numbers_input.setPlainText(
            self.settings.get("multiple_numbers_input", "")
        )
        self.advanced_message_input.setPlainText(
            self.settings.get("advanced_message_input", "")
        )
        self.advanced_result_output.setPlainText(
            self.settings.get("advanced_result", "")
        )
        self.use_web.setChecked(bool(self.settings.get("use_web", False)))

    def center_window(self):
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        available = screen.availableGeometry()
        frame = self.frameGeometry()
        frame.moveCenter(available.center())
        self.move(frame.topLeft())

    def is_window_on_screen(self):
        frame = self.frameGeometry()
        for screen in QApplication.screens():
            if screen.availableGeometry().intersects(frame):
                return True
        return False

    def apply_theme(self, theme_name):
        if theme_name not in self.THEMES:
            theme_name = "dark"
        self.current_theme = theme_name
        theme = self.THEMES[theme_name]

        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(theme["window"]))
        palette.setColor(QPalette.WindowText, QColor(theme["text"]))
        palette.setColor(QPalette.Base, QColor(theme["field"]))
        palette.setColor(QPalette.AlternateBase, QColor(theme["panel"]))
        palette.setColor(QPalette.Text, QColor(theme["text"]))
        palette.setColor(QPalette.Button, QColor(theme["panel"]))
        palette.setColor(QPalette.ButtonText, QColor(theme["text"]))
        palette.setColor(QPalette.Highlight, QColor(theme["accent"]))
        palette.setColor(QPalette.HighlightedText, QColor(theme["selection_text"]))
        palette.setColor(QPalette.Link, QColor(theme["accent"]))
        QApplication.setPalette(palette)

        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background-color: {theme['window']};
                color: {theme['text']};
            }}
            QMenuBar, QMenu, QStatusBar {{
                background-color: {theme['panel']};
                color: {theme['text']};
            }}
            QMenuBar::item:selected, QMenu::item:selected {{
                background-color: {theme['accent']};
                color: white;
            }}
            QGroupBox {{
                background-color: {theme['panel']};
                border: 1px solid {theme['border']};
                border-radius: 7px;
                margin-top: 12px;
                padding: 10px;
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: {theme['accent']};
            }}
            QLineEdit, QTextEdit, QComboBox {{
                background-color: {theme['field']};
                color: {theme['text']};
                border: 1px solid {theme['border']};
                border-radius: 5px;
                padding: 6px;
                selection-background-color: {theme['accent']};
                selection-color: {theme['selection_text']};
            }}
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
                border: 1px solid {theme['accent']};
            }}
            QTabWidget::pane {{
                background-color: {theme['panel']};
                border: 1px solid {theme['border']};
                border-radius: 6px;
            }}
            QTabBar::tab {{
                background-color: {theme['window']};
                color: {theme['text']};
                border: 1px solid {theme['border']};
                padding: 8px 14px;
                min-width: 105px;
            }}
            QTabBar::tab:selected {{
                background-color: {theme['accent']};
                color: white;
            }}
            QCheckBox {{ spacing: 7px; }}
            QPushButton {{
                background-color: {theme['panel']};
                color: {theme['text']};
                border: 1px solid {theme['border']};
                border-radius: 5px;
                padding: 8px 12px;
                min-height: 18px;
            }}
            QPushButton:hover {{ border-color: {theme['accent']}; }}
            QPushButton#primaryButton {{
                background-color: {theme['accent']};
                color: white;
                border: none;
                font-weight: bold;
            }}
            QPushButton#primaryButton:hover {{ background-color: {theme['accent_hover']}; }}
            QPushButton#secondaryButton {{
                background-color: {theme['panel']};
                color: {theme['accent']};
                border: 1px solid {theme['accent']};
                font-weight: bold;
            }}
            QPushButton#smallButton {{ padding: 5px 8px; min-height: 14px; }}
            QPushButton#dangerButton {{
                background-color: #c62828;
                color: white;
                border: none;
                font-weight: bold;
            }}
            QLabel#helpLabel {{ color: {theme['muted']}; font-size: 10pt; }}
            QLabel#aboutTitle {{ color: {theme['accent']}; font-size: 20pt; font-weight: bold; }}
            QLabel#warningLabel {{ color: #d32f2f; font-weight: bold; }}
            QDockWidget {{ color: {theme['text']}; font-weight: bold; }}
            QDockWidget::title {{
                background-color: {theme['panel']};
                border: 1px solid {theme['border']};
                padding: 7px;
                text-align: center;
            }}
            QFrame#phoneCard {{
                background-color: {theme['field']};
                border: 1px solid {theme['border']};
                border-radius: 14px;
            }}
            QLabel#previewHeading {{ color: {theme['accent']}; font-size: 14pt; font-weight: bold; }}
            QLabel#previewNumber {{ color: {theme['muted']}; font-weight: bold; padding: 6px; }}
            QLabel#previewBubble {{
                background-color: {theme['accent']};
                color: white;
                border-radius: 10px;
                padding: 12px;
                margin: 8px;
            }}
        """)
        self.update_theme_combos()

    def change_theme_from_combo(self, index):
        theme = self.theme_combo.itemData(index)
        if theme:
            self.apply_theme(theme)

    def change_theme_from_settings(self, index):
        theme = self.settings_theme_combo.itemData(index)
        if theme:
            self.apply_theme(theme)

    def update_theme_combos(self):
        for combo in (getattr(self, "theme_combo", None), getattr(self, "settings_theme_combo", None)):
            if combo is None:
                continue
            index = combo.findData(self.current_theme)
            if index >= 0 and combo.currentIndex() != index:
                combo.blockSignals(True)
                combo.setCurrentIndex(index)
                combo.blockSignals(False)

    def change_language(self, language):
        if language not in self.languages:
            return
        self.current_language = language
        self.setWindowTitle(self.languages[language]["window_title"])

        for combo in (self.lang_combo, self.settings_language_combo):
            if combo.currentText() != language:
                combo.blockSignals(True)
                combo.setCurrentText(language)
                combo.blockSignals(False)

        self.retranslate_simple_tab()
        self.retranslate_advanced_tab()
        self.tabs.setTabText(2, "Settings")
        self.tabs.setTabText(3, self.languages[language]["about_tab"])
        self.save_btn.setText(self.languages[language]["save_settings"])
        self.reset_btn.setText(self.languages[language]["reset_settings"])
        self.update_preview()

    def retranslate_simple_tab(self):
        lang = self.languages[self.current_language]
        self.tabs.setTabText(0, lang["simple_tab"])
        self.phone_group.setTitle(lang["phone_number"])
        self.phone_help_label.setText(lang["phone_help"])
        self.phone_input.setPlaceholderText(lang["phone_placeholder"])
        self.message_group.setTitle(lang["message"])
        self.message_input.setPlaceholderText(lang["message_placeholder"])
        self.include_country_code.setText(lang["wa_format"])
        self.generate_btn.setText(lang["generate_btn"])
        self.result_group.setTitle(lang["generated_link"])
        self.copy_btn.setText(lang["copy_btn"])

    def retranslate_advanced_tab(self):
        lang = self.languages[self.current_language]
        self.tabs.setTabText(1, lang["advanced_tab"])
        self.numbers_group.setTitle(lang["multiple_numbers"])
        self.numbers_help_label.setText(lang["multiple_numbers_help"])
        self.multiple_numbers_input.setPlaceholderText(lang["multiple_numbers_placeholder"])
        self.advanced_message_group.setTitle(lang["message_options"])
        self.advanced_message_input.setPlaceholderText(lang["message_placeholder"])
        self.quick_insert_label.setText(lang["quick_insert"])
        self.name_btn.setText(lang["name_btn"])
        self.date_btn.setText(lang["date_btn"])
        self.company_btn.setText(lang["company_btn"])
        self.advanced_options_group.setTitle(lang["advanced_options"])
        self.use_web.setText(lang["use_web"])
        self.generate_advanced_btn.setText(lang["generate_multiple"])
        self.advanced_result_group.setTitle(lang["generated_links"])
        self.advanced_result_output.setPlaceholderText(lang["links_placeholder"])
        self.copy_all_btn.setText(lang["copy_all"])

    def sync_format_controls(self, checked):
        self.wa_format = bool(checked)
        target = 0 if checked else 1
        if self.format_combo.currentIndex() != target:
            self.format_combo.blockSignals(True)
            self.format_combo.setCurrentIndex(target)
            self.format_combo.blockSignals(False)

    def sync_format_checkbox(self, index):
        checked = bool(self.format_combo.itemData(index))
        self.wa_format = checked
        if self.include_country_code.isChecked() != checked:
            self.include_country_code.setChecked(checked)
        self.update_preview()

    @staticmethod
    def normalize_phone(raw_phone):
        digits = "".join(character for character in raw_phone if character.isdigit())
        return digits if 6 <= len(digits) <= 15 else ""

    def build_link(self, phone, message="", use_web=False):
        if not phone:
            return ""
        encoded_message = urllib.parse.quote(message) if message else ""
        if use_web:
            link = f"https://web.whatsapp.com/send?phone={phone}"
            if encoded_message:
                link += f"&text={encoded_message}"
            return link
        if self.wa_format:
            link = f"https://wa.me/{phone}"
            if encoded_message:
                link += f"?text={encoded_message}"
            return link
        link = f"https://api.whatsapp.com/send?phone={phone}"
        if encoded_message:
            link += f"&text={encoded_message}"
        return link

    def update_preview(self, *_):
        if not hasattr(self, "preview_message_label"):
            return

        if self.tabs.currentIndex() == 1:
            raw_numbers = [line.strip() for line in self.multiple_numbers_input.toPlainText().splitlines() if line.strip()]
            valid_numbers = [self.normalize_phone(number) for number in raw_numbers]
            valid_numbers = [number for number in valid_numbers if number]
            phone = valid_numbers[0] if valid_numbers else ""
            count_text = f"{len(valid_numbers)} valid recipient(s)" if valid_numbers else "No valid recipients"
            message = self.advanced_message_input.toPlainText().strip()
            self.preview_number_label.setText(count_text)
            link = self.build_link(phone, message, self.use_web.isChecked())
        else:
            phone = self.normalize_phone(self.phone_input.text())
            message = self.message_input.toPlainText().strip()
            self.preview_number_label.setText(phone or "No valid phone number")
            link = self.build_link(phone, message)

        self.preview_message_label.setText(message or "Your message preview will appear here.")
        self.preview_link = link
        self.preview_link_output.setText(link)
        self.open_preview_btn.setEnabled(bool(link))

    def open_preview_link(self):
        if self.preview_link:
            QDesktopServices.openUrl(QUrl(self.preview_link))

    def show_about_tab(self):
        self.tabs.setCurrentIndex(3)
        self.raise_()
        self.activateWindow()

    def insert_variable(self, variable):
        cursor = self.advanced_message_input.textCursor()
        cursor.insertText(variable)
        self.advanced_message_input.setTextCursor(cursor)
        self.advanced_message_input.setFocus()

    def generate_simple_link(self):
        raw_phone = self.phone_input.text().strip()
        if not raw_phone:
            self.show_warning("input_error", "enter_phone")
            return
        phone = self.normalize_phone(raw_phone)
        if not phone:
            self.show_warning("input_error", "valid_phone")
            return

        message = self.message_input.toPlainText().strip()
        link = self.build_link(phone, message)
        self.result_output.setPlainText(link)
        self.result_output.selectAll()
        self.preview_link = link
        self.preview_link_output.setText(link)

    def generate_advanced_links(self):
        numbers_text = self.multiple_numbers_input.toPlainText().strip()
        if not numbers_text:
            self.show_warning("input_error", "enter_numbers")
            return

        raw_numbers = [line.strip() for line in numbers_text.splitlines() if line.strip()]
        valid_numbers = []
        invalid_numbers = []
        for raw_number in raw_numbers:
            phone = self.normalize_phone(raw_number)
            if phone:
                valid_numbers.append(phone)
            else:
                invalid_numbers.append(raw_number)

        if not valid_numbers:
            self.show_warning("input_error", "no_valid_numbers")
            return
        if invalid_numbers:
            lang = self.languages[self.current_language]
            QMessageBox.warning(
                self,
                lang["invalid_numbers"],
                lang["numbers_skipped"] + "\n".join(invalid_numbers),
            )

        message = self.advanced_message_input.toPlainText().strip()
        links = [self.build_link(number, message, self.use_web.isChecked()) for number in valid_numbers]
        result_text = f"Generated {len(links)} links:\n\n" + "\n".join(
            f"{index}. {link}" for index, link in enumerate(links, 1)
        )
        self.advanced_result_output.setPlainText(result_text)
        self.advanced_result_output.selectAll()
        self.update_preview()

    def show_warning(self, title_key, message_key):
        lang = self.languages[self.current_language]
        QMessageBox.warning(self, lang[title_key], lang[message_key])

    def copy_to_clipboard(self):
        link = self.result_output.toPlainText().strip()
        if not link:
            self.show_warning("error", "no_link_copy")
            return
        QApplication.clipboard().setText(link)
        self.statusBar().showMessage(self.languages[self.current_language]["copied_clipboard"], 3000)

    def copy_all_links(self):
        links = self.advanced_result_output.toPlainText().strip()
        if not links:
            self.show_warning("error", "no_links_copy")
            return
        QApplication.clipboard().setText(links)
        self.statusBar().showMessage(self.languages[self.current_language]["all_copied"], 3000)

    def copy_contact(self):
        QApplication.clipboard().setText("e-com-tech@mail.com / rahfie27@gmail.com")
        self.statusBar().showMessage("Contact copied to clipboard.", 3000)

    def copy_donation(self):
        QApplication.clipboard().setText("paypal.me/rahfie")
        self.statusBar().showMessage("Donation link copied to clipboard.", 3000)

    def save_current_settings(self):
        if self.save_settings(show_error=True):
            QMessageBox.information(
                self,
                self.languages[self.current_language]["success"],
                self.languages[self.current_language]["settings_saved"],
            )

    def reset_settings(self):
        reply = QMessageBox.question(
            self,
            "Confirm Reset",
            "Reset settings, layout, position, size, and all saved last inputs?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        store = self.create_settings_store()
        store.clear()
        store.sync()

        self.current_theme = "dark"
        self.current_language = "English"
        self.wa_format = True
        self.lang_combo.setCurrentText("English")
        self.include_country_code.setChecked(True)
        self.use_web.setChecked(False)
        self.phone_input.clear()
        self.message_input.clear()
        self.result_output.clear()
        self.multiple_numbers_input.clear()
        self.advanced_message_input.clear()
        self.advanced_result_output.clear()
        self.tabs.setCurrentIndex(0)
        self.preview_dock.setFloating(False)
        self.addDockWidget(Qt.RightDockWidgetArea, self.preview_dock)
        self.preview_dock.setVisible(True)
        self.resize(*self.DEFAULT_SIZE)
        self.center_window()
        self.apply_theme("dark")
        self.update_preview()
        self.save_settings(show_error=False)

        QMessageBox.information(
            self,
            self.languages[self.current_language]["success"],
            self.languages[self.current_language]["settings_reset"],
        )

    def closeEvent(self, event):
        self.save_settings(show_error=False)
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    app.setOrganizationName("ECOMTECH")
    app.setApplicationName("WhatsApp Link Generator")
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))

    window = WhatsAppLinkGenerator()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
