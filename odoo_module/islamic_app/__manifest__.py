{
    'name': 'Islamic Application Backend',
    'version': '19.0.1.0.0',
    'category': 'Services',
    'summary': 'Backend for Islamic Mobile Application with Quran, Adhkar, Audio & AI',
    'description': """
        Comprehensive Islamic Application Backend Module for Odoo 19
        =============================================================
        
        Features:
        - Quran content management with multi-language translations (EN, AR, FR, TR, HI)
        - Adhkar (supplications) with categories and counting
        - Audio management for recitations and spiritual content
        - AI-powered search and recommendations
        - User management with role-based access (Regular, Admin, Special)
        - Subscription and billing management
        - Push notification system (Prayer times, Dhikr reminders, Family ties)
        - Family ties (Silat al-Rahim) tracking
        - Dhikr counter and progress tracking
        - JWT-based REST API for React Native mobile app
        - RTL support for Arabic language
        - Virtual avatar content management
    """,
    'author': 'Islamic App Development Team',
    'website': 'https://islamicapp.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'web',
    ],
    'data': [
        # Security
        'security/islamic_app_groups.xml',
        'security/ir.model.access.csv',
        'security/islamic_app_rules.xml',
        
        # Data
        'data/islamic_app_language_data.xml',
        'data/islamic_app_adhkar_category_data.xml',
        'data/islamic_app_adhkar_data.xml',
        'data/islamic_app_subscription_plan_data.xml',
        'data/islamic_app_notification_type_data.xml',
        'data/islamic_app_quran_data.xml',
        'data/islamic_app_cron_data.xml',
        
        # Views
        'views/islamic_content_views.xml',
        'views/islamic_audio_views.xml',
        'views/islamic_user_views.xml',
        'views/islamic_subscription_views.xml',
        'views/islamic_adhkar_views.xml',
        'views/islamic_notification_views.xml',
        'views/islamic_ai_views.xml',
        'views/islamic_family_views.xml',
        'views/islamic_dhikr_views.xml',
        'views/islamic_app_menus.xml',
    ],
    'assets': {},
    'installable': True,
    'application': True,
    'auto_install': False,
}
