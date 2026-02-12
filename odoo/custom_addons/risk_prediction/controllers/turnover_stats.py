# -*- coding: utf-8 -*-

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
                # "risk_label": {
                #     "low": "Risque faible",
                #     "medium": "Risque moyen",
                #     "high": "Risque élevé",
                #     "undefined": "Non évalué"
                # }.get(emp.predicted_risk),
                # "status_label": (
                #     "Non évalué"
                #     if emp.predicted_risk == 'undefined'
                #     else None
                # )
            })

        total = Employee.search_count(domain)

        return {
            "risk": risk,
            "total": total,
            "count": len(data),
            "employees": data
        }
