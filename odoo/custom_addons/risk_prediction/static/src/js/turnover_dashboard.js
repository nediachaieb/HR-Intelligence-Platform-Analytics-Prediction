/** @odoo-module **/
import {registry} from "@web/core/registry";
import {Component, onMounted, onWillStart, useRef, useState} from "@odoo/owl";
import {useService} from "@web/core/utils/hooks";

export class TurnoverDashboard extends Component {

    setup() {
        this.rpc = useService("rpc");
        this.action = useService("action");
        this.chartRef = useRef("riskChart");
        this.chart = null;


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

        onMounted(() => {
            if (this.state.stats) {
                this.renderChart();
            }
        });

    }

    renderChart() {

        const ctx = document.getElementById("turnoverChart");

        if (!ctx || !this.state.stats) return;

        if (this.chartInstance) {
            this.chartInstance.destroy();
        }

        this.chartInstance = new Chart(ctx, {
            type: "doughnut",
            data: {
                labels: ["Risque faible", "Risque moyen", "Risque élevé"],
                datasets: [{
                    data: [
                        this.state.stats.percent.low,
                        this.state.stats.percent.medium,
                        this.state.stats.percent.high
                    ],
                    backgroundColor: [
                        "#28a745",
                        "#ffc107",
                        "#dc3545"
                    ],
                    borderWidth: 2,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: "65%",
                plugins: {
                    legend: {
                        position: "bottom",
                        labels: {
                            padding: 20,
                            font: {size: 14}
                        }
                    }
                },
                animation: {
                    animateScale: true
                },

                onClick: (event, elements) => {

                if (!elements.length) return;

                const index = elements[0].index;

                const riskMap = ["low", "medium", "high"];
                const selectedRisk = riskMap[index];

                this.openRisk(selectedRisk);

            }

            }
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
            views: [[false, "tree"], [false, "form"]],
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
