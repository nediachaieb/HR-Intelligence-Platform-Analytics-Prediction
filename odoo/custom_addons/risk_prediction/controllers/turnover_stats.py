# -*- coding: utf-8 -*-
from collections import defaultdict
from datetime import datetime

from dateutil.relativedelta import relativedelta
from odoo import http
from odoo.http import request


class TurnoverStatsController(http.Controller):
    # =====================================================
    # ÉTAPE 1 — Statistiques globales (dashboard niveau 1)
    # =====================================================
    @http.route('/hr/turnover/stats', type='json', auth='user')
    def turnover_stats(self):
        user = request.env.user

        # Sécurité RH
        if not user.has_group('risk_prediction.group_rh_risk'):
            return {"error": "Access denied"}

        Employee = request.env['hr.employee'].sudo()

        total = Employee.search_count([])
        low = Employee.search_count([('predicted_risk', '=', 'low')])
        medium = Employee.search_count([('predicted_risk', '=', 'medium')])
        high = Employee.search_count([('predicted_risk', '=', 'high')])
        undefined = Employee.search_count([('predicted_risk', '=', 'undefined')])

        evaluated = low + medium + high

        def pct(x):
            return round((x / evaluated) * 100, 2) if evaluated else 0.0

        return {
            "total": total,
            "evaluated": evaluated,
            "undefined": undefined,
            "low": low,
            "medium": medium,
            "high": high,
            "percent": {
                "low": pct(low),
                "medium": pct(medium),
                "high": pct(high),
            }
        }


class TurnoverDrilldownController(http.Controller):
    # =====================================================
    # ÉTAPE 2 — Détail des employés par niveau de risque
    # =====================================================
    @http.route('/hr/turnover/employees', type='json', auth='user')
    def turnover_employees(self, risk=None, limit=20, offset=0):

        # Sécurité RH
        if not request.env.user.has_group('risk_prediction.group_rh_risk'):
            return {"error": "Access denied"}

        Employee = request.env['hr.employee'].sudo()
        Evaluation = request.env['historique.evaluation'].sudo()

        domain = [('predicted_risk', '=', risk)]

        employees = Employee.search(
            domain,
            limit=limit,
            offset=offset,
            order="write_date desc"
        )

        data = []
        for emp in employees:
            last_eval = Evaluation.search(
                [('employee_id', '=', emp.id)],
                order='date desc',
                limit=1
            )

            data.append({
                "id": emp.id,
                "name": emp.name,
                "department": emp.department_id.name if emp.department_id else "",
                "job_title": emp.job_title or "",
                "last_evaluation": last_eval.date if last_eval else None,
                "predicted_risk": emp.predicted_risk,
            })

        total = Employee.search_count(domain)

        return {
            "risk": risk,
            "total": total,
            "count": len(data),
            "employees": data
        }


class TurnoverDashboardChartsController(http.Controller):

    @http.route("/hr/turnover/dashboard/charts", type="json", auth="user")
    def dashboard_charts(self):
        if not request.env.user.has_group("risk_prediction.group_rh_risk"):
            return {"error": "Access denied"}

        Employee = request.env["hr.employee"].sudo()
        Evaluation = request.env["historique.evaluation"].sudo()

        employees = Employee.search([])

        # ================================
        # 1️⃣ BAR CHART — Par département
        # ================================

        dept_risk = defaultdict(lambda: {
            "high": 0,
            "medium": 0,
            "low": 0
        })

        for emp in employees:
            dept = emp.department_id.name if emp.department_id else "Non défini"
            risk = emp.predicted_risk or "undefined"

            if risk in ["high", "medium", "low"]:
                dept_risk[dept][risk] += 1

        bar_data = {
            "labels": list(dept_risk.keys()),
            "high": [v["high"] for v in dept_risk.values()],
            "medium": [v["medium"] for v in dept_risk.values()],
            "low": [v["low"] for v in dept_risk.values()],
        }

        # ====================================
        # 2️⃣ LINE CHART — Évolution temporelle
        # ====================================

        today = datetime.today()

        months = []
        high_values = []
        medium_values = []
        low_values = []

        for i in range(12, -1, -1):
            start_date = (today - relativedelta(months=i)).replace(day=1)
            end_date = start_date + relativedelta(months=1)

            months.append(start_date.strftime("%b %Y"))

            high_count = Evaluation.search_count([
                ("date", ">=", start_date),
                ("date", "<", end_date),
                ("pred_risk", "=", "high"),
            ])

            medium_count = Evaluation.search_count([
                ("date", ">=", start_date),
                ("date", "<", end_date),
                ("pred_risk", "=", "medium"),
            ])

            low_count = Evaluation.search_count([
                ("date", ">=", start_date),
                ("date", "<", end_date),
                ("pred_risk", "=", "low"),
            ])

            high_values.append(high_count)
            medium_values.append(medium_count)
            low_values.append(low_count)

        line_data = {
            "labels": months,
            "high": high_values,
            "medium": medium_values,
            "low": low_values,
        }

        return {
            "bar": bar_data,
            "line": line_data,
        }
