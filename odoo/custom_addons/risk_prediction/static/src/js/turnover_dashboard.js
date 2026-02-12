/** @odoo-module **/
import {registry} from "@web/core/registry";
import {Component, onWillStart, useState} from "@odoo/owl";
import {useService} from "@web/core/utils/hooks";

export class TurnoverDashboard extends Component {

    setup() {
        this.rpc = useService("rpc");
        this.action = useService("action");


        this.state = useState({
            stats: null,
            employees: [],
            selectedRisk: null,
            loading: false,
        });

        // Chargement les donnes initial
        onWillStart(async () => {
            this.state.stats = await this.rpc("/hr/turnover/stats", {});
            // const res = await this.rpc("/hr/turnover/stats", {});
            // this.state.stats = res;
        });

    }

    // Clic sur une zone de risque => afficher les employés correspondants
    async openRisk(risk) {
        this.state.loading = true;
        this.state.selectedRisk = risk;

        const result = await this.rpc("/hr/turnover/employees", {
            risk: risk,
            limit: 20,
        });

        this.state.employees = result.employees;
        this.state.loading = false;
    }

    // Voir le profil d'un employé
    openEmployee(employeeId) {
        console.log("OPEN PROFILE FOR ID =", employeeId);
        this.action.doAction({
            type: "ir.actions.client",
            tag: "risk_prediction_employee_profile",
            context: {
                employee_id: employeeId,
            },
        });
    }


    openHistory(employeeId) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Historique IA",
            res_model: "historique.evaluation",
            // views: [[false, "tree"], [false, "form"]],
            views: [ [false, "form"]],
            domain: [["employee_id", "=", employeeId]],
            target: "current",
        });

    }


}

TurnoverDashboard.template = "risk_prediction.TurnoverDashboard";
//clé : "risk_prediction_turnover_dashboard" Nom interne (technical name) de ton action
//valeur : TurnoverDashboard : Le composant JS qui sera chargé quand Odoo exécutera cette action
registry.category("actions").add(
    "risk_prediction_turnover_dashboard",
    TurnoverDashboard
);
