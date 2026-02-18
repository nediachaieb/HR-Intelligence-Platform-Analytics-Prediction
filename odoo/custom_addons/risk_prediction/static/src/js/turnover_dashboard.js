/** @odoo-module **/
import {registry} from "@web/core/registry";
import {Component, onMounted, onWillStart, useRef, useState} from "@odoo/owl";
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
            showModal: false,
            charts: null,
        });
        // REFS OWL 2
        this.donutRef = useRef("donutChart");
        this.barRef = useRef("barChart");
        this.lineRef = useRef("lineChart");

        // Charger données AVANT render
        onWillStart(async () => {
            this.state.stats = await this.rpc("/hr/turnover/stats", {});
            this.state.charts = await this.rpc("/hr/turnover/dashboard/charts", {});
        });
        // Render charts APRES mount DOM
        onMounted(async () => {

            if (!this.state.stats) {
                this.state.stats = await this.rpc("/hr/turnover/stats", {});
            }

            if (!this.state.charts) {
                this.state.charts = await this.rpc("/hr/turnover/dashboard/charts", {});
            }

            setTimeout(() => {
                if (this.donutRef.el) this.renderDonut();
                if (this.barRef.el) this.renderBarChart();
                if (this.lineRef.el) this.renderLineChart();
            }, 50);

        });

    }

    // Affichage du graphique en donut
    renderDonut() {
        const data = this.state.stats;

        const chart = new Chart(this.donutRef.el, {
            type: 'doughnut',
            data: {
                //labels: ['Low', 'Medium', 'High'],
                labels: ["Risque faible", "Risque moyen", "Risque élevé"],
                datasets: [{
                    data: [
                        data.percent.low,
                        data.percent.medium,
                        data.percent.high
                    ],
                    backgroundColor: [
                        '#28a745',
                        '#ffc107',
                        '#dc3545'
                    ],
                    hoverOffset: 10,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: 1200,
                    easing: 'easeOutQuart'
                },
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                },
                onHover: (event, elements) => {
                    event.native.target.style.cursor =
                        elements.length ? "pointer" : "default";
                },
                onClick: async (evt, elements) => {
                    if (elements.length > 0) {
                        const index = elements[0].index;
                        const riskMap = ['low', 'medium', 'high'];
                        const selectedRisk = riskMap[index];

                        await this.openRisk(selectedRisk);
                    }
                }
            }
        });
    }

    renderBarChart() {
        const ctx = this.barRef.el.getContext("2d");

        new Chart(ctx, {
            type: "bar",
            data: {
                labels: this.state.charts.bar.labels,
                datasets: [
                    {
                        label: "Risque élevé",
                        data: this.state.charts.bar.high,
                        backgroundColor: "#dc3545",
                    },
                    {
                        label: "Risque moyen",
                        data: this.state.charts.bar.medium,
                        backgroundColor: "#ffc107",
                    },
                    {
                        label: "Risque faible",
                        data: this.state.charts.bar.low,
                        backgroundColor: "#198754",
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: 1200,
                    easing: "easeOutBounce",
                },
                plugins: {
                    legend: {
                        position: "top",
                    },
                },
            },
        });
    }

    renderLineChart() {
        const ctx = this.lineRef.el.getContext("2d");

        new Chart(ctx, {
            type: "line",
            data: {
                labels: this.state.charts.line.labels,
                datasets: [
                    {
                        label: "Risque élevé",
                        data: this.state.charts.line.high,
                        borderColor: "#dc3545",
                        tension: 0.4,
                    },
                    {
                        label: "Risque moyen",
                        data: this.state.charts.line.medium,
                        borderColor: "#ffc107",
                        tension: 0.4,
                    },
                    {
                        label: "Risque faible",
                        data: this.state.charts.line.low,
                        borderColor: "#198754",
                        tension: 0.4,
                    }
                ]

            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: 1500,
                    easing: "easeInOutQuart",
                },
                layout: {
                padding: {
                    top: 20,
                    bottom: 20,
                    left: 10,
                    right: 10
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    suggestedMin: 0,   // ou une valeur basse si tes données montent haut
                    ticks: { padding: 10 }
                }
            }
            },
        });
    }


    // Clic sur une zone de risque => afficher les employés correspondants
    async openRisk(risk) {
        this.state.loading = true;
        this.state.showModal = true;
        this.state.selectedRisk = risk;

        const result = await this.rpc("/hr/turnover/employees", {
            risk: risk,
            limit: 20,
        });

        this.state.employees = result.employees;
        this.state.loading = false;
    }

    // Fermer la modal et réinitialiser les données
    closeModal() {
        this.state.showModal = false;
        this.state.selectedRisk = null;
        this.state.employees = [];
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
