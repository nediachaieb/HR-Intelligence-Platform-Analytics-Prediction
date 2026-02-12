/** @odoo-module **/
import { Component, onWillStart, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";

export class EmployeeProfileDashboard extends Component {

    setup() {
        this.rpc = useService("rpc");
        this.actionService = useService("action");

        this.state = useState({
            loading: true,
            employee: null,
            error: null,
        });
// Chargement du profil de l'employé
        onWillStart(async () => {
            console.log("PROPS ACTION =", this.props.action);

            const employeeId = this.props.action?.context?.employee_id;

            if (!employeeId) {
                this.state.error = "Employee ID manquant.";
                this.state.loading = false;
                return;
            }

            try {
                const res = await this.rpc("/hr/turnover/employee/profile", {
                    employee_id: employeeId,
                });

                this.state.employee = res;

            } catch (e) {
                this.state.error = "Erreur lors du chargement du profil.";
            } finally {
                this.state.loading = false;
            }
        });
    }

    backToDashboard() {
        this.actionService.doAction("risk_prediction.action_turnover_dashboard");
    }
}

EmployeeProfileDashboard.template = "risk_prediction.EmployeeProfileDashboard";

registry.category("actions").add(
    "risk_prediction_employee_profile",
    EmployeeProfileDashboard
);
