from odoo import http
from odoo.http import request
from odoo.exceptions import AccessError

class EmployeeProfileController(http.Controller):

    @http.route("/hr/turnover/employee/profile", type="json", auth="user")
    def employee_profile(self, employee_id=None):
        user = request.env.user

        # Sécurité RH
        if not user.has_group("risk_prediction.group_rh_risk"):
            raise AccessError("Access denied")
        emp = request.env["hr.employee"].sudo().browse(employee_id)
        if not emp.exists():
            return {"error": "Employee not found"}

        return {
            "id": emp.id,
            "name": emp.name,
            "department": emp.department_id.name or "",
            "job_title": emp.job_title or "",
            "gender": emp.gender or "",
            "birthday": emp.birthday or "",
            "age": emp.age or 0,

            # Position
            "job_level": emp.job_level or "",
            "years_at_company": emp.years_at_company or 0,
            "remote_work": "Yes" if emp.remote_work else "No",

            # Contract
            "contract_status": emp.contract_status or "",
            "monthly_income": emp.monthly_income or 0.0,
            "number_of_promotions": emp.number_of_promotions or 0,
        }
