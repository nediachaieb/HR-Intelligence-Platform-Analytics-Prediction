# -*- coding: utf-8 -*-

import logging
import requests
from collections import defaultdict
from datetime import date, datetime, timedelta

from dateutil.relativedelta import relativedelta
from odoo import models, fields, api
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    # ----------------------------------------------------------------
  # convertir le champ string to int
    progress_bar = fields.Integer(string="Risk", compute='_compute_progresse_bar', store=False)

    @api.depends('predicted_risk')
    def _compute_progresse_bar(self):
        for rec in self:
            if rec.predicted_risk == "low":
                rec.progress_bar = 30
            elif rec.predicted_risk == "medium":
                rec.progress_bar = 60
            elif rec.predicted_risk == "high":
                rec.progress_bar = 100
            else:
                rec.progress_bar = 0

    progress_html = fields.Html(
        compute="_compute_progress_html", sanitize=False, string="Progression du risque", readonly=True
    )

    @api.depends('predicted_risk', 'progress_bar')
    def _compute_progress_html(self):
        for record in self:
            color = {
                'high': 'bg-danger',
                'medium': 'bg-warning',
                'low': 'bg-success'
            }.get(record.predicted_risk, 'bg-secondary')

            value = record.progress_bar or 0
            record.progress_html = f"""
                      <div class="progress" style="height: 25px;">
                          <div class="progress-bar {color}" role="progressbar"
                               style="width: {value}%; min-width: 20px;">
                              {value:.0f}%
                          </div>
                      </div>
                  """

    # ------------------------------------------------------------------
    #
    age = fields.Integer(string="Age", compute='_compute_age', store=True)
    years_at_company = fields.Integer(string="Ancienneté", compute='_compute_years_at_company')
    company_size = fields.Integer(string="Taille de l'entreprise", compute='_compute_company_size')
    work_hours_week = fields.Float(string="Heures de travail par semaine", compute='_compute_work_hours_week')
    overTime = fields.Selection(
        [('yes', 'Oui'), ('no', 'Non')],
        string="Heures supplémentaires", compute='_compute_work_hours_week'
    )
    job_level = fields.Selection(
        [('entry', 'Débutant'), ('mid', 'Intermédiaire'), ('senior', 'Senior')],
        string="Niveau de poste", compute='_compute_job_level'
    )
    remote_work = fields.Selection(
        [('yes', 'Oui'), ('no', 'Non')],
        string="Remote", compute='_compute_remote_work'
    )
    contract_status = fields.Selection(
        [('new', 'Nouveau'), ('running', 'En cours'), ('expired', 'Expiré')],
        string="Statut du contrat", compute='_compute_contract_status', store=True
    )
    number_of_promotions = fields.Integer(string="Promotions", compute='_compute_number_of_promotions')
    monthly_income = fields.Float(string="Salaire mensuel", compute='_compute_monthly_income', store=True)

    # ------------------------------------------------------------------
    # Champs d’évaluation RH (mis à jour par le sondage)
    job_satisfaction = fields.Selection(
        [
            ('low', 'Faible'),
            ('medium', 'Moyen'),
            ('high', 'Élevé'),
            ('very_high', 'Très Élevé'),
        ],
        string="Satisfaction au travail",
        store=True,
    )
    work_life_balance = fields.Selection(
        [
            ('poor', 'Mauvais'), ('fair', 'Passable'), ('good', 'Bon'), ('excellent', 'Excellent')
        ],
        string="Équilibre vie pro / perso"
    )
    performance_rating = fields.Selection(
        [('low', 'Faible'), ('below_average', 'Sous la Moyenne'),
         ('average', 'Moyenne'), ('high', 'Élevé')],
        string="Évaluation de performance", default="average"
    )
    leadership_opportunities = fields.Selection(
        [('yes', 'Oui'), ('no', 'Non')],
        string="Opportunités de leadership"
    )
    innovation_opportunities = fields.Selection(
        [('yes', 'Oui'), ('no', 'Non')],
        string="Opportunités d'innovation"
    )
    company_reputation = fields.Selection(
        [('poor', 'Mauvaise'), ('fair', 'Correcte'), ('good', 'Bonne'), ('excellent', 'Excellente')],
        string="Réputation de l'entreprise"
    )
    employee_recognition = fields.Selection(
        [('low', 'Faible'), ('medium', 'Moyen'), ('high', 'Élevé'), ('very_high', 'Très Élevé')],
        string="Reconnaissance employé"
    )

    #  Risque prédit via FastAPI
    predicted_risk = fields.Selection(
        [('low', 'Faible'), ('medium', 'Moyen'), ('high', 'Élevé'), ('undefined', 'Non défini')],
        string="Risque prédit", readonly=True
    )
    prediction_reason = fields.Char(string="Raison de non-prédiction", readonly=True)

    historic_detaill = fields.One2many('historique.evaluation', 'employee_id', string='Historique', invisible="1")

    # ==================================================================
    @api.depends('birthday')
    def _compute_age(self):
        today = date.today()
        for rec in self:
            rec.age = today.year - rec.birthday.year if rec.birthday else 0

    # ------------------------------------------------------------------
    @api.depends('contract_id.date_start', 'contract_id.date_end')
    def _compute_years_at_company(self):
        today = date.today()
        for rec in self:
            start = rec.contract_id.date_start
            end = rec.contract_id.date_end or today
            rec.years_at_company = relativedelta(end, start).years if start else 0

    # ------------------------------------------------------------------
    @api.depends('company_id')
    def _compute_company_size(self):
        for rec in self:
            rec.company_size = self.env['hr.employee'].search_count([
                ('company_id', '=', rec.company_id.id)
            ]) if rec.company_id else 0

    # ------------------------------------------------------------------
    @api.depends('attendance_ids.check_in', 'attendance_ids.check_out')
    def _compute_work_hours_week(self):
        today = date.today()
        start_week = datetime.combine(today - timedelta(days=today.weekday()), datetime.min.time())
        end_week = start_week + timedelta(days=7)

        attendances = self.env['hr.attendance'].search([
            ('check_in', '>=', start_week),
            ('check_out', '<=', end_week),
            #('check_out', '!=', False),
        ])

        hrs = defaultdict(float)
        for att in attendances:
            hrs[att.employee_id.id] += (att.check_out - att.check_in).total_seconds() / 3600

        for rec in self:
            h = round(hrs.get(rec.id, 0.0), 2)
            rec.work_hours_week = h
            rec.overTime = 'yes' if h > 45.0 else 'no'

    # ------------------------------------------------------------------
    @api.depends('work_location_id')
    def _compute_remote_work(self):
        for rec in self:
            loc = (rec.work_location_id.name or '').lower()
            rec.remote_work = 'yes' if loc in ('home', 'remote') else 'no'

    # ------------------------------------------------------------------
    @api.depends('contract_id.date_start')
    def _compute_job_level(self):
        today = date.today()
        for rec in self:
            start = rec.contract_id.date_start
            yrs = (today - start).days // 365 if start else 0
            rec.job_level = 'entry' if yrs <= 2 else 'mid' if yrs <= 6 else 'senior'

    # ------------------------------------------------------------------
    @api.depends('contract_id.date_start', 'contract_id.date_end')
    def _compute_contract_status(self):
        today = date.today()
        for rec in self:
            start, end = rec.contract_id.date_start, rec.contract_id.date_end
            if start and start > today:
                rec.contract_status = 'new'
            elif start and (not end or end >= today):
                rec.contract_status = 'running'
            elif end and end < today:
                rec.contract_status = 'expired'

    # ------------------------------------------------------------------
    @api.depends('contract_ids')
    def _compute_number_of_promotions(self):
        for rec in self:
            jobs = [c.job_id.id for c in rec.contract_ids if c.job_id]
            rec.number_of_promotions = max(len(set(jobs)) - 1, 0)

    # ------------------------------------------------------------------
    @api.depends('contract_id.wage')
    def _compute_monthly_income(self):
        for rec in self:
            rec.monthly_income = rec.contract_id.wage if rec.contract_id else 0.0

    # ==================================================================
    #  Endpoint FastAPI
    # ------------------------------------------------------------------

    def predict_risk_for_employees(self):
        """
        Appelle le service FastAPI 'http://fastapirisk:8020/predict'
        et met à jour le champ predicted_risk.
        Règle: si A incomplet ou B incomplet -> pas d'appel API, predicted_risk='undefined' + prediction_reason.
        """
        url = "http://fastapirisk:8020/predict"
        valid_keys = [k for k, _ in self._fields['predicted_risk'].selection]

        for rec in self:
            # --- Groupe A : RH obligatoires ---
            missing_A = []
            job_role_val = (getattr(rec, 'job_id', False) and rec.job_id.name) or (
                        rec.department_id and rec.department_id.name)

            # Numériques/infos RH
            if not rec.age or rec.age <= 0: missing_A.append('age')
            if rec.years_at_company is None or rec.years_at_company < 0: missing_A.append('years_at_company')
            if rec.monthly_income is None or rec.monthly_income <= 0: missing_A.append('monthly_income')
            if getattr(rec, 'km_home_work', None) is None: missing_A.append('distance_from_home')  # 0 peut être valide
            if rec.number_of_promotions is None: missing_A.append('number_of_promotions')
            if rec.children is None: missing_A.append('number_of_dependents')

            # Catégorielles RH
            if not job_role_val: missing_A.append('job_role')
            if not rec.job_level: missing_A.append('job_level')
            if rec.company_size is None: missing_A.append('company_size')
            if not rec.certificate: missing_A.append('education_level')
            if not rec.marital: missing_A.append('marital_status')
            if rec.overTime not in ('yes', 'no'): missing_A.append('overtime')
            if rec.remote_work not in ('yes', 'no'): missing_A.append('remote_work')
            if not rec.gender: missing_A.append('gender')
            if not rec.performance_rating: missing_A.append('performance_rating')

            if missing_A:
                rec.predicted_risk = 'undefined'
                rec.prediction_reason = "RH incomplet : " + ", ".join(missing_A)
                self.env['historique.evaluation'].sudo().create({
                    'name': f"Évaluation IA - {fields.Datetime.now().strftime('%Y-%m-%d %H:%M')} | Motif: RH incomplet",
                    'date': fields.Datetime.now(),
                    'employee_id': rec.id,
                    'job_satis': rec.job_satisfaction,
                    'work_life': rec.work_life_balance,
                    'leadership_opport': rec.leadership_opportunities,
                    'innovation_opport': rec.innovation_opportunities,
                    'company_reput': rec.company_reputation,
                    'employee_recog': rec.employee_recognition,
                    'performance': rec.performance_rating,
                    'pred_risk': 'undefined',
                })
                continue  # pas d'appel API

            # --- Groupe B : Employé 6/6 requis ---
            missing_B = []
            for f in [
                'job_satisfaction', 'work_life_balance', 'employee_recognition',
                'leadership_opportunities', 'innovation_opportunities', 'company_reputation'
            ]:
                if not getattr(rec, f):
                    missing_B.append(f)

            if missing_B:
                rec.predicted_risk = 'undefined'
                rec.prediction_reason = "Sondage incomplet : " + ", ".join(missing_B)
                self.env['historique.evaluation'].sudo().create({
                    'name': f"Évaluation IA - {fields.Datetime.now().strftime('%Y-%m-%d %H:%M')} | Motif: Sondage incomplet",
                    'date': fields.Datetime.now(),
                    'employee_id': rec.id,
                    'job_satis': rec.job_satisfaction,
                    'work_life': rec.work_life_balance,
                    'leadership_opport': rec.leadership_opportunities,
                    'innovation_opport': rec.innovation_opportunities,
                    'company_reput': rec.company_reputation,
                    'employee_recog': rec.employee_recognition,
                    'performance': rec.performance_rating,
                    'pred_risk': 'undefined',
                })
                continue  # pas d'appel API

            # --- Payload strict : aucune valeur par défaut n'est injectée ---
            payload = {
                "age": int(rec.age),
                "years_at_company": int(rec.years_at_company),
                "job_role": job_role_val,
                "monthly_income": int(rec.monthly_income),
                "number_of_promotions": int(rec.number_of_promotions),  # 0 possible mais valeur réelle
                "distance_from_home": int(rec.km_home_work),  # 0 possible mais valeur réelle
                "number_of_dependents": int(rec.children),  # 0 possible mais valeur réelle
                "job_level": rec.job_level.capitalize(),
                "company_size": self._get_company_size_label(rec.company_size),
                "education_level": self._map_certificate_to_level(rec.certificate),
                "marital_status": rec.marital.capitalize(),
                "overtime": "Yes" if rec.overTime == "yes" else "No",
                "remote_work": "Yes" if rec.remote_work == "yes" else "No",
                "gender": self._label(rec.gender),

                # Ordinales (toutes présentes, pas de fallback)
                "performance_rating": self._label(rec.performance_rating),
                "leadership_opportunities": "Yes" if rec.leadership_opportunities == "yes" else "No",
                "innovation_opportunities": "Yes" if rec.innovation_opportunities == "yes" else "No",
                "company_reputation": self._label(rec.company_reputation),
                "employee_recognition": self._label(rec.employee_recognition),
                "work_life_balance": self._label(rec.work_life_balance),
                "job_satisfaction": self._label(rec.job_satisfaction),
            }

            # --- Appel API ---
            try:
                _logger.info("Payload sent to FastAPI for %s: %s", rec.name, payload)
                resp = requests.post(url, json=payload, timeout=30)
                if resp.status_code == 200:
                    raw = (resp.json().get("prediction", "undefined") or "undefined").lower()
                    risk = raw if raw in valid_keys else 'undefined'
                    if risk == 'undefined':
                        rec.prediction_reason = rec.prediction_reason or "Réponse API invalide"
                else:
                    risk = 'undefined'
                    rec.prediction_reason = f"Erreur API: HTTP {resp.status_code}"
            except Exception as e:
                _logger.error("API Error for %s: %s", rec.name, e)
                risk = 'undefined'
                rec.prediction_reason = f"Erreur API : {e}"

            # --- Mise à jour + Historisation ---
            rec.predicted_risk = risk
            if risk != 'undefined':
                rec.prediction_reason = False  # on efface la raison si tout est OK

            self.env['historique.evaluation'].sudo().create({
                'name': f"Évaluation IA - {fields.Datetime.now().strftime('%Y-%m-%d %H:%M')}",
                'date': fields.Datetime.now(),
                'employee_id': rec.id,
                'job_satis': rec.job_satisfaction,
                'work_life': rec.work_life_balance,
                'leadership_opport': rec.leadership_opportunities,
                'innovation_opport': rec.innovation_opportunities,
                'company_reput': rec.company_reputation,
                'employee_recog': rec.employee_recognition,
                'performance': rec.performance_rating,
                'pred_risk': risk,
            })

        return True

    # ==================================================================
    # mapping
    # ------------------------------------------------------------------
    def _map_certificate_to_level(self, cert):
        return {
            'graduate': "Associate Degree",
            'bachelor': "Bachelor’s Degree",
            'master': "Master’s Degree",
            'doctor': "PhD",
        }.get(cert.lower(), "High School") if cert else "High School"

    def _get_company_size_label(self, size):
        return "Small" if size <= 50 else "Moyen" if size <= 250 else "Large"

    def _label(self, value):
        """
        Convertit un code stocké (low/medium/high…) en label lisible par l’API.
        """
        return {
            "low": "Low", "medium": "Medium", "high": "High", "very_high": "Very High",
            "poor": "Poor", "fair": "Fair", "good": "Good", "excellent": "Excellent","average": "Average",
            "below_average": "Below Average", "yes": "Yes", "no": "No",
            "male": "Male", "female": "Female"
        }.get(value and value.lower())
