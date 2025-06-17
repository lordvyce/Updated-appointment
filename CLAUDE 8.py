import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import DateEntry
import re
import json
from datetime import datetime, date, timedelta
import os
import csv
import threading
from tkinter import font
import webbrowser
import urllib.parse
import time
import schedule
from threading import Timer
import subprocess
import platform
try:
    import yagmail
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False
    
# Try to import pandas for Excel export
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

class ModernCompactClinicSystem:
    def __init__(self):
        self.load_email_settings()
        self.appointments = []
        self.current_theme = "light"
        self.reminder_settings = {
            "enabled": True,
            "remind_3_days": True,
            "remind_1_day": True,
            "remind_morning": True,
            "remind_1_hour": True,
            "business_hours_start": "09:00",
            "business_hours_end": "18:00",
            "check_interval": 300,  # Check every 5 minutes for testing
            "auto_send_whatsapp": True,
            "whatsapp_delay": 3
        }
        self.email_settings = {  # <--- MOVE THIS UP HERE!
            "enabled": True,
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "email_address": "",
            "app_password": "",
            "clinic_name": "Modern Clinic System",
            "clinic_address": "123 Medical Center Dr, Health City, HC 12345",
            "clinic_phone": "(555) 123-4567",
            "auto_send_email": True,
            "email_delay": 2
        }
        self.sent_reminders = {}
        self.reminder_thread = None
        self.reminder_running = False
        self.setup_themes()
        self.setup_gui()
        self.load_data()
        self.load_reminder_data()
        self.setup_keyboard_shortcuts()
        self.auto_save_active = True
        self.start_auto_save()
        self.start_reminder_system()
        
    def create_email_settings_dialog(self):
        """Create email configuration dialog"""
        theme = self.get_theme()
        
        dialog = tk.Toplevel(self.root)
        dialog.title("📧 Email Settings")
        dialog.geometry("500x600")
        dialog.configure(bg=theme["bg_primary"])
        dialog.grab_set()
        
        # Header
        header = tk.Frame(dialog, bg=theme["accent"], height=60)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text="📧 Email Configuration",
            font=self.fonts["heading"],
            bg=theme["accent"],
            fg="white"
        ).pack(expand=True)
        
        # Settings form
        form_frame = tk.Frame(dialog, bg=theme["bg_primary"])
        form_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Email settings fields
        settings_vars = {}
        
        fields = [
            ("📧 Your Email:", "email_address", self.email_settings.get("email_address", "")),
            ("🔑 App Password:", "app_password", self.email_settings.get("app_password", "")),
            ("🏥 Clinic Name:", "clinic_name", self.email_settings.get("clinic_name", "")),
            ("📍 Clinic Address:", "clinic_address", self.email_settings.get("clinic_address", "")),
            ("📞 Clinic Phone:", "clinic_phone", self.email_settings.get("clinic_phone", ""))
        ]
        
        for i, (label, key, value) in enumerate(fields):
            tk.Label(
                form_frame,
                text=label,
                font=self.fonts["body"],
                bg=theme["bg_primary"],
                fg=theme["text_primary"]
            ).grid(row=i, column=0, sticky='w', pady=5)
            
            var = tk.StringVar(value=value)
            settings_vars[key] = var
            
            # Show password field for app password
            show_char = "*" if "password" in key.lower() else None
            entry = tk.Entry(
                form_frame,
                textvariable=var,
                font=self.fonts["body"],
                bg=theme["bg_secondary"],
                fg=theme["text_primary"],
                show=show_char,
                width=40
            )
            entry.grid(row=i, column=1, sticky='ew', pady=5, padx=(10, 0))
        
        # Auto-send checkbox
        auto_send_var = tk.BooleanVar(value=self.email_settings.get("auto_send_email", True))
        tk.Checkbutton(
            form_frame,
            text="📤 Automatically send email reminders",
            variable=auto_send_var,
            bg=theme["bg_primary"],
            fg=theme["text_primary"],
            font=self.fonts["body"]
        ).grid(row=len(fields), column=0, columnspan=2, sticky='w', pady=10)
        
        # Instructions
        instructions = tk.Text(
            form_frame,
            height=8,
            bg=theme["bg_secondary"],
            fg=theme["text_primary"],
            font=self.fonts["small"],
            wrap='word'
        )
        instructions.grid(row=len(fields)+1, column=0, columnspan=2, sticky='ew', pady=10)
        instructions.insert('1.0', """
    📧 EMAIL SETUP INSTRUCTIONS:

    1. Use Gmail for best results
    2. Enable 2-Factor Authentication on your Google account
    3. Generate an App Password:
       • Go to Google Account → Security → 2-Step Verification
       • Click "App passwords" 
       • Select "Mail" and your device
       • Copy the 16-character password (no spaces)
    4. Paste the App Password above (NOT your regular Gmail password)
    5. Test the connection using the Test button

    ⚠️ NEVER use your regular Gmail password!
    ✅ Only use the generated App Password for security.
        """)
        
        form_frame.grid_columnconfigure(1, weight=1)
        
        # Buttons
        btn_frame = tk.Frame(dialog, bg=theme["bg_primary"])
        btn_frame.pack(fill='x', padx=20, pady=(0, 20))
        
    def save_settings():
        for key, var in settings_vars.items():
            self.email_settings[key] = var.get()
        self.email_settings["auto_send_email"] = auto_send_var.get()
        self.save_email_settings()
        self.show_toast("Email settings saved!", "success")
        dialog.destroy()
    
    def test_email():
        try:
            if not EMAIL_AVAILABLE:
                self.show_toast("Please install yagmail: pip install yagmail", "error")
                return
                
            email_addr = settings_vars["email_address"].get()
            app_password = settings_vars["app_password"].get()
            
            if not email_addr or not app_password:
                self.show_toast("Please enter email and app password first", "warning")
                return
            
            yag = yagmail.SMTP(email_addr, app_password)
            yag.send(
                to=email_addr,
                subject="Test Email - Clinic System",
                contents="This is a test email from your clinic system. Email is working correctly!"
            )
            yag.close()
            self.show_toast("Test email sent successfully! Check your inbox.", "success")
        except Exception as e:
            self.show_toast(f"Email test failed: {str(e)}", "error")
        
        tk.Button(
            btn_frame,
            text="📧 Test Email",
            command=test_email,
            bg=theme["warning"],
            fg="white",
            font=self.fonts["body"],
            relief='flat',
            padx=15,
            cursor='hand2'
        ).pack(side='left', padx=(0, 10))
        
        tk.Button(
            btn_frame,
            text="💾 Save Settings",
            command=save_settings,
            bg=theme["success"],
            fg="white",
            font=self.fonts["body"],
            relief='flat',
            padx=15,
            cursor='hand2'
        ).pack(side='left', padx=10)
        
        tk.Button(
            btn_frame,
            text="❌ Cancel",
            command=dialog.destroy,
            bg=theme["danger"],
            fg="white",
            font=self.fonts["body"],
            relief='flat',
            padx=15,
            cursor='hand2'
        ).pack(side='left')

    def save_email_settings(self):
        """Save email settings to file"""
        try:
            with open('email_settings.json', 'w') as f:
                json.dump(self.email_settings, f, indent=2)
        except:
            pass

    def load_email_settings(self):
        """Load email settings from file"""
        try:
            if os.path.exists('email_settings.json'):
                with open('email_settings.json', 'r') as f:
                    saved_settings = json.load(f)
                    self.email_settings.update(saved_settings)
        except:
            pass
    
    def validate_email(self, email):
        """Validate email format"""
        import re
        if not email:
            return False
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def send_email_reminder(self, appointment, reminder_type):
        """Send email reminder to patient"""
        if not EMAIL_AVAILABLE:
            self.log_reminder_activity(
                appointment['patient_name'], 
                appointment.get('email', 'N/A'),
                f"Email library not available for {reminder_type} reminder", 
                "ERROR"
            )
            return False
    
        email = appointment.get('email', '').strip()
        if not email or not self.validate_email(email):
            return False
        
        try:
            # Create email content
            subject = self.get_email_subject(appointment, reminder_type)
            body = self.get_email_body(appointment, reminder_type)
            
            # Send email using yagmail
            if self.email_settings.get("auto_send_email", True):
                yag = yagmail.SMTP(
                    self.email_settings["email_address"], 
                    self.email_settings["app_password"]
                )
                yag.send(
                    to=email,
                    subject=subject,
                        contents=body
                )
                yag.close()
                
                self.log_reminder_activity(
                    appointment['patient_name'], 
                    email,
                    f"{reminder_type.replace('_', ' ').title()} email reminder sent", 
                    "SENT 📧"
                )
                return True
            else:
                self.log_reminder_activity(
                    appointment['patient_name'], 
                    email,
                    f"{reminder_type.replace('_', ' ').title()} email reminder (auto-send disabled)", 
                    "LOGGED 📧"
                )
                return True
                
        except Exception as e:
            self.log_reminder_activity(
                appointment['patient_name'], 
                email,
                f"Error sending {reminder_type} email: {str(e)}", 
                "ERROR ❌"
            )
            return False

    def get_email_subject(self, appointment, reminder_type):
        """Generate email subject based on reminder type"""
        clinic_name = self.email_settings.get("clinic_name", "Clinic")
        name = appointment['patient_name']
        
        subjects = {
            "3_days": f"Appointment Reminder - {name} | {clinic_name}",
            "1_day": f"Tomorrow's Appointment - {name} | {clinic_name}",
            "morning": f"Today's Appointment - {name} | {clinic_name}",
            "1_hour": f"Appointment in 1 Hour - {name} | {clinic_name}",
            "manual": f"Appointment Reminder - {name} | {clinic_name}"
        }
        
        return subjects.get(reminder_type, f"Appointment Reminder - {name} | {clinic_name}")

    def get_email_body(self, appointment, reminder_type):
        """Generate email body based on reminder type"""
        name = appointment['patient_name']
        procedure = appointment['procedure']
        apt_date = appointment.get('appointment_date', 'N/A')
        apt_time = appointment.get('appointment_time', '09:00')
        clinic_name = self.email_settings.get("clinic_name", "Clinic")
        clinic_address = self.email_settings.get("clinic_address", "")
        clinic_phone = self.email_settings.get("clinic_phone", "")
        
        bodies = {
                "3_days": f"""
    Dear {name},

    This is a friendly reminder about your upcoming appointment:

    🔬 Procedure: {procedure}
    📅 Date: {apt_date}
    ⏰ Time: {apt_time}
    📍 Location: {clinic_address}

    Your appointment is in 3 days. Please mark your calendar and prepare any necessary documents.

    If you need to reschedule or have any questions, please contact us at {clinic_phone}.

    Best regards,
    {clinic_name} Team
            """,
            
            "1_day": f"""
    Dear {name},

    Your appointment is tomorrow! Here are the details:

    🔬 Procedure: {procedure}
    📅 Date: {apt_date} (TOMORROW)
    ⏰ Time: {apt_time}
    📍 Location: {clinic_address}

    Please arrive 15 minutes early for check-in. Don't forget to bring:
    • Photo ID
    • Insurance card
    • Any relevant medical records

    Contact us at {clinic_phone} if you have any questions.

    Best regards,
    {clinic_name} Team
            """,
            
            "morning": f"""
    Dear {name},

    Good morning! You have an appointment TODAY:

    🔬 Procedure: {procedure}
    📅 Date: TODAY ({apt_date})
    ⏰ Time: {apt_time}
    📍 Location: {clinic_address}

    Please arrive 15 minutes early. Our team is ready to assist you.

    If you're running late or have any issues, please call us immediately at {clinic_phone}.

    Best regards,
    {clinic_name} Team
            """,
            
            "1_hour": f"""
    Dear {name},

    Your appointment is in 1 HOUR:

    🔬 Procedure: {procedure}
    ⏰ Time: {apt_time} (in 1 hour)
    📍 Location: {clinic_address}

    Please make your way to our clinic now. Parking is available on-site.

    If you're running late, please call us at {clinic_phone}.

    Best regards,
    {clinic_name} Team
            """
        }
            
        return bodies.get(reminder_type, f"""
    Dear {name},

    This is a reminder about your appointment:

    🔬 Procedure: {procedure}
    📅 Date: {apt_date}
    ⏰ Time: {apt_time}
    📍 Location: {clinic_address}

    Please contact us at {clinic_phone} if you have any questions.

    Best regards,
    {clinic_name} Team
        """)
        
    def setup_themes(self):
        """Setup light and dark theme configurations"""
        self.themes = {
            "light": {
                "bg_primary": "#ffffff",
                "bg_secondary": "#f8fafc",
                "bg_accent": "#e2e8f0",
                "text_primary": "#1e293b",
                "text_secondary": "#64748b",
                "accent": "#3b82f6",
                "success": "#10b981",
                "warning": "#f59e0b",
                "danger": "#ef4444",
                "sidebar": "#f1f5f9",
                "gradient_start": "#3b82f6",
                "gradient_end": "#8b5cf6"
            },
            "dark": {
                "bg_primary": "#0f172a",
                "bg_secondary": "#1e293b",
                "bg_accent": "#334155",
                "text_primary": "#f1f5f9",
                "text_secondary": "#cbd5e1",
                "accent": "#60a5fa",
                "success": "#34d399",
                "warning": "#fbbf24",
                "danger": "#f87171",
                "sidebar": "#1e293b",
                "gradient_start": "#60a5fa",
                "gradient_end": "#a78bfa"
            }
        }

    def get_theme(self):
        """Get current theme colors"""
        return self.themes[self.current_theme]

    def setup_gui(self):
        """Setup the main GUI with ultra-compact design"""
        self.root = tk.Tk()
        self.root.title("🏥 Modern Clinic System - Auto WhatsApp Reminders")
        self.root.geometry("800x600")
        self.root.minsize(750, 550)
        
        theme = self.get_theme()
        self.root.configure(bg=theme["bg_primary"])
        
        # Custom fonts
        self.fonts = {
            "title": ("Segoe UI", 16, "bold"),
            "heading": ("Segoe UI", 12, "bold"),
            "body": ("Segoe UI", 10),
            "small": ("Segoe UI", 8)
        }
        
        self.setup_main_layout()
        self.create_sidebar()
        self.create_main_content()
        self.create_floating_actions()
        self.create_notification_system()
        self.apply_theme()

    def setup_main_layout(self):
        """Create the main layout structure"""
        self.main_container = tk.Frame(self.root)
        self.main_container.pack(fill='both', expand=True)
        
        self.main_container.grid_columnconfigure(1, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)

    def create_sidebar(self):
        """Create compact sidebar navigation"""
        theme = self.get_theme()
        
        self.sidebar = tk.Frame(
            self.main_container, 
            width=200, 
            bg=theme["sidebar"],
            relief='flat',
            bd=1
        )
        self.sidebar.grid(row=0, column=0, sticky='ns', padx=(0, 1))
        self.sidebar.grid_propagate(False)
        
        # Header with theme toggle
        header_frame = tk.Frame(self.sidebar, bg=theme["sidebar"])
        header_frame.pack(fill='x', pady=10)
        
        # App title
        title_label = tk.Label(
            header_frame,
            text="🏥 Clinic Pro",
            font=self.fonts["title"],
            bg=theme["sidebar"],
            fg=theme["text_primary"]
        )
        title_label.pack()
        
        # Auto-reminder status indicator
        whatsapp_status = "📱 WhatsApp AUTO" if self.reminder_settings.get("auto_send_whatsapp", True) else "📱 Manual Only"
        self.reminder_status = tk.Label(
            header_frame,
            text=f"🔔 Reminders: {'ON' if self.reminder_settings['enabled'] else 'OFF'}",
            font=self.fonts["small"],
            bg=theme["success"] if self.reminder_settings["enabled"] else theme["danger"],
            fg="white",
            padx=5,
            pady=2
        )
        self.reminder_status.pack(pady=(5, 2))
        
        self.whatsapp_status = tk.Label(
            header_frame,
            text=whatsapp_status,
            font=self.fonts["small"],
            bg=theme["accent"],
            fg="white",
            padx=5,
            pady=2
        )
        self.whatsapp_status.pack(pady=(2, 0))
        
        # Theme toggle button
        self.theme_btn = tk.Button(
            header_frame,
            text="🌙" if self.current_theme == "light" else "☀️",
            command=self.toggle_theme,
            bg=theme["accent"],
            fg="white",
            font=self.fonts["body"],
            relief='flat',
            padx=10,
            pady=2,
            cursor='hand2'
        )
        self.theme_btn.pack(pady=(10, 0))
        
        # Navigation buttons
        self.nav_buttons = []
        nav_items = [
            ("➕ Add Patient", self.show_add_page, "add"),
            ("📋 View All", self.show_view_page, "view"),
            ("📊 Reports", self.show_reports_page, "reports"),  # ← CHANGED
            ("📊 Dashboard", self.show_dashboard_page, "dashboard"),
            ("📱 Auto WhatsApp", self.show_reminders_page, "reminders"),
            ("⚙️ Settings", self.show_settings_page, "settings")
        ]
        
        nav_frame = tk.Frame(self.sidebar, bg=theme["sidebar"])
        nav_frame.pack(fill='x', pady=20, padx=10)
        
        self.current_page = "add"
        
        for text, command, page_id in nav_items:
            btn = tk.Button(
                nav_frame,
                text=text,
                command=lambda cmd=command, pid=page_id: self.navigate_to(cmd, pid),
                bg=theme["accent"] if page_id == self.current_page else theme["bg_accent"],
                fg="white" if page_id == self.current_page else theme["text_primary"],
                font=self.fonts["body"],
                relief='flat',
                anchor='w',
                padx=15,
                pady=8,
                cursor='hand2'
            )
            btn.pack(fill='x', pady=2)
            self.nav_buttons.append((btn, page_id))
        
        # Quick stats
        self.create_quick_stats()

    def create_quick_stats(self):
        """Create quick statistics panel in sidebar"""
        theme = self.get_theme()
        
        stats_frame = tk.LabelFrame(
            self.sidebar,
            text="📈 Live Stats",
            bg=theme["sidebar"],
            fg=theme["text_primary"],
            font=self.fonts["small"],
            relief='flat'
        )
        stats_frame.pack(fill='x', pady=20, padx=10)
        
        self.stats_labels = {}
        stats_items = [
            ("Total Patients:", "total"),
            ("Today's Appointments:", "today"),
            ("WhatsApp Sent:", "whatsapp_sent")
        ]
        
        for text, key in stats_items:
            frame = tk.Frame(stats_frame, bg=theme["sidebar"])
            frame.pack(fill='x', pady=2)
            
            tk.Label(
                frame,
                text=text,
                bg=theme["sidebar"],
                fg=theme["text_secondary"],
                font=self.fonts["small"]
            ).pack(side='left')
            
            value_label = tk.Label(
                frame,
                text="0",
                bg=theme["sidebar"],
                fg=theme["accent"],
                font=("Segoe UI", 8, "bold")
            )
            value_label.pack(side='right')
            self.stats_labels[key] = value_label

    def create_main_content(self):
        """Create main content area"""
        theme = self.get_theme()
        
        self.content_area = tk.Frame(
            self.main_container,
            bg=theme["bg_primary"]
        )
        self.content_area.grid(row=0, column=1, sticky='nsew', padx=10, pady=10)
        
        # Create all pages
        self.pages = {}
        self.create_add_page()
        self.create_view_page()
        self.create_reports_page()  # ← CHANGED
        self.create_dashboard_page()
        self.create_reminders_page()
        self.create_settings_page()
        
        # Show default page
        self.show_add_page()

    def create_reminders_page(self):
        """Create auto-WhatsApp reminders management page"""
        theme = self.get_theme()
        
        page = tk.Frame(self.content_area, bg=theme["bg_primary"])
        self.pages["reminders"] = page
        
        # Header
        header = tk.Frame(page, bg=theme["bg_primary"])
        header.pack(fill='x', pady=(0, 20))
        
        tk.Label(
            header,
            text="📱 Auto WhatsApp Reminder System",
            font=self.fonts["title"],
            bg=theme["bg_primary"],
            fg=theme["text_primary"]
        ).pack(side='left')
        
        # Control buttons
        controls_frame = tk.Frame(header, bg=theme["bg_primary"])
        controls_frame.pack(side='right')
        
        # Toggle reminder system
        toggle_btn = tk.Button(
            controls_frame,
            text="🔔 ON" if self.reminder_settings["enabled"] else "🔕 OFF",
            command=self.toggle_reminder_system,
            bg=theme["success"] if self.reminder_settings["enabled"] else theme["danger"],
            fg="white",
            font=self.fonts["body"],
            relief='flat',
            padx=15,
            pady=5,
            cursor='hand2'
        )
        toggle_btn.pack(side='left', padx=(0, 5))
        
        # Toggle WhatsApp auto-send
        whatsapp_toggle_btn = tk.Button(
            controls_frame,
            text="📱 AUTO" if self.reminder_settings.get("auto_send_whatsapp", True) else "📱 MANUAL",
            command=self.toggle_whatsapp_auto_send,
            bg=theme["accent"] if self.reminder_settings.get("auto_send_whatsapp", True) else theme["warning"],
            fg="white",
            font=self.fonts["body"],
            relief='flat',
            padx=15,
            pady=5,
            cursor='hand2'
        )
        whatsapp_toggle_btn.pack(side='left')
        
        # Settings panel
        settings_frame = tk.LabelFrame(
            page,
            text="⚙️ WhatsApp Reminder Settings",
            bg=theme["bg_secondary"],
            fg=theme["text_primary"],
            font=self.fonts["body"]
        )
        settings_frame.pack(fill='x', padx=5, pady=5)
        
        settings_inner = tk.Frame(settings_frame, bg=theme["bg_secondary"])
        settings_inner.pack(fill='x', padx=15, pady=15)
        
        # Reminder options
        self.reminder_vars = {}
        options = [
            ("remind_3_days", "📅 3 Days Before"),
            ("remind_1_day", "📅 1 Day Before"),
            ("remind_morning", "🌅 Morning Of"),
            ("remind_1_hour", "⏰ 1 Hour Before")
        ]
        
        for i, (key, text) in enumerate(options):
            var = tk.BooleanVar(value=self.reminder_settings[key])
            self.reminder_vars[key] = var
            
            cb = tk.Checkbutton(
                settings_inner,
                text=text,
                variable=var,
                bg=theme["bg_secondary"],
                fg=theme["text_primary"],
                font=self.fonts["body"],
                anchor='w',
                command=self.save_reminder_settings
            )
            cb.grid(row=i//2, column=i%2, sticky='w', padx=10, pady=5)
        
        # WhatsApp settings
        whatsapp_frame = tk.Frame(settings_inner, bg=theme["bg_secondary"])
        whatsapp_frame.grid(row=2, column=0, columnspan=2, sticky='ew', pady=10)
        
        tk.Label(
            whatsapp_frame,
            text="📱 WhatsApp Settings:",
            bg=theme["bg_secondary"],
            fg=theme["text_primary"],
            font=self.fonts["heading"]
        ).pack(anchor='w')
        
        # Auto-send checkbox
        self.auto_whatsapp_var = tk.BooleanVar(value=self.reminder_settings.get("auto_send_whatsapp", True))
        auto_cb = tk.Checkbutton(
            whatsapp_frame,
            text="🚀 Automatically send WhatsApp messages",
            variable=self.auto_whatsapp_var,
            bg=theme["bg_secondary"],
            fg=theme["text_primary"],
            font=self.fonts["body"],
            command=self.save_reminder_settings
        )
        auto_cb.pack(anchor='w', pady=2)
        
        # Delay setting
        delay_frame = tk.Frame(whatsapp_frame, bg=theme["bg_secondary"])
        delay_frame.pack(anchor='w', pady=5)
        
        tk.Label(
            delay_frame,
            text="⏱️ Delay between messages:",
            bg=theme["bg_secondary"],
            fg=theme["text_primary"],
            font=self.fonts["body"]
        ).pack(side='left')
        
        self.delay_var = tk.StringVar(value=str(self.reminder_settings.get("whatsapp_delay", 3)))
        delay_entry = tk.Entry(
            delay_frame,
            textvariable=self.delay_var,
            width=5,
            font=self.fonts["body"],
            bg=theme["bg_primary"],
            fg=theme["text_primary"]
        )
        delay_entry.pack(side='left', padx=(10, 5))
        
        tk.Label(
            delay_frame,
            text="seconds",
            bg=theme["bg_secondary"],
            fg=theme["text_primary"],
            font=self.fonts["body"]
        ).pack(side='left')
        
        # Business hours
        hours_frame = tk.Frame(settings_inner, bg=theme["bg_secondary"])
        hours_frame.grid(row=3, column=0, columnspan=2, sticky='ew', pady=10)
        
        tk.Label(
            hours_frame,
            text="🕐 Business Hours:",
            bg=theme["bg_secondary"],
            fg=theme["text_primary"],
            font=self.fonts["body"]
        ).pack(side='left')
        
        self.start_time_var = tk.StringVar(value=self.reminder_settings["business_hours_start"])
        tk.Entry(
            hours_frame,
            textvariable=self.start_time_var,
            width=8,
            font=self.fonts["body"],
            bg=theme["bg_primary"],
            fg=theme["text_primary"]
        ).pack(side='left', padx=(10, 5))
        
        tk.Label(hours_frame, text="to", bg=theme["bg_secondary"], fg=theme["text_primary"]).pack(side='left')
        
        self.end_time_var = tk.StringVar(value=self.reminder_settings["business_hours_end"])
        tk.Entry(
            hours_frame,
            textvariable=self.end_time_var,
            width=8,
            font=self.fonts["body"],
            bg=theme["bg_primary"],
            fg=theme["text_primary"]
        ).pack(side='left', padx=(5, 10))
        
        tk.Button(
            hours_frame,
            text="💾 Save Settings",
            command=self.save_reminder_settings,
            bg=theme["accent"],
            fg="white",
            font=self.fonts["small"],
            relief='flat',
            padx=15,
            cursor='hand2'
        ).pack(side='left', padx=10)
        
        # WhatsApp Activity Log
        log_frame = tk.LabelFrame(
            page,
            text="📱 WhatsApp Activity Log",
            bg=theme["bg_secondary"],
            fg=theme["text_primary"],
            font=self.fonts["body"]
        )
        log_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Log treeview
        log_scroll = ttk.Scrollbar(log_frame)
        log_scroll.pack(side='right', fill='y')
        
        self.reminder_log_tree = ttk.Treeview(
            log_frame,
            columns=('Time', 'Patient', 'Phone', 'Type', 'Status'),
            show='headings',
            yscrollcommand=log_scroll.set,
            height=8
        )
        
        log_scroll.config(command=self.reminder_log_tree.yview)
        
        for col, width in [('Time', 100), ('Patient', 120), ('Phone', 100), ('Type', 100), ('Status', 80)]:
            self.reminder_log_tree.heading(col, text=col)
            self.reminder_log_tree.column(col, width=width, anchor='center')
        
        self.reminder_log_tree.pack(fill='both', expand=True)
        
        # Control buttons
        control_frame = tk.Frame(log_frame, bg=theme["bg_secondary"])
        control_frame.pack(fill='x', pady=5)
        
        tk.Button(
            control_frame,
            text="🔄 Refresh Log",
            command=self.refresh_reminder_log,
            bg=theme["accent"],
            fg="white",
            font=self.fonts["small"],
            relief='flat',
            padx=10,
            cursor='hand2'
        ).pack(side='left', padx=5)
        
        tk.Button(
            control_frame,
            text="🗑️ Clear Log",
            command=self.clear_reminder_log,
            bg=theme["warning"],
            fg="white",
            font=self.fonts["small"],
            relief='flat',
            padx=10,
            cursor='hand2'
        ).pack(side='left', padx=5)
        
        tk.Button(
            control_frame,
            text="📱 Test WhatsApp",
            command=self.test_whatsapp_reminder,
            bg=theme["success"],
            fg="white",
            font=self.fonts["small"],
            relief='flat',
            padx=10,
            cursor='hand2'
        ).pack(side='left', padx=5)
        
        tk.Button(
            control_frame,
            text="🚀 Send Now to All Today",
            command=self.send_reminders_now,
            bg=theme["danger"],
            fg="white",
            font=self.fonts["small"],
            relief='flat',
            padx=10,
            cursor='hand2'
        ).pack(side='right', padx=5)

    # AUTO-REMINDER SYSTEM METHODS WITH REAL WHATSAPP SENDING
    def start_reminder_system(self):
        """Start the auto-reminder background system"""
        if not self.reminder_running and self.reminder_settings["enabled"]:
            self.reminder_running = True
            self.reminder_thread = threading.Thread(target=self.reminder_loop, daemon=True)
            self.reminder_thread.start()
            self.log_reminder_activity("System", "", "Reminder system started", "SUCCESS")

    def stop_reminder_system(self):
        """Stop the auto-reminder system"""
        self.reminder_running = False
        if self.reminder_thread:
            self.reminder_thread = None
        self.log_reminder_activity("System", "", "Reminder system stopped", "INFO")

    def reminder_loop(self):
        """Main reminder checking loop - checks every 5 minutes"""
        while self.reminder_running:
            try:
                if self.reminder_settings["enabled"]:
                    self.check_and_send_reminders()
                time.sleep(self.reminder_settings["check_interval"])  # Check every 5 minutes
            except Exception as e:
                self.log_reminder_activity("System", "", f"Error: {str(e)}", "ERROR")
                time.sleep(60)  # Wait 1 minute before retrying

    def check_and_send_reminders(self):
        """Check appointments and send WhatsApp reminders"""
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        
        # Check if within business hours
        if not self.is_business_hours(current_time):
            return
        
        for appointment in self.appointments:
            if not appointment.get('enable_reminders', True):
                continue
                
            apt_datetime = self.get_appointment_datetime(appointment)
            if not apt_datetime:
                continue
            
            apt_id = appointment['id']
            time_diff = apt_datetime - now
            
            # Check for different reminder types
            self.check_reminder_type(appointment, apt_id, time_diff, "3_days", timedelta(days=3))
            self.check_reminder_type(appointment, apt_id, time_diff, "1_day", timedelta(days=1))
            self.check_reminder_type(appointment, apt_id, time_diff, "morning", timedelta(hours=12))
            self.check_reminder_type(appointment, apt_id, time_diff, "1_hour", timedelta(hours=1))

    def check_reminder_type(self, appointment, apt_id, time_diff, reminder_type, target_time):
        """Check if a specific reminder type should be sent"""
        setting_key = f"remind_{reminder_type}" if reminder_type != "morning" else "remind_morning"
        
        if not self.reminder_settings.get(setting_key, True):
            return
        
        reminder_key = f"{apt_id}_{reminder_type}"
        
        # Check if already sent
        if reminder_key in self.sent_reminders:
            return
        
        # Check if it's time to send
        should_send = False
        
        if reminder_type == "morning":
            # Send morning reminder if appointment is today and it's morning (8-10 AM)
            if time_diff.days == 0 and 8 <= datetime.now().hour <= 10:
                should_send = True
        elif reminder_type == "1_hour":
            # Send 1 hour reminder with 30-minute tolerance
            if timedelta(minutes=30) <= time_diff <= timedelta(hours=1, minutes=30):
                should_send = True
        else:
            # For 3-day and 1-day reminders, check with 6-hour tolerance
            tolerance = timedelta(hours=6)
            if abs(time_diff - target_time) <= tolerance:
                should_send = True
        
            # Add this to your check_reminder_type method after WhatsApp sending
        if should_send:
            # Send WhatsApp
            whatsapp_success = self.send_auto_whatsapp_reminder(appointment, reminder_type)
            
            # Send Email
            email_success = False
            if appointment.get('enable_email', True) and appointment.get('email'):
                email_success = self.send_email_reminder(appointment, reminder_type)
                if email_success:
                    time.sleep(self.email_settings.get("email_delay", 2))
            
            # Mark as sent if either succeeded
            if whatsapp_success or email_success:
                self.sent_reminders[reminder_key] = datetime.now().isoformat()
                self.save_reminder_data()

    def send_auto_whatsapp_reminder(self, appointment, reminder_type):
        """Send automatic WhatsApp reminder - REAL WHATSAPP SENDING!"""
        try:
            message = self.get_reminder_message(appointment, reminder_type)
            phone = appointment['phone_number']
            
            # Clean and format phone number
            clean_phone = self.clean_phone_number(phone)
            if not clean_phone:
                self.log_reminder_activity(
                    appointment['patient_name'], 
                    phone,
                    f"Invalid phone number for {reminder_type} reminder", 
                    "ERROR"
                )
                return False
            
            # Send WhatsApp message
            if self.reminder_settings.get("auto_send_whatsapp", True):
                success = self.send_whatsapp_message_auto(clean_phone, message)
                
                if success:
                    self.log_reminder_activity(
                        appointment['patient_name'], 
                        clean_phone,
                        f"{reminder_type.replace('_', ' ').title()} reminder sent via WhatsApp", 
                        "SENT ✅"
                    )
                    
                    # Show background notification
                    self.root.after(0, lambda: self.show_whatsapp_notification(appointment, reminder_type))
                    
                    # Add delay between messages
                    time.sleep(self.reminder_settings.get("whatsapp_delay", 3))
                    return True
                else:
                    self.log_reminder_activity(
                        appointment['patient_name'], 
                        clean_phone,
                        f"Failed to send {reminder_type} reminder", 
                        "FAILED ❌"
                    )
                    return False
            else:
                # Just log that reminder would be sent
                self.log_reminder_activity(
                    appointment['patient_name'], 
                    clean_phone,
                    f"{reminder_type.replace('_', ' ').title()} reminder (auto-send disabled)", 
                    "LOGGED 📝"
                )
                return True
                
        except Exception as e:
            self.log_reminder_activity(
                appointment['patient_name'], 
                phone,
                f"Error sending {reminder_type} reminder: {str(e)}", 
                "ERROR ❌"
            )
            return False

    def send_whatsapp_message_auto(self, phone_number, message):
        """Actually send WhatsApp message automatically"""
        try:
            # Create WhatsApp URL
            whatsapp_url = f"https://wa.me/{phone_number}?text={urllib.parse.quote(message)}"
            
            # Open WhatsApp in browser
            success = webbrowser.open(whatsapp_url)
            
            if success:
                # Give time for WhatsApp Web to load
                time.sleep(2)
                
                # Try to auto-send using keyboard simulation (Windows/Mac)
                self.auto_send_whatsapp_message()
                
                return True
            else:
                return False
                
        except Exception as e:
            print(f"WhatsApp send error: {e}")
            return False

    def auto_send_whatsapp_message(self):
        """Simulate Enter key press to send WhatsApp message"""
        try:
            import pyautogui
            # Wait for WhatsApp Web to load
            time.sleep(3)
            # Press Enter to send the message
            pyautogui.press('enter')
        except ImportError:
            # If pyautogui is not available, try alternative methods
            try:
                if platform.system() == "Windows":
                    # Windows: Use VBS script to send Enter key
                    import tempfile
                    vbs_script = '''
                    Set WshShell = WScript.CreateObject("WScript.Shell")
                    WshShell.AppActivate "WhatsApp"
                    WScript.Sleep 1000
                    WshShell.SendKeys "{ENTER}"
                    '''
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.vbs', delete=False) as f:
                        f.write(vbs_script)
                        vbs_file = f.name
                    
                    subprocess.run(['cscript', '/nologo', vbs_file], capture_output=True)
                    os.unlink(vbs_file)
                    
                elif platform.system() == "Darwin":  # macOS
                    # macOS: Use AppleScript
                    applescript = '''
                    tell application "System Events"
                        tell process "WhatsApp"
                            keystroke return
                        end tell
                    end tell
                    '''
                    subprocess.run(['osascript', '-e', applescript])
            except:
                pass  # If automation fails, user can manually send

    def clean_phone_number(self, phone):
        """Clean and format phone number for WhatsApp"""
        if not phone or not phone.strip():
            return None
        
        # Remove all non-digit characters except +
        clean = re.sub(r'[^\d+]', '', phone.strip())
        
        # If no country code, add default (change +1 to your country code)
        if not clean.startswith('+'):
            # Remove leading zeros
            clean = clean.lstrip('0')
            # Add country code (change +1 to your country code)
            clean = '+1' + clean
        
        # Remove + for WhatsApp URL (wa.me expects numbers without +)
        return clean.replace('+', '')

    def get_reminder_message(self, appointment, reminder_type):
        """Generate reminder message based on type"""
        name = appointment['patient_name']
        procedure = appointment['procedure']
        apt_date = appointment.get('appointment_date', 'N/A')
        apt_time = appointment.get('appointment_time', '09:00')
        
        messages = {
            "3_days": f"🏥 Hi {name}! This is a friendly reminder about your {procedure} appointment in 3 days on {apt_date} at {apt_time}. Please confirm your attendance by replying to this message. Thank you! 😊",
            
            "1_day": f"🏥 Hello {name}! Your {procedure} appointment is tomorrow {apt_date} at {apt_time}. Please arrive 15 minutes early for check-in. Looking forward to seeing you! 👋",
            
            "morning": f"🌅 Good morning {name}! You have a {procedure} appointment TODAY at {apt_time}. Please arrive 15 minutes early. Our clinic address: [Your Address]. See you soon! 🏥",
            
            "1_hour": f"⏰ Hi {name}! Your {procedure} appointment is in 1 HOUR at {apt_time}. Please make your way to our clinic now. Don't forget to bring your ID and insurance card. Thank you! 🚗"
        }
        
        return messages.get(reminder_type, f"Hi {name}, reminder about your {procedure} appointment.")

    def show_whatsapp_notification(self, appointment, reminder_type):
        """Show background notification for sent WhatsApp"""
        message = f"📱 WhatsApp sent to {appointment['patient_name']} ({reminder_type.replace('_', ' ').title()} reminder)"
        self.show_toast(message, "success")

    def toggle_whatsapp_auto_send(self):
        """Toggle automatic WhatsApp sending"""
        self.reminder_settings["auto_send_whatsapp"] = not self.reminder_settings.get("auto_send_whatsapp", True)
        self.save_reminder_settings()
        
        status = "enabled" if self.reminder_settings["auto_send_whatsapp"] else "disabled"
        self.show_toast(f"Auto WhatsApp sending {status}! 📱", "info")
        
        self.update_reminder_status()

    def test_whatsapp_reminder(self):
        """Test WhatsApp reminder system with real sending"""
        if not self.appointments:
            self.show_toast("No appointments to test with! Add a patient first.", "warning")
            return
        
        # Find an appointment or create test data
        test_apt = self.appointments[0].copy() if self.appointments else {
            'id': 999,
            'patient_name': 'TEST PATIENT',
            'procedure': 'TEST PROCEDURE',
            'phone_number': '+1234567890',  # Use a test number
            'appointment_date': datetime.now().strftime('%Y-%m-%d'),
            'appointment_time': (datetime.now() + timedelta(hours=1)).strftime('%H:%M')
        }
        
        # Ask user for confirmation
        if messagebox.askyesno(
            "Test WhatsApp Reminder", 
            f"This will send a TEST WhatsApp message to:\n\n"
            f"Patient: {test_apt['patient_name']}\n"
            f"Phone: {test_apt.get('phone_number', 'N/A')}\n\n"
            f"Continue?"
        ):
            success = self.send_auto_whatsapp_reminder(test_apt, "test")
            if success:
                self.show_toast("Test WhatsApp reminder sent! Check your phone/WhatsApp Web.", "success")
            else:
                self.show_toast("Failed to send test reminder. Check phone number and try again.", "error")

    def send_reminders_now(self):
        """Send reminders to all today's appointments immediately"""
        today = datetime.now().strftime('%Y-%m-%d')
        today_appointments = [apt for apt in self.appointments 
                            if apt.get('appointment_date') == today 
                            and apt.get('enable_reminders', True)]
        
        if not today_appointments:
            self.show_toast("No appointments with reminders enabled for today!", "warning")
            return
        
        if messagebox.askyesno(
            "Send Reminders Now", 
            f"This will send WhatsApp reminders to {len(today_appointments)} patients with appointments today.\n\nContinue?"
        ):
            sent_count = 0
            for apt in today_appointments:
                success = self.send_auto_whatsapp_reminder(apt, "manual")
                if success:
                    sent_count += 1
                # Small delay between messages
                time.sleep(self.reminder_settings.get("whatsapp_delay", 3))
            
            self.show_toast(f"Sent {sent_count}/{len(today_appointments)} WhatsApp reminders!", "success")

    def get_appointment_datetime(self, appointment):
        """Get appointment datetime object"""
        try:
            date_str = appointment.get('appointment_date')
            time_str = appointment.get('appointment_time', '09:00')
            
            if not date_str:
                return None
            
            # Parse date and time
            appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            appointment_time = datetime.strptime(time_str, '%H:%M').time()
            
            return datetime.combine(appointment_date, appointment_time)
        except:
            return None

    def is_business_hours(self, current_time):
        """Check if current time is within business hours"""
        try:
            start_time = self.reminder_settings["business_hours_start"]
            end_time = self.reminder_settings["business_hours_end"]
            
            current = datetime.strptime(current_time, '%H:%M').time()
            start = datetime.strptime(start_time, '%H:%M').time()
            end = datetime.strptime(end_time, '%H:%M').time()
            
            return start <= current <= end
        except:
            return True

    def toggle_reminder_system(self):
        """Toggle the reminder system on/off"""
        self.reminder_settings["enabled"] = not self.reminder_settings["enabled"]
        
        if self.reminder_settings["enabled"]:
            self.start_reminder_system()
            self.show_toast("Auto-reminder system enabled! 🔔", "success")
        else:
            self.stop_reminder_system()
            self.show_toast("Auto-reminder system disabled! 🔕", "warning")
        
        self.save_reminder_settings()
        self.update_reminder_status()

    def update_reminder_status(self):
        """Update reminder status display"""
        theme = self.get_theme()
        
        if hasattr(self, 'reminder_status'):
            if self.reminder_settings["enabled"]:
                self.reminder_status.config(
                    text="🔔 Reminders: ON",
                    bg=theme["success"]
                )
            else:
                self.reminder_status.config(
                    text="🔕 Reminders: OFF",
                    bg=theme["danger"]
                )
        
        if hasattr(self, 'whatsapp_status'):
            if self.reminder_settings.get("auto_send_whatsapp", True):
                self.whatsapp_status.config(
                    text="📱 WhatsApp AUTO",
                    bg=theme["accent"]
                )
            else:
                self.whatsapp_status.config(
                    text="📱 Manual Only",
                    bg=theme["warning"]
                )

    def log_reminder_activity(self, patient, phone, activity, status):
        """Log reminder activity with phone number"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Add to log file
        try:
            with open('whatsapp_reminder_log.txt', 'a', encoding='utf-8') as f:
                f.write(f"{timestamp} | {patient} | {phone} | {activity} | {status}\n")
        except:
            pass
        
        # Update UI log if on reminders page
        if hasattr(self, 'reminder_log_tree'):
            self.root.after(0, lambda: self.add_log_entry(timestamp, patient, phone, activity, status))

    def add_log_entry(self, timestamp, patient, phone, activity, status):
        """Add entry to reminder log tree"""
        try:
            time_only = timestamp.split(' ')[1]  # Time only
            patient_short = patient[:12] + "..." if len(patient) > 12 else patient
            phone_short = phone[:12] + "..." if len(phone) > 12 else phone
            activity_short = activity[:15] + "..." if len(activity) > 15 else activity
            
            self.reminder_log_tree.insert('', 0, values=(
                time_only,
                patient_short,
                phone_short,
                activity_short,
                status
            ))
            
            # Keep only last 100 entries
            children = self.reminder_log_tree.get_children()
            if len(children) > 100:
                for item in children[100:]:
                    self.reminder_log_tree.delete(item)
        except:
            pass

    def refresh_reminder_log(self):
        """Refresh the reminder log display"""
        # Clear current log
        for item in self.reminder_log_tree.get_children():
            self.reminder_log_tree.delete(item)
        
        # Load from file
        try:
            if os.path.exists('whatsapp_reminder_log.txt'):
                with open('whatsapp_reminder_log.txt', 'r', encoding='utf-8') as f:
                    lines = f.readlines()[-100:]  # Last 100 entries
                    
                for line in reversed(lines):
                    parts = line.strip().split(' | ')
                    if len(parts) >= 5:
                        timestamp, patient, phone, activity, status = parts[:5]
                        time_only = timestamp.split(' ')[1]
                        self.reminder_log_tree.insert('', 'end', values=(
                            time_only,
                            patient[:12] + "..." if len(patient) > 12 else patient,
                            phone[:12] + "..." if len(phone) > 12 else phone,
                            activity[:15] + "..." if len(activity) > 15 else activity,
                            status
                        ))
        except:
            pass

    def clear_reminder_log(self):
        """Clear the reminder log"""
        if messagebox.askyesno("Clear Log", "Are you sure you want to clear the WhatsApp reminder log?"):
            # Clear file
            try:
                open('whatsapp_reminder_log.txt', 'w').close()
            except:
                pass
            
            # Clear tree
            for item in self.reminder_log_tree.get_children():
                self.reminder_log_tree.delete(item)
            
            self.show_toast("WhatsApp reminder log cleared!", "info")

    def save_reminder_settings(self):
        """Save reminder settings to file"""
        # Update settings from UI
        if hasattr(self, 'reminder_vars'):
            for key, var in self.reminder_vars.items():
                self.reminder_settings[key] = var.get()
        
        if hasattr(self, 'auto_whatsapp_var'):
            self.reminder_settings["auto_send_whatsapp"] = self.auto_whatsapp_var.get()
        
        if hasattr(self, 'start_time_var'):
            self.reminder_settings["business_hours_start"] = self.start_time_var.get()
        
        if hasattr(self, 'end_time_var'):
            self.reminder_settings["business_hours_end"] = self.end_time_var.get()
        
        if hasattr(self, 'delay_var'):
            try:
                self.reminder_settings["whatsapp_delay"] = int(self.delay_var.get())
            except:
                self.reminder_settings["whatsapp_delay"] = 3
        
        try:
            with open('whatsapp_reminder_settings.json', 'w') as f:
                json.dump(self.reminder_settings, f, indent=2)
        except:
            pass
        
        self.update_reminder_status()

    def load_reminder_data(self):
        """Load reminder settings and sent reminders"""
        # Load settings
        try:
            if os.path.exists('whatsapp_reminder_settings.json'):
                with open('whatsapp_reminder_settings.json', 'r') as f:
                    saved_settings = json.load(f)
                    self.reminder_settings.update(saved_settings)
        except:
            pass
        
        # Load sent reminders
        try:
            if os.path.exists('sent_whatsapp_reminders.json'):
                with open('sent_whatsapp_reminders.json', 'r') as f:
                    self.sent_reminders = json.load(f)
        except:
            pass

    def save_reminder_data(self):
        """Save sent reminders data"""
        try:
            with open('sent_whatsapp_reminders.json', 'w') as f:
                json.dump(self.sent_reminders, f, indent=2)
        except:
            pass

    # Continue with all your existing methods but I'll add the key ones for the UI...
    
    def create_add_page(self):
        """Add patient page with all required fields including WhatsApp and clinic date"""
        theme = self.get_theme()

        page = tk.Frame(self.content_area, bg=theme["bg_primary"])
        self.pages["add"] = page

        header = tk.Frame(page, bg=theme["bg_primary"])
        header.pack(fill='x', pady=(0, 20))

        tk.Label(
            header,
            text="➕ New Patient Appointment",
            font=self.fonts["title"],
            bg=theme["bg_primary"],
            fg=theme["text_primary"]
        ).pack(side='left')

        quick_frame = tk.Frame(header, bg=theme["bg_primary"])
        quick_frame.pack(side='right')

        self.create_quick_button(quick_frame, "🗑️", self.clear_form, "Clear Form")
        self.create_quick_button(quick_frame, "📋", self.show_view_page, "View All")

        form_frame = tk.Frame(page, bg=theme["bg_secondary"], relief='flat', bd=1)
        form_frame.pack(fill='both', expand=True, padx=10, pady=10)

        self.form_vars = {}

        main_form = tk.Frame(form_frame, bg=theme["bg_secondary"])
        main_form.pack(fill='none', expand=False, padx=30, pady=30)
        main_form.grid_columnconfigure(0, weight=0)
        main_form.grid_columnconfigure(1, weight=1)

        row = 0

        # Patient Name
        tk.Label(
            main_form,
            text="👤 Patient Name*",
            font=self.fonts["heading"],
            bg=theme["bg_secondary"],
            fg=theme["text_primary"],
            anchor='w'
        ).grid(row=row, column=0, sticky='w', pady=(5, 2))
        self.form_vars["name"] = tk.StringVar()
        tk.Entry(
            main_form,
            textvariable=self.form_vars["name"],
            font=self.fonts["body"],
            bg=theme["bg_primary"],
            fg=theme["text_primary"],
            relief='solid',
            bd=1,
            width=28,
            insertbackground=theme["text_primary"]
        ).grid(row=row, column=1, sticky='ew', pady=(5, 10), padx=(5, 0))
        row += 1

        # Procedure Type & Detail (side by side)
        tk.Label(
            main_form,
            text="🔬 Procedure Type & Details*",
            font=self.fonts["heading"],
            bg=theme["bg_secondary"],
            fg=theme["text_primary"],
            anchor='w'
        ).grid(row=row, column=0, sticky='w', pady=(5, 2))
        proc_frame = tk.Frame(main_form, bg=theme["bg_secondary"])
        proc_frame.grid(row=row, column=1, sticky='ew', pady=(5, 10), padx=(5, 0))
        
        self.form_vars["procedure_type"] = tk.StringVar()
        proc_combo = ttk.Combobox(
            proc_frame,
            textvariable=self.form_vars["procedure_type"],
            values=["DX", "US", "CT", "Mammo", "X-Ray", "MRI", "Blood Test"],
            state="readonly",
            width=10,
            font=self.fonts["body"]
        )
        proc_combo.pack(side='left')
        proc_combo.set("Select Type")
        
        self.form_vars["procedure_details"] = tk.StringVar()
        details_entry = tk.Entry(
            proc_frame,
            textvariable=self.form_vars["procedure_details"],
            font=self.fonts["body"],
            bg=theme["bg_primary"],
            fg=theme["text_primary"],
            relief='solid',
            bd=1,
            width=15,
            insertbackground=theme["text_primary"]
        )
        details_entry.pack(side='left', fill='x', expand=True, padx=(8, 0))
        row += 1

        # Example text
        tk.Label(
            main_form,
            text="💡 e.g. 'US' and 'abdomen', 'CT' and 'brain with contrast'",
            font=self.fonts["small"],
            bg=theme["bg_secondary"],
            fg=theme["text_secondary"],
            anchor='w'
        ).grid(row=row, column=1, sticky='w', pady=(0, 10), padx=(5, 0))
        row += 1

        # Primary WhatsApp Phone Number
        tk.Label(
            main_form,
            text="📱 WhatsApp Phone Number*",
            font=self.fonts["heading"],
            bg=theme["bg_secondary"],
            fg=theme["text_primary"],
            anchor='w'
        ).grid(row=row, column=0, sticky='w', pady=(5, 2))
        self.form_vars["phone1"] = tk.StringVar()
        phone_entry = tk.Entry(
            main_form,
            textvariable=self.form_vars["phone1"],
            font=self.fonts["body"],
            bg=theme["bg_primary"],
            fg=theme["text_primary"],
            relief='solid',
            bd=1,
            width=28,
            insertbackground=theme["text_primary"]
        )
        phone_entry.grid(row=row, column=1, sticky='ew', pady=(5, 5), padx=(5, 0))
        row += 1
        
        # Phone number help text
        tk.Label(
            main_form,
            text="💡 Include country code (e.g., +1234567890 for US, +441234567890 for UK)",
            font=self.fonts["small"],
            bg=theme["bg_secondary"],
            fg=theme["text_secondary"],
            anchor='w'
        ).grid(row=row, column=1, sticky='w', pady=(0, 10), padx=(5, 0))
        row += 1

        # Secondary Phone Number
        tk.Label(
            main_form,
            text="📞 Secondary Phone (Optional)",
            font=self.fonts["body"],
            bg=theme["bg_secondary"],
            fg=theme["text_primary"],
            anchor='w'
        ).grid(row=row, column=0, sticky='w', pady=(5, 2))
        self.form_vars["phone2"] = tk.StringVar()
        tk.Entry(
            main_form,
            textvariable=self.form_vars["phone2"],
            font=self.fonts["body"],
            bg=theme["bg_primary"],
            fg=theme["text_primary"],
            relief='solid',
            bd=1,
            width=28,
            insertbackground=theme["text_primary"]
        ).grid(row=row, column=1, sticky='ew', pady=(5, 10), padx=(5, 0))
        row += 1

        # Email Address
        tk.Label(
            main_form,
            text="📧 Email Address (Optional)",
            font=self.fonts["body"],
            bg=theme["bg_secondary"],
            fg=theme["text_primary"],
            anchor='w'
        ).grid(row=row, column=0, sticky='w', pady=(5, 2))
        self.form_vars["email"] = tk.StringVar()
        tk.Entry(
            main_form,
            textvariable=self.form_vars["email"],
            font=self.fonts["body"],
            bg=theme["bg_primary"],
            fg=theme["text_primary"],
            relief='solid',
            bd=1,
            width=28,
            insertbackground=theme["text_primary"]
        ).grid(row=row, column=1, sticky='ew', pady=(5, 10), padx=(5, 0))
        row += 1

        # Clinic Date (FIXED - NOW INCLUDED)
        tk.Label(
            main_form,
            text="🏥 Clinic Date (Optional)",
            font=self.fonts["body"],
            bg=theme["bg_secondary"],
            fg=theme["text_primary"],
            anchor='w'
        ).grid(row=row, column=0, sticky='w', pady=(5, 2))
        self.form_vars["clinic_date"] = tk.StringVar()
        clinic_date_entry = tk.Entry(
            main_form,
            textvariable=self.form_vars["clinic_date"],
            font=self.fonts["body"],
            bg=theme["bg_primary"],
            fg=theme["text_primary"],
            relief='solid',
            bd=1,
            width=28,
            insertbackground=theme["text_primary"]
        )
        clinic_date_entry.grid(row=row, column=1, sticky='ew', pady=(5, 5), padx=(5, 0))
        row += 1
        
        # Clinic date help text
        tk.Label(
            main_form,
            text="💡 Format: YYYY-MM-DD (e.g., 2025-06-15) or leave blank",
            font=self.fonts["small"],
            bg=theme["bg_secondary"],
            fg=theme["text_secondary"],
            anchor='w'
        ).grid(row=row, column=1, sticky='w', pady=(0, 10), padx=(5, 0))
        row += 1

        # Appointment Date with time
        tk.Label(
            main_form,
            text="📋 Appointment Date & Time*",
            font=self.fonts["heading"],
            bg=theme["bg_secondary"],
            fg=theme["text_primary"],
            anchor='w'
        ).grid(row=row, column=0, sticky='w', pady=(5, 2))
        
        datetime_frame = tk.Frame(main_form, bg=theme["bg_secondary"])
        datetime_frame.grid(row=row, column=1, sticky='ew', pady=(5, 10), padx=(5, 0))
        
        self.appointment_date_entry = DateEntry(
            datetime_frame,
            width=15,
            background=theme["accent"],
            foreground='white',
            borderwidth=1,
            font=self.fonts["body"],
            mindate=date.today()
        )
        self.appointment_date_entry.pack(side='left')
        
        # Time entry
        self.form_vars["appointment_time"] = tk.StringVar(value="09:00")
        time_entry = tk.Entry(
            datetime_frame,
            textvariable=self.form_vars["appointment_time"],
            font=self.fonts["body"],
            bg=theme["bg_primary"],
            fg=theme["text_primary"],
            relief='solid',
            bd=1,
            width=8,
            insertbackground=theme["text_primary"]
        )
        time_entry.pack(side='left', padx=(8, 0))
        
        tk.Label(
            datetime_frame,
            text="(HH:MM)",
            font=self.fonts["small"],
            bg=theme["bg_secondary"],
            fg=theme["text_secondary"]
        ).pack(side='left', padx=(5, 0))
        row += 1

        # Email & WhatsApp Auto-reminder option (expanded)
        communication_frame = tk.LabelFrame(
            main_form,
            text="📱📧 Auto-Reminders (WhatsApp & Email)",
            bg=theme["bg_secondary"],
            fg=theme["accent"],
            font=self.fonts["heading"]
        )
        communication_frame.grid(row=row, column=0, columnspan=2, sticky='ew', pady=15)
        communication_frame.grid_columnconfigure(0, weight=1)

        # WhatsApp reminders checkbox
        self.form_vars["enable_reminders"] = tk.BooleanVar(value=True)
        whatsapp_cb = tk.Checkbutton(
            communication_frame,
            text="📱 Send automatic WhatsApp reminders",
            variable=self.form_vars["enable_reminders"],
            bg=theme["bg_secondary"],
            fg=theme["text_primary"],
            font=self.fonts["body"],
            anchor='w'
        )
        whatsapp_cb.pack(anchor='w', padx=10, pady=5, fill='x')

        # Email reminders checkbox
        self.form_vars["enable_email"] = tk.BooleanVar(value=True)
        email_cb = tk.Checkbutton(
            communication_frame,
            text="📧 Send automatic email reminders",
            variable=self.form_vars["enable_email"],
            bg=theme["bg_secondary"],
            fg=theme["text_primary"],
            font=self.fonts["body"],
            anchor='w'
        )
        email_cb.pack(anchor='w', padx=10, pady=5, fill='x')

        # Reminder timing info
        tk.Label(
            communication_frame,
            text="⏰ Timing: 3 days, 1 day, morning, 1 hour before appointment",
            font=self.fonts["small"],
            bg=theme["bg_secondary"],
            fg=theme["text_secondary"],
            anchor='w'
        ).pack(anchor='w', padx=10, pady=(0, 10))
        row += 1

        # Notes (optional)
        tk.Label(
            main_form,
            text="📝 Notes (Optional)",
            font=self.fonts["heading"],
            bg=theme["bg_secondary"],
            fg=theme["text_primary"],
            anchor='w'
        ).grid(row=row, column=0, sticky='nw', pady=(5, 2))
        
        notes_frame = tk.Frame(main_form, bg=theme["bg_secondary"])
        notes_frame.grid(row=row, column=1, sticky='ew', pady=(5, 15), padx=(5, 0))
        
        self.notes_text = tk.Text(
            notes_frame,
            font=self.fonts["body"],
            bg=theme["bg_primary"],
            fg=theme["text_primary"],
            relief='solid',
            bd=1,
            height=4,
            width=28,
            insertbackground=theme["text_primary"],
            wrap='word'
        )
        self.notes_text.pack(fill='both', expand=True)
        row += 1

        # Action buttons
        actions_frame = tk.Frame(main_form, bg=theme["bg_secondary"])
        actions_frame.grid(row=row, column=0, columnspan=2, pady=30)
        
        # Save Patient button
        tk.Button(
            actions_frame,
            text="💾 Save Patient",
            command=self.add_appointment,
            bg=theme["success"],
            fg="white",
            font=self.fonts["heading"],
            relief='flat',
            padx=30,
            pady=12,
            cursor='hand2'
        ).pack(side='left', padx=10)
        
        # Quick Save & New button
        tk.Button(
            actions_frame,
            text="⚡ Quick Save & New",
            command=self.quick_save_and_new,
            bg=theme["accent"],
            fg="white",
            font=self.fonts["body"],
            relief='flat',
            padx=20,
            pady=10,
            cursor='hand2'
        ).pack(side='left', padx=10)
        
        # Clear button
        tk.Button(
            actions_frame,
            text="🗑️ Clear Form",
            command=self.clear_form,
            bg=theme["warning"],
            fg="white",
            font=self.fonts["body"],
            relief='flat',
            padx=20,
            pady=10,
            cursor='hand2'
        ).pack(side='left', padx=10)

    def add_appointment(self):
        """Add new appointment with WhatsApp reminder validation - FIXED"""
        # Get form data
        name = self.form_vars.get('name', tk.StringVar()).get().strip()
        procedure_type = self.form_vars.get('procedure_type', tk.StringVar()).get().strip()
        procedure_details = self.form_vars.get('procedure_details', tk.StringVar()).get().strip()
        phone1 = self.form_vars.get('phone1', tk.StringVar()).get().strip()
        phone2 = self.form_vars.get('phone2', tk.StringVar()).get().strip()
        clinic_date = self.form_vars.get('clinic_date', tk.StringVar()).get().strip()
        appointment_time = self.form_vars.get('appointment_time', tk.StringVar()).get().strip()
        enable_reminders = self.form_vars.get('enable_reminders', tk.BooleanVar()).get()
        email = self.form_vars.get('email', tk.StringVar()).get().strip()
        enable_email = self.form_vars.get('enable_email', tk.BooleanVar()).get()
        
        # Get notes from text widget
        notes = ""
        if hasattr(self, 'notes_text'):
            notes = self.notes_text.get('1.0', tk.END).strip()
        
        # Validation - if any validation fails, return False and DON'T clear form
        if not all([name, procedure_type, phone1]) or procedure_type == "Select Type":
            self.show_toast("Please fill in all required fields (Name, Procedure, WhatsApp Phone)!", "error")
            return False
        
        if email and not self.validate_email(email):
            self.show_toast("Please enter a valid email address!", "error")
            return False
        
        # Validate WhatsApp phone number
        clean_phone = self.clean_phone_number(phone1)
        if not clean_phone:
            self.show_toast("Please enter a valid WhatsApp phone number with country code (e.g., +1234567890)!", "error")
            return False
        
        # Validate secondary phone if provided
        if phone2 and not self.clean_phone_number(phone2):
            self.show_toast("Please enter a valid secondary phone number!", "error")
            return False
        
        # Validate appointment time
        if not self.validate_time(appointment_time):
            self.show_toast("Please enter a valid time (HH:MM format, e.g., 09:30)!", "error")
            return False
        
        # Validate clinic date if provided
        if clinic_date and not self.validate_date(clinic_date):
            self.show_toast("Please enter clinic date in YYYY-MM-DD format (e.g., 2025-06-15) or leave blank!", "error")
            return False
        
        # Create appointment object
        full_procedure = procedure_type.upper()
        if procedure_details:
            full_procedure += f": {procedure_details}"
            
        # Add email to the appointment object
        appointment = {
            'id': len(self.appointments) + 1,
            'patient_name': name,
            'procedure': full_procedure,
            'phone_number': phone1,
            'phone_number2': phone2,
            'email': email,  # ADD THIS LINE
            'clinic_date': clinic_date,
            'appointment_date': self.appointment_date_entry.get_date().strftime('%Y-%m-%d'),
            'appointment_time': appointment_time,
            'enable_reminders': enable_reminders,
            'enable_email': enable_email,  # ADD THIS LINE
            'notes': notes,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
                
        # Save the appointment with proper error handling
        try:
            self.appointments.append(appointment)
            self.save_data()
            self.update_stats()
            
            # Log appointment creation
            if enable_reminders:
                self.log_reminder_activity(
                    name, 
                    phone1,
                    f"New appointment created with WhatsApp reminders enabled", 
                    "CREATED ✅"
                )
        
        # SUCCESS: Only clear form AFTER successful save
            self.clear_form()
        
            reminder_status = "with WhatsApp auto-reminders" if enable_reminders else "without auto-reminders"
            self.show_toast(f"✅ Patient saved! ID: {appointment['id']} {reminder_status} - Form cleared", "success")
            return True
        
        except Exception as e:
        # FAILURE: Don't clear the form, show error message
            self.show_toast(f"❌ Failed to save patient: {str(e)}", "error")
            return False

    def validate_date(self, date_str):
        """Validate date format YYYY-MM-DD"""
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except:
            return False

    def validate_time(self, time_str):
        """Validate time format HH:MM"""
        try:
            datetime.strptime(time_str, '%H:%M')
            return True
        except:
            return False

    def clear_form(self):
        """Clear all form fields"""
        for var in self.form_vars.values():
            if isinstance(var, tk.StringVar):
                var.set("")
            elif isinstance(var, tk.BooleanVar):
                var.set(True)  # Default to enable reminders
        
        if hasattr(self, 'form_vars') and 'procedure_type' in self.form_vars:
            self.form_vars['procedure_type'].set("Select Type")
        
        if hasattr(self, 'appointment_date_entry'):
            self.appointment_date_entry.set_date(date.today())
        
        if hasattr(self, 'form_vars') and 'appointment_time' in self.form_vars:
            self.form_vars['appointment_time'].set("09:00")
        
        if hasattr(self, 'notes_text'):
            self.notes_text.delete('1.0', tk.END)
        
        self.show_toast("Form cleared", "info")

    # Add the remaining essential methods for the complete app...

    def navigate_to(self, command, page_id):
        """Navigate to a specific page"""
        theme = self.get_theme()
        for btn, pid in self.nav_buttons:
            if pid == page_id:
                btn.config(bg=theme["accent"], fg="white")
            else:
                btn.config(bg=theme["bg_accent"], fg=theme["text_primary"])
        
        self.current_page = page_id
        command()

    def show_add_page(self):
        """Show add appointment page"""
        self.hide_all_pages()
        self.pages["add"].pack(fill='both', expand=True)

    def show_reminders_page(self):
        """Show reminders page"""
        self.hide_all_pages()
        self.pages["reminders"].pack(fill='both', expand=True)
        self.refresh_reminder_log()

    def hide_all_pages(self):
        """Hide all pages"""
        for page in self.pages.values():
            page.pack_forget()

    def create_quick_button(self, parent, icon, command, tooltip):
        """Create a compact icon button"""
        theme = self.get_theme()
        
        btn = tk.Button(
            parent,
            text=icon,
            command=command,
            bg=theme["accent"],
            fg="white",
            font=self.fonts["body"],
            relief='flat',
            padx=8,
            pady=4,
            cursor='hand2'
        )
        btn.pack(side='left', padx=2)
        return btn

    def show_toast(self, message, type="info"):
        """Show toast notification"""
        theme = self.get_theme()
        colors = {
            "info": theme["accent"],
            "success": theme["success"],
            "warning": theme["warning"],
            "error": theme["danger"]
        }
        
        toast = tk.Toplevel(self.root)
        toast.wm_overrideredirect(True)
        toast.wm_attributes("-topmost", True)
        
        # Position at top-right
        toast.geometry(f"350x70+{self.root.winfo_x() + self.root.winfo_width() - 370}+{self.root.winfo_y() + 20}")
        
        frame = tk.Frame(toast, bg=colors[type], relief='flat', bd=1)
        frame.pack(fill='both', expand=True)
        
        tk.Label(
            frame,
            text=message,
            bg=colors[type],
            fg="white",
            font=self.fonts["body"],
            wraplength=320
        ).pack(expand=True, padx=15, pady=15)
        
        # Auto-hide after 4 seconds
        self.root.after(4000, toast.destroy)

    def create_view_page(self):
        """Create compact appointments view page with WhatsApp status"""
        theme = self.get_theme()
        
        page = tk.Frame(self.content_area, bg=theme["bg_primary"])
        self.pages["view"] = page
        
        # Header with controls
        header = tk.Frame(page, bg=theme["bg_primary"])
        header.pack(fill='x', pady=(0, 10))
        
        tk.Label(
            header,
            text="📋 All Appointments",
            font=self.fonts["title"],
            bg=theme["bg_primary"],
            fg=theme["text_primary"]
        ).pack(side='left')
        
        # Control buttons
        controls = tk.Frame(header, bg=theme["bg_primary"])
        controls.pack(side='right')
        
        self.create_quick_button(controls, "🔄", self.refresh_appointments, "Refresh")
        self.create_quick_button(controls, "✏️", self.edit_appointment, "Edit Selected")
        self.create_quick_button(controls, "🗑️", self.delete_appointment, "Delete Selected")
        self.create_quick_button(controls, "📱", self.send_manual_whatsapp, "Send Manual WhatsApp")
        
        # Compact treeview
        tree_frame = tk.Frame(page, bg=theme["bg_secondary"], relief='flat', bd=1)
        tree_frame.pack(fill='both', expand=True)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame)
        v_scrollbar.pack(side='right', fill='y')
        
        h_scrollbar = ttk.Scrollbar(tree_frame, orient='horizontal')
        h_scrollbar.pack(side='bottom', fill='x')
        
        # Treeview with WhatsApp status column
        self.appointments_tree = ttk.Treeview(
            tree_frame,
            columns=('ID', 'Name', 'Procedure', 'Phone', 'Email', 'DateTime', 'WhatsApp', 'Notes'),
            show='headings',
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set,
            height=15
        )
        
        v_scrollbar.config(command=self.appointments_tree.yview)
        h_scrollbar.config(command=self.appointments_tree.xview)
        
        # Updated column setup with WhatsApp status
        columns = [
            ('ID', 40),
            ('Name', 120),
            ('Procedure', 110),
            ('Phone', 100),
            ('Email', 120),
            ('DateTime', 120),
            ('WhatsApp', 80),
            ('Notes', 100)
        ]
        
        for col, width in columns:
            self.appointments_tree.heading(col, text=col)
            self.appointments_tree.column(col, width=width, anchor='center')
        
        self.appointments_tree.pack(fill='both', expand=True)

    def create_reports_page(self):
        """Create comprehensive reports and analytics page"""
        theme = self.get_theme()
        
        page = tk.Frame(self.content_area, bg=theme["bg_primary"])
        self.pages["reports"] = page  # Changed from "search" to "reports"
        
        # Header
        tk.Label(
            page,
            text="📊 Reports & Analytics",
            font=self.fonts["title"],
            bg=theme["bg_primary"],
            fg=theme["text_primary"]
        ).pack(pady=(0, 20))
    
    # ... new reporting dashboard code ...)
        
        # Search controls
        search_frame = tk.Frame(page, bg=theme["bg_secondary"], relief='flat', bd=1)
        search_frame.pack(fill='x', pady=(0, 10), padx=5)
        
        search_inner = tk.Frame(search_frame, bg=theme["bg_secondary"])
        search_inner.pack(fill='x', padx=15, pady=10)
        
        tk.Label(
            search_inner,
            text="Search:",
            font=self.fonts["body"],
            bg=theme["bg_secondary"],
            fg=theme["text_primary"]
        ).pack(side='left')
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.live_search)
        
        search_entry = tk.Entry(
            search_inner,
            textvariable=self.search_var,
            font=self.fonts["body"],
            bg=theme["bg_primary"],
            fg=theme["text_primary"],
            relief='flat',
            bd=1,
            insertbackground=theme["text_primary"]
        )
        search_entry.pack(side='left', fill='x', expand=True, padx=(10, 5))
        
        clear_search_btn = tk.Button(
            search_inner,
            text="❌",
            command=self.clear_search,
            bg=theme["danger"],
            fg="white",
            font=self.fonts["small"],
            relief='flat',
            padx=5,
            cursor='hand2'
        )
        clear_search_btn.pack(side='right')
        
        # Search results
        results_frame = tk.Frame(page, bg=theme["bg_secondary"], relief='flat', bd=1)
        results_frame.pack(fill='both', expand=True, padx=5)
        
        results_scrollbar = ttk.Scrollbar(results_frame)
        results_scrollbar.pack(side='right', fill='y')
        
        self.search_tree = ttk.Treeview(
            results_frame,
            columns=('ID', 'Name', 'Procedure', 'Phone', 'DateTime', 'WhatsApp', 'Notes'),
            show='headings',
            yscrollcommand=results_scrollbar.set,
            height=12
        )
        
        results_scrollbar.config(command=self.search_tree.yview)
        
        for col, width in [('ID', 40), ('Name', 120), ('Procedure', 110), ('Phone', 100), ('DateTime', 120), ('WhatsApp', 80), ('Notes', 100)]:
            self.search_tree.heading(col, text=col)
            self.search_tree.column(col, width=width, anchor='center')
        
        self.search_tree.pack(fill='both', expand=True)

    def generate_daily_report(self):
        """Generate daily appointment report"""
        # Implementation here
        
    def generate_weekly_report(self):
        """Generate weekly appointment summary"""
        # Implementation here
        
    def generate_monthly_report(self):
        """Generate monthly overview report"""
        # Implementation here
        
    def generate_procedure_analytics(self):
        """Generate procedure distribution analytics"""
        # Implementation here
        
    def generate_whatsapp_stats(self):
        """Generate WhatsApp communication statistics"""
        # Implementation here
        
    def export_report_pdf(self):
        """Export report to PDF"""
        # Implementation here
        
    def schedule_report(self):
        """Schedule automatic report generation"""    

    def create_dashboard_page(self):
        """Create dashboard with WhatsApp statistics"""
        theme = self.get_theme()
        
        page = tk.Frame(self.content_area, bg=theme["bg_primary"])
        self.pages["dashboard"] = page
        
        # Header
        tk.Label(
            page,
            text="📊 Dashboard",
            font=self.fonts["title"],
            bg=theme["bg_primary"],
            fg=theme["text_primary"]
        ).pack(pady=(0, 20))
        
        # Stats cards
        stats_container = tk.Frame(page, bg=theme["bg_primary"])
        stats_container.pack(fill='x', pady=(0, 20))
        
        # Create stat cards
        self.create_stat_card(stats_container, "Total Appointments", "📋", "total_count")
        self.create_stat_card(stats_container, "WhatsApp Sent", "📱", "whatsapp_count")
        self.create_stat_card(stats_container, "This Week", "📅", "week_count")
        
        # Procedure distribution
        procedures_frame = tk.LabelFrame(
            page,
            text="🔬 Procedure Distribution",
            bg=theme["bg_secondary"],
            fg=theme["text_primary"],
            font=self.fonts["body"]
        )
        procedures_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.procedure_listbox = tk.Listbox(
            procedures_frame,
            bg=theme["bg_primary"],
            fg=theme["text_primary"],
            font=self.fonts["body"],
            relief='flat'
        )
        self.procedure_listbox.pack(fill='both', expand=True, padx=10, pady=10)

    def create_stat_card(self, parent, title, icon, var_name):
        """Create a statistics card"""
        theme = self.get_theme()
        
        card = tk.Frame(parent, bg=theme["accent"], relief='flat', bd=1)
        card.pack(side='left', fill='both', expand=True, padx=5)
        
        tk.Label(
            card,
            text=icon,
            font=("Arial", 20),
            bg=theme["accent"],
            fg="white"
        ).pack(pady=(10, 5))
        
        value_label = tk.Label(
            card,
            text="0",
            font=self.fonts["title"],
            bg=theme["accent"],
            fg="white"
        )
        value_label.pack()
        
        tk.Label(
            card,
            text=title,
            font=self.fonts["small"],
            bg=theme["accent"],
            fg="white"
        ).pack(pady=(0, 10))
        
        setattr(self, f"{var_name}_label", value_label)

    def create_settings_page(self):
        """Create settings page"""
        theme = self.get_theme()
        
        page = tk.Frame(self.content_area, bg=theme["bg_primary"])
        self.pages["settings"] = page
    
        
        # Header
        tk.Label(
            page,
            text="⚙️ Settings",
            font=self.fonts["title"],
            bg=theme["bg_primary"],
            fg=theme["text_primary"]
        ).pack(pady=(0, 20))
        
        # Settings sections
        sections = tk.Frame(page, bg=theme["bg_primary"])
        sections.pack(fill='both', expand=True)
        
        # Theme section
        theme_section = tk.LabelFrame(
            sections,
            text="🎨 Appearance",
            bg=theme["bg_secondary"],
            fg=theme["text_primary"],
            font=self.fonts["body"]
        )
        theme_section.pack(fill='x', padx=5, pady=5)
        
        theme_frame = tk.Frame(theme_section, bg=theme["bg_secondary"])
        theme_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(
            theme_frame,
            text="Theme:",
            bg=theme["bg_secondary"],
            fg=theme["text_primary"],
            font=self.fonts["body"]
        ).pack(side='left')
        
        theme_toggle = tk.Button(
            theme_frame,
            text=f"{self.current_theme.title()} Mode",
            command=self.toggle_theme,
            bg=theme["accent"],
            fg="white",
            font=self.fonts["body"],
            relief='flat',
            padx=15,
            cursor='hand2'
        )
        theme_toggle.pack(side='right')
        
        # WhatsApp section
        whatsapp_section = tk.LabelFrame(
            sections,
            text="📱 WhatsApp Settings",
            bg=theme["bg_secondary"],
            fg=theme["text_primary"],
            font=self.fonts["body"]
        )
        whatsapp_section.pack(fill='x', padx=5, pady=5)
        
        whatsapp_frame = tk.Frame(whatsapp_section, bg=theme["bg_secondary"])
        whatsapp_frame.pack(fill='x', padx=10, pady=10)
        
        # Add this after the WhatsApp section in your settings page
        # Email section
        email_section = tk.LabelFrame(
            sections,
            text="📧 Email Settings",
            bg=theme["bg_secondary"],
            fg=theme["text_primary"],
            font=self.fonts["body"]
        )
        email_section.pack(fill='x', padx=5, pady=5)

        email_frame = tk.Frame(email_section, bg=theme["bg_secondary"])
        email_frame.pack(fill='x', padx=10, pady=10)

        # Email status
        email_status = "CONFIGURED" if self.email_settings.get("email_address") else "NOT CONFIGURED"
        email_color = theme["success"] if self.email_settings.get("email_address") else theme["danger"]

        tk.Label(
            email_frame,
            text=f"Status: {email_status}",
            bg=theme["bg_secondary"],
            fg=email_color,
            font=self.fonts["body"]
        ).pack(side='left')

        tk.Button(
            email_frame,
            text="📧 Configure Email",
            command=self.create_email_settings_dialog,
            bg=theme["accent"],
            fg="white",
            font=self.fonts["body"],
            relief='flat',
            padx=15,
            cursor='hand2'
        ).pack(side='right')
        
        # WhatsApp status
        status_text = "AUTO ENABLED" if self.reminder_settings.get("auto_send_whatsapp", True) else "MANUAL ONLY"
        status_color = theme["success"] if self.reminder_settings.get("auto_send_whatsapp", True) else theme["warning"]
        
        tk.Label(
            whatsapp_frame,
            text=f"Status: {status_text}",
            bg=theme["bg_secondary"],
            fg=status_color,
            font=self.fonts["body"]
        ).pack(side='left')
        
        tk.Button(
            whatsapp_frame,
            text="⚙️ Configure Auto-WhatsApp",
            command=lambda: self.navigate_to(self.show_reminders_page, "reminders"),
            bg=theme["accent"],
            fg="white",
            font=self.fonts["body"],
            relief='flat',
            padx=15,
            cursor='hand2'
        ).pack(side='right')
        
        # Data section
        data_section = tk.LabelFrame(
            sections,
            text="💾 Data Management",
            bg=theme["bg_secondary"],
            fg=theme["text_primary"],
            font=self.fonts["body"]
        )
        data_section.pack(fill='x', padx=5, pady=5)
        
        data_frame = tk.Frame(data_section, bg=theme["bg_secondary"])
        data_frame.pack(fill='x', padx=10, pady=10)
        
        # Export buttons
        export_btns = [
            ("📊 Export CSV", self.export_to_csv, theme["success"]),
            ("📈 Export Excel", self.export_to_excel, theme["success"]),
            ("📤 Export JSON", self.export_data, theme["accent"]),
            ("📥 Import Data", self.import_data, theme["warning"])
        ]
        
        for text, command, color in export_btns:
            if "Excel" in text and not PANDAS_AVAILABLE:
                continue
                
            btn = tk.Button(
                data_frame,
                text=text,
                command=command,
                bg=color,
                fg="white",
                font=self.fonts["small"],
                relief='flat',
                padx=10,
                pady=5,
                cursor='hand2'
            )
            btn.pack(side='left', padx=2)

    def create_floating_actions(self):
        """Create floating action buttons with WhatsApp controls"""
        theme = self.get_theme()
        
        self.fab_frame = tk.Frame(
            self.root,
            bg=theme["accent"],
            relief='flat'
        )
        self.fab_frame.place(relx=0.95, rely=0.9, anchor='center')
        
        # Main FAB
        self.main_fab = tk.Button(
            self.fab_frame,
            text="📱",
            command=self.toggle_fab_menu,
            bg=theme["accent"],
            fg="white",
            font=("Arial", 16),
            relief='flat',
            width=3,
            height=1,
            cursor='hand2'
        )
        self.main_fab.pack()
        
        # Hidden action buttons
        self.fab_actions = tk.Frame(self.fab_frame, bg=theme["accent"])
        self.fab_menu_visible = False
        
        fab_buttons = [
            ("💾", self.quick_save, "Quick Save"),
            ("🔔", self.toggle_reminder_system, "Toggle Auto-Reminders"),
            ("📱", self.toggle_whatsapp_auto_send, "Toggle Auto-WhatsApp"),
            ("🔄", self.refresh_all, "Refresh All")
        ]
        
        for icon, command, tooltip in fab_buttons:
            btn = tk.Button(
                self.fab_actions,
                text=icon,
                command=command,
                bg=theme["success"],
                fg="white",
                font=("Arial", 12),
                relief='flat',
                width=2,
                cursor='hand2'
            )
            btn.pack(pady=1)

    def create_notification_system(self):
        """Create toast notification system"""
        self.notifications = []

    def toggle_theme(self):
        """Toggle between light and dark themes."""
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        self.apply_theme()
        self.show_toast(f"Switched to {self.current_theme} theme", "success")

    def apply_theme(self):
        """Apply current theme to all widgets"""
        theme = self.get_theme()
        
        # Update root
        self.root.configure(bg=theme["bg_primary"])
        
        # Update theme button
        if hasattr(self, 'theme_btn'):
            self.theme_btn.config(
                text="🌙" if self.current_theme == "light" else "☀️",
                bg=theme["accent"]
            )
        
        # Update reminder status
        self.update_reminder_status()

    def toggle_fab_menu(self):
        """Toggle floating action button menu"""
        if self.fab_menu_visible:
            self.fab_actions.pack_forget()
            self.main_fab.config(text="📱")
        else:
            self.fab_actions.pack(side='top', pady=(0, 5))
            self.main_fab.config(text="✕")
        
        self.fab_menu_visible = not self.fab_menu_visible

    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts"""
        self.root.bind('<Control-s>', lambda e: self.quick_save())
        self.root.bind('<Control-n>', lambda e: self.navigate_to(self.show_add_page, "add"))
        self.root.bind('<Control-f>', lambda e: self.navigate_to(self.show_reports_page, "reports"))
        self.root.bind('<Control-r>', lambda e: self.refresh_all())
        self.root.bind('<F1>', lambda e: self.show_help())
        self.root.bind('<Control-w>', lambda e: self.navigate_to(self.show_reminders_page, "reminders"))

    def start_auto_save(self):
        """Start auto-save functionality"""
        if self.auto_save_active:
            self.save_data()
            self.save_reminder_data()
            self.root.after(30000, self.start_auto_save)  # Auto-save every 30 seconds

    def quick_save(self):
        """Quick save current form"""
        if self.current_page == "add":
            self.add_appointment()
        else:
            self.save_data()
            self.show_toast("Data saved successfully!", "success")

    def quick_save_and_new(self):
        """Quick save and prepare for new entry"""
        if self.add_appointment():
            self.clear_form()
            self.show_toast("Patient saved! Ready for next entry.", "success")

    def send_manual_whatsapp(self):
        """Send manual WhatsApp message to selected patient"""
        selected = self.appointments_tree.selection()
        if not selected:
            self.show_toast("Please select an appointment to send WhatsApp message!", "warning")
            return
        
        item = self.appointments_tree.item(selected[0])
        apt_id = int(item['values'][0])
        
        # Find appointment
        appointment = next((apt for apt in self.appointments if apt['id'] == apt_id), None)
        if not appointment:
            self.show_toast("Appointment not found!", "error")
            return
        
        self.create_manual_whatsapp_dialog(appointment)

    def create_manual_whatsapp_dialog(self, appointment):
        """Create manual WhatsApp message dialog"""
        theme = self.get_theme()
        
        dialog = tk.Toplevel(self.root)
        dialog.title("📱 Send Manual WhatsApp")
        dialog.geometry("500x600")
        dialog.configure(bg=theme["bg_primary"])
        dialog.grab_set()
        dialog.resizable(False, False)
        
        # Center the dialog
        dialog.transient(self.root)
        
        # Header
        header = tk.Frame(dialog, bg=theme["success"], height=80)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text="📱 Manual WhatsApp Message",
            font=self.fonts["title"],
            bg=theme["success"],
            fg="white"
        ).pack(expand=True)
        
        # Patient info
        info_frame = tk.Frame(dialog, bg=theme["bg_secondary"])
        info_frame.pack(fill='x', padx=20, pady=(20, 10))
        
        tk.Label(
            info_frame,
            text=f"Patient: {appointment['patient_name']}",
            font=self.fonts["heading"],
            bg=theme["bg_secondary"],
            fg=theme["text_primary"]
        ).pack(anchor='w', pady=2)
        
        tk.Label(
            info_frame,
            text=f"Phone: {appointment['phone_number']}",
            font=self.fonts["body"],
            bg=theme["bg_secondary"],
            fg=theme["text_secondary"]
        ).pack(anchor='w', pady=2)
        
        appointment_datetime = f"{appointment.get('appointment_date', 'N/A')} at {appointment.get('appointment_time', '09:00')}"
        tk.Label(
            info_frame,
            text=f"Appointment: {appointment_datetime}",
            font=self.fonts["body"],
            bg=theme["bg_secondary"],
            fg=theme["text_secondary"]
        ).pack(anchor='w', pady=2)
        
        # Quick templates
        templates_frame = tk.LabelFrame(
            dialog,
            text="📝 Quick Templates",
            bg=theme["bg_primary"],
            fg=theme["text_primary"],
            font=self.fonts["body"]
        )
        templates_frame.pack(fill='x', padx=20, pady=10)
        
        templates = [
            ("Reminder", f"Hi {appointment['patient_name']}, reminder about your {appointment['procedure']} appointment on {appointment_datetime}. Thank you!"),
            ("Confirmation", f"Hello {appointment['patient_name']}, your appointment is confirmed for {appointment_datetime}. Please arrive 15 minutes early."),
            ("Follow-up", f"Hi {appointment['patient_name']}, hope your visit went well. If you have questions, please contact us.")
        ]
        
        template_var = tk.StringVar()
        
        for title, template in templates:
            tk.Radiobutton(
                templates_frame,
                text=title,
                variable=template_var,
                value=template,
                bg=theme["bg_primary"],
                fg=theme["text_primary"],
                font=self.fonts["small"],
                anchor='w'
            ).pack(anchor='w', pady=2)
        
        # Message area
        message_frame = tk.LabelFrame(
            dialog,
            text="✏️ Your Message",
            bg=theme["bg_primary"],
            fg=theme["text_primary"],
            font=self.fonts["body"]
        )
        message_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        message_text = tk.Text(
            message_frame,
            font=self.fonts["body"],
            bg=theme["bg_secondary"],
            fg=theme["text_primary"],
            relief='solid',
            bd=1,
            height=6,
            wrap='word'
        )
        message_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        def load_template():
            selected = template_var.get()
            if selected:
                message_text.delete('1.0', tk.END)
                message_text.insert('1.0', selected)
        
        tk.Button(
            templates_frame,
            text="📋 Load Selected Template",
            command=load_template,
            bg=theme["accent"],
            fg="white",
            font=self.fonts["small"],
            relief='flat',
            cursor='hand2'
        ).pack(pady=5)
        
        # Buttons
        btn_frame = tk.Frame(dialog, bg=theme["bg_primary"])
        btn_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        def send_message():
            message = message_text.get('1.0', tk.END).strip()
            if not message:
                self.show_toast("Please enter a message!", "warning")
                return
            
            clean_phone = self.clean_phone_number(appointment['phone_number'])
            if not clean_phone:
                self.show_toast("Invalid phone number!", "error")
                return
            
            whatsapp_url = f"https://wa.me/{clean_phone}?text={urllib.parse.quote(message)}"
            
            try:
                webbrowser.open(whatsapp_url)
                
                # Log manual message
                self.log_reminder_activity(
                    appointment['patient_name'], 
                    appointment['phone_number'],
                    "Manual WhatsApp message sent", 
                    "MANUAL ✅"
                )
                
                dialog.destroy()
                self.show_toast("WhatsApp opened! Message ready to send.", "success")
            except Exception as e:
                self.show_toast(f"Failed to open WhatsApp: {str(e)}", "error")
        
        tk.Button(
            btn_frame,
            text="📱 Open WhatsApp",
            command=send_message,
            bg=theme["success"],
            fg="white",
            font=self.fonts["heading"],
            relief='flat',
            padx=25,
            pady=10,
            cursor='hand2'
        ).pack(side='left', padx=(0, 10))
        
        tk.Button(
            btn_frame,
            text="❌ Cancel",
            command=dialog.destroy,
            bg=theme["danger"],
            fg="white",
            font=self.fonts["body"],
            relief='flat',
            padx=20,
            pady=10,
            cursor='hand2'
        ).pack(side='left')

    def refresh_appointments(self):
        """Refresh appointments display with WhatsApp status"""
        # Clear existing items
        for item in self.appointments_tree.get_children():
            self.appointments_tree.delete(item)
        
        # Add appointments
        for apt in self.appointments:
            # Truncate long text for display
            name = apt['patient_name'][:15] + "..." if len(apt['patient_name']) > 15 else apt['patient_name']
            procedure = apt['procedure'][:12] + "..." if len(apt['procedure']) > 12 else apt['procedure']
            notes = apt.get('notes', '')[:12] + "..." if len(apt.get('notes', '')) > 12 else apt.get('notes', '')
            
            # Create datetime display
            date_str = apt.get('appointment_date', 'N/A')
            time_str = apt.get('appointment_time', '09:00')
            datetime_str = f"{date_str} {time_str}"
            
            # WhatsApp status
            whatsapp_status = "📱ON" if apt.get('enable_reminders', True) else "📱OFF"
            
            self.appointments_tree.insert('', 'end', values=(
                apt['id'],
                name,
                procedure,
                apt['phone_number'],
                apt.get('email', ''),  # ADD EMAIL
                datetime_str,
                whatsapp_status,
                notes
            ))
        
        self.update_stats()

    def live_search(self, *args):
        """Perform live search as user types"""
        search_term = self.search_var.get().strip().lower()
        
        # Clear results
        for item in self.search_tree.get_children():
            self.search_tree.delete(item)
        
        if not search_term:
            return
        
        # Search and display results
        for apt in self.appointments:
            if (search_term in apt['patient_name'].lower() or 
                search_term in apt['phone_number'] or
                search_term in apt['procedure'].lower() or
                search_term in apt.get('notes', '').lower()):
                
                # Truncate for display
                name = apt['patient_name'][:15] + "..." if len(apt['patient_name']) > 15 else apt['patient_name']
                procedure = apt['procedure'][:12] + "..." if len(apt['procedure']) > 12 else apt['procedure']
                notes = apt.get('notes', '')[:12] + "..." if len(apt.get('notes', '')) > 12 else apt.get('notes', '')
                
                date_str = apt.get('appointment_date', 'N/A')
                time_str = apt.get('appointment_time', '09:00')
                datetime_str = f"{date_str} {time_str}"
                
                whatsapp_status = "📱ON" if apt.get('enable_reminders', True) else "📱OFF"
                
                self.search_tree.insert('', 'end', values=(
                    apt['id'],
                    name,
                    procedure,
                    apt['phone_number'],
                    datetime_str,
                    whatsapp_status,
                    notes
                ))

    def clear_search(self):
        """Clear search results"""
        self.search_var.set("")
        for item in self.search_tree.get_children():
            self.search_tree.delete(item)

    def edit_appointment(self):
        """Edit selected appointment"""
        selected = self.appointments_tree.selection()
        if not selected:
            self.show_toast("Please select an appointment to edit!", "warning")
            return
        
        item = self.appointments_tree.item(selected[0])
        apt_id = int(item['values'][0])
        
        # Find appointment
        appointment = next((apt for apt in self.appointments if apt['id'] == apt_id), None)
        if not appointment:
            self.show_toast("Appointment not found!", "error")
            return
        
        self.create_edit_dialog(appointment)

    def create_edit_dialog(self, appointment):
        """Create edit dialog with WhatsApp settings"""
        theme = self.get_theme()
        
        dialog = tk.Toplevel(self.root)
        dialog.title("✏️ Edit Appointment")
        dialog.geometry("450x650")
        dialog.configure(bg=theme["bg_primary"])
        dialog.grab_set()
        dialog.resizable(False, False)
        
        # Center the dialog
        dialog.transient(self.root)
        
        # Header
        header = tk.Frame(dialog, bg=theme["accent"], height=60)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text="✏️ Edit Patient Appointment",
            font=self.fonts["heading"],
            bg=theme["accent"],
            fg="white"
        ).pack(expand=True)
        
        # Form
        form_frame = tk.Frame(dialog, bg=theme["bg_primary"])
        form_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Edit variables
        edit_vars = {}
        
        # Form fields
        fields = [
            ("👤 Patient Name:", "name", appointment['patient_name']),
            ("🔬 Procedure:", "procedure", appointment['procedure']),
            ("📱 WhatsApp Phone:", "phone1", appointment['phone_number']),
            ("📋 Appointment Date:", "appointment_date", appointment.get('appointment_date', '')),
            ("⏰ Appointment Time:", "appointment_time", appointment.get('appointment_time', '09:00'))
        ]
        
        for i, (label, key, value) in enumerate(fields):
            tk.Label(
                form_frame,
                text=label,
                font=self.fonts["body"],
                bg=theme["bg_primary"],
                fg=theme["text_primary"],
                anchor='w'
            ).grid(row=i, column=0, sticky='w', pady=5)
            
            var = tk.StringVar(value=value)
            edit_vars[key] = var
            
            entry = tk.Entry(
                form_frame,
                textvariable=var,
                font=self.fonts["body"],
                bg=theme["bg_secondary"],
                fg=theme["text_primary"],
                relief='flat',
                bd=1
            )
            entry.grid(row=i, column=1, sticky='ew', pady=5, padx=(10, 0))
        
        # WhatsApp Auto-reminder checkbox
        whatsapp_frame = tk.LabelFrame(
            form_frame,
            text="📱 WhatsApp Auto-Reminders",
            bg=theme["bg_primary"],
            fg=theme["accent"],
            font=self.fonts["body"]
        )
        whatsapp_frame.grid(row=len(fields), column=0, columnspan=2, sticky='ew', pady=15)
        
        enable_reminders_var = tk.BooleanVar(value=appointment.get('enable_reminders', True))
        reminder_cb = tk.Checkbutton(
            whatsapp_frame,
            text="✅ Enable automatic WhatsApp reminders",
            variable=enable_reminders_var,
            bg=theme["bg_primary"],
            fg=theme["text_primary"],
            font=self.fonts["body"],
            anchor='w'
        )
        reminder_cb.pack(anchor='w', padx=10, pady=10)
        
        # Notes field
        tk.Label(
            form_frame,
            text="📝 Notes:",
            font=self.fonts["body"],
            bg=theme["bg_primary"],
            fg=theme["text_primary"],
            anchor='w'
        ).grid(row=len(fields)+1, column=0, sticky='nw', pady=5)
        
        notes_text = tk.Text(
            form_frame,
            font=self.fonts["body"],
            bg=theme["bg_secondary"],
            fg=theme["text_primary"],
            relief='flat',
            bd=1,
            height=4,
            wrap='word'
        )
        notes_text.grid(row=len(fields)+1, column=1, sticky='ew', pady=5, padx=(10, 0))
        notes_text.insert('1.0', appointment.get('notes', ''))
        
        form_frame.grid_columnconfigure(1, weight=1)
        
        # Buttons
        btn_frame = tk.Frame(dialog, bg=theme["bg_primary"])
        btn_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        def save_changes():
            # Validate phone number
            new_phone = edit_vars['phone1'].get().strip()
            if new_phone and not self.clean_phone_number(new_phone):
                self.show_toast("Please enter a valid WhatsApp phone number!", "error")
                return
            
            # Validate time
            new_time = edit_vars['appointment_time'].get().strip()
            if new_time and not self.validate_time(new_time):
                self.show_toast("Please enter a valid time (HH:MM format)!", "error")
                return
            
            # Update appointment
            old_reminder_status = appointment.get('enable_reminders', True)
            new_reminder_status = enable_reminders_var.get()
            
            appointment.update({
                'patient_name': edit_vars['name'].get().strip(),
                'procedure': edit_vars['procedure'].get().strip(),
                'phone_number': edit_vars['phone1'].get().strip(),
                'appointment_date': edit_vars['appointment_date'].get().strip(),
                'appointment_time': edit_vars['appointment_time'].get().strip(),
                'enable_reminders': new_reminder_status,
                'notes': notes_text.get('1.0', tk.END).strip(),
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            
            # Log WhatsApp reminder status change
            if old_reminder_status != new_reminder_status:
                status_text = "enabled" if new_reminder_status else "disabled"
                self.log_reminder_activity(
                    appointment['patient_name'], 
                    appointment['phone_number'],
                    f"WhatsApp auto-reminders {status_text}", 
                    "UPDATED ⚙️"
                )
            
            self.save_data()
            self.refresh_appointments()
            dialog.destroy()
            self.show_toast("Appointment updated successfully!", "success")
        
        tk.Button(
            btn_frame,
            text="💾 Save Changes",
            command=save_changes,
            bg=theme["success"],
            fg="white",
            font=self.fonts["body"],
            relief='flat',
            padx=20,
            pady=8,
            cursor='hand2'
        ).pack(side='left', padx=(0, 10))
        
        tk.Button(
            btn_frame,
            text="❌ Cancel",
            command=dialog.destroy,
            bg=theme["danger"],
            fg="white",
            font=self.fonts["body"],
            relief='flat',
            padx=20,
            pady=8,
            cursor='hand2'
        ).pack(side='left')

    def delete_appointment(self):
        """Delete selected appointment"""
        selected = self.appointments_tree.selection()
        if not selected:
            self.show_toast("Please select an appointment to delete!", "warning")
            return
        
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this appointment?"):
            item = self.appointments_tree.item(selected[0])
            apt_id = int(item['values'][0])
            
            # Find and log deleted appointment
            appointment = next((apt for apt in self.appointments if apt['id'] == apt_id), None)
            if appointment:
                self.log_reminder_activity(
                    appointment['patient_name'], 
                    appointment.get('phone_number', ''),
                    "Appointment deleted", 
                    "DELETED 🗑️"
                )
            
            self.appointments = [apt for apt in self.appointments if apt['id'] != apt_id]
            self.save_data()
            self.refresh_appointments()
            self.show_toast("Appointment deleted successfully!", "success")

    def update_stats(self):
        """Update statistics with WhatsApp data"""
        total = len(self.appointments)
        today = date.today()
        
        today_count = sum(1 for apt in self.appointments 
                         if apt.get('appointment_date') == today.strftime('%Y-%m-%d'))
        
        # Count WhatsApp messages sent
        whatsapp_sent = len(self.sent_reminders)
        
        # Update sidebar stats
        if hasattr(self, 'stats_labels'):
            self.stats_labels['total'].config(text=str(total))
            self.stats_labels['today'].config(text=str(today_count))
            self.stats_labels['whatsapp_sent'].config(text=str(whatsapp_sent))

    def update_dashboard(self):
        """Update dashboard statistics"""
        self.update_stats()
        
        # Update dashboard cards
        if hasattr(self, 'total_count_label'):
            self.total_count_label.config(text=str(len(self.appointments)))
        
        if hasattr(self, 'whatsapp_count_label'):
            self.whatsapp_count_label.config(text=str(len(self.sent_reminders)))
        
        # Count procedures
        procedure_counts = {}
        for apt in self.appointments:
            proc = apt['procedure'].split(':')[0]
            procedure_counts[proc] = procedure_counts.get(proc, 0) + 1
        
        # Update procedure list
        if hasattr(self, 'procedure_listbox'):
            self.procedure_listbox.delete(0, tk.END)
            for proc, count in sorted(procedure_counts.items(), key=lambda x: x[1], reverse=True):
                self.procedure_listbox.insert(tk.END, f"{proc}: {count} appointments")

    def refresh_all(self):
        """Refresh all data"""
        self.load_data()
        self.refresh_appointments()
        self.update_dashboard()
        if self.current_page == "reminders":
            self.refresh_reminder_log()
        self.show_toast("All data refreshed!", "success")

    def show_view_page(self):
        """Show view appointments page"""
        self.hide_all_pages()
        self.pages["view"].pack(fill='both', expand=True)
        self.refresh_appointments()

    def show_reports_page(self):
        """Show reports page"""
        self.hide_all_pages()
        self.pages["reports"].pack(fill='both', expand=True)
        self.update_reports()  # New method to refresh report data

    def show_dashboard_page(self):
        """Show dashboard page"""
        self.hide_all_pages()
        self.pages["dashboard"].pack(fill='both', expand=True)
        self.update_dashboard()

    def show_settings_page(self):
        """Show settings page"""
        self.hide_all_pages()
        self.pages["settings"].pack(fill='both', expand=True)

    def export_to_csv(self):
        """Export data to CSV with WhatsApp info"""
        if not self.appointments:
            self.show_toast("No appointments to export!", "warning")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = ['ID', 'Patient Name', 'Procedure', 'WhatsApp Phone', 
                                'Appointment Date', 'Appointment Time', 'Auto WhatsApp', 
                                'Notes', 'Created At']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    
                    writer.writeheader()
                    for apt in self.appointments:
                        writer.writerow({
                            'ID': apt['id'],
                            'Patient Name': apt['patient_name'],
                            'Procedure': apt['procedure'],
                            'WhatsApp Phone': apt['phone_number'],
                            'Appointment Date': apt.get('appointment_date', ''),
                            'Appointment Time': apt.get('appointment_time', '09:00'),
                            'Auto WhatsApp': 'Yes' if apt.get('enable_reminders', True) else 'No',
                            'Notes': apt.get('notes', ''),
                            'Created At': apt.get('created_at', '')
                        })
                
                self.show_toast("Data exported to CSV successfully!", "success")
            except Exception as e:
                self.show_toast(f"Export failed: {str(e)}", "error")

    def export_to_excel(self):
        """Export data to Excel with WhatsApp info"""
        if not PANDAS_AVAILABLE:
            self.show_toast("Excel export requires pandas and openpyxl", "error")
            return
        
        if not self.appointments:
            self.show_toast("No appointments to export!", "warning")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                data = []
                for apt in self.appointments:
                    data.append({
                        'ID': apt['id'],
                        'Patient Name': apt['patient_name'],
                        'Procedure': apt['procedure'],
                        'WhatsApp Phone': apt['phone_number'],
                        'Appointment Date': apt.get('appointment_date', ''),
                        'Appointment Time': apt.get('appointment_time', '09:00'),
                        'Auto WhatsApp': 'Yes' if apt.get('enable_reminders', True) else 'No',
                        'Notes': apt.get('notes', ''),
                        'Created At': apt.get('created_at', '')
                    })
                df = pd.DataFrame(data)
                with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='Appointments', index=False)
                self.show_toast("Data exported to Excel successfully!", "success")
            except Exception as e:
                self.show_toast(f"Export failed: {str(e)}", "error")

    def export_data(self):
        """Export data to JSON with WhatsApp info"""
        if not self.appointments:
            self.show_toast("No appointments to export!", "warning")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if filename:
            try:
                export_data = {
                    'appointments': self.appointments,
                    'whatsapp_reminder_settings': self.reminder_settings,
                    'sent_whatsapp_reminders': self.sent_reminders
                }
                with open(filename, 'w') as f:
                    json.dump(export_data, f, indent=2, default=str)
                self.show_toast("Data exported to JSON successfully!", "success")
            except Exception as e:
                self.show_toast(f"Export failed: {str(e)}", "error")

    def import_data(self):
        """Import data from JSON with WhatsApp info"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if filename:
            try:
                with open(filename, 'r') as f:
                    imported_data = json.load(f)

                if messagebox.askyesno("Confirm Import", "This will replace all current data. Continue?"):
                    # Handle different import formats
                    if isinstance(imported_data, list):
                        # Old format - just appointments
                        self.appointments = imported_data
                    else:
                        # New format - with WhatsApp data
                        self.appointments = imported_data.get('appointments', [])
                        if 'whatsapp_reminder_settings' in imported_data:
                            self.reminder_settings.update(imported_data['whatsapp_reminder_settings'])
                        if 'sent_whatsapp_reminders' in imported_data:
                            self.sent_reminders = imported_data['sent_whatsapp_reminders']
                    
                    self.save_data()
                    self.save_reminder_data()
                    self.refresh_all()
                    self.show_toast("Data imported successfully!", "success")
            except Exception as e:
                self.show_toast(f"Import failed: {str(e)}", "error")

    def save_data(self):
        """Save data to file"""
        try:
            with open('appointments.json', 'w') as f:
                json.dump(self.appointments, f, indent=2, default=str)
        except Exception as e:
            self.show_toast(f"Save failed: {str(e)}", "error")

    def load_data(self):
        """Load data from file"""
        try:
            if os.path.exists('appointments.json'):
                with open('appointments.json', 'r') as f:
                    self.appointments = json.load(f)
                self.update_stats()
        except Exception as e:
            self.show_toast(f"Load failed: {str(e)}", "error")

    def show_help(self):
        """Show help dialog with WhatsApp auto-reminder info"""
        help_text = """
🔥 MODERN CLINIC SYSTEM - AUTO WHATSAPP EDITION 🔥

KEYBOARD SHORTCUTS:
Ctrl+S  : Quick Save
Ctrl+N  : New Appointment
Ctrl+F  : Search
Ctrl+R  : Refresh All
Ctrl+W  : Auto-WhatsApp Page
F1      : Show Help

📱 AUTO WHATSAPP FEATURES:
• Automatic WhatsApp reminders: 3 days, 1 day, morning, 1 hour before
• Real browser automation opens WhatsApp Web/App
• Smart business hours checking (9AM-6PM default)
• Individual patient WhatsApp control
• Comprehensive activity logging with phone numbers
• Background operation with beautiful notifications

🚀 WHATSAPP FUNCTIONALITY:
• Select patient and click 📱 button for manual messages
• Choose from pre-made message templates
• Custom message editing with real-time preview
• Automatic phone number cleaning and formatting
• Opens WhatsApp Web or mobile app directly
• Auto-sends messages when WhatsApp Web loads

🌟 SYSTEM FEATURES:
• Auto-clear form after saving patient
• Ultra-compact design with dark/light themes
• Live search as you type
• Auto-save every 30 seconds with WhatsApp data
• Floating action buttons with WhatsApp controls
• Toast notifications for all WhatsApp activities
• Smart form validation with phone number checking
• Dashboard with WhatsApp statistics
• Export/Import with complete WhatsApp settings

🔧 WHATSAPP CONTROLS:
• Toggle auto-WhatsApp on/off from sidebar or FAB menu
• Configure reminder types in Auto WhatsApp page
• Set business hours for optimal sending times
• View complete WhatsApp activity log with phone numbers
• Test WhatsApp functionality with real sending
• Individual appointment WhatsApp settings
• Manual "Send Now" for all today's appointments
• Delay settings between messages

📋 WHATSAPP LOG TRACKING:
• Patient name and phone number logging
• Timestamp for all WhatsApp activities
• Success/failure status tracking
• Manual vs automatic message distinction
• Complete audit trail for clinic compliance

Made with ❤️ for modern clinic management!
Never miss an appointment with AUTO WHATSAPP! 📱✨
        """

        messagebox.showinfo("🚀 Auto WhatsApp Help Guide", help_text)

    def run(self):
        """Run the application"""
        self.show_toast("Welcome to Modern Clinic System - Auto WhatsApp Edition! 📱", "success")
        try:
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.root.mainloop()
        except Exception as e:
            print(f"Error running application: {e}")

    def on_closing(self):
        """Handle application closing"""
        try:
            # Stop reminder system
            self.stop_reminder_system()
            
            # Save all data
            self.save_data()
            self.save_reminder_data()
            self.save_reminder_settings()
            
            # Log system shutdown
            self.log_reminder_activity("System", "", "Auto WhatsApp system closing", "SHUTDOWN 🔌")
            
            self.root.destroy()
        except:
            self.root.destroy()

if __name__ == "__main__":
    try:
        app = ModernCompactClinicSystem()
        app.run()
    except Exception as e:
        print(f"Error starting application: {e}")
        messagebox.showerror("Startup Error", f"Failed to start application:\n{e}")
            
