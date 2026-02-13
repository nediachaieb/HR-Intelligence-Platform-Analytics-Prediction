{
    'name': 'Risk Prediction',
    'version': '17.0.1.0.0',
    'summary': 'Predict employee risk and satisfaction based on Surveys',
    'category': 'Human Resources',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'hr',
        'survey', 'hr_attendance', 'hr_contract',
    ],
    'data': [
        'security/groups.xml',
        'security/record_rules.xml',
        'security/ir.model.access.csv',
        'data/ir_actions_server.xml',
        'data/hr_demo_employees.xml',
        'data/survey_question_category_data.xml',
        'data/employee_satisfaction_survey.xml',
        'views/hr_employee_views.xml',
        'views/survey_question_views.xml',
        'views/turnover_dashboard_view.xml',
        #'views/assets.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'risk_prediction/static/src/js/turnover_dashboard.js',
            'risk_prediction/static/src/xml/turnover_dashboard.xml',
            "risk_prediction/static/src/js/employee_profile_dashboard.js",
            "risk_prediction/static/src/xml/employee_profile_dashboard.xml",
            "risk_prediction/static/lib/chart.min.js"
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
