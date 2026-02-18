
from odoo import models, fields

class HistoricEvaluation(models.Model):
    _name = 'historique.evaluation'
    _description = 'Evaluation History'

    name = fields.Char(string="Référence")
    date = fields.Datetime(string="Date", readonly=True)
    job_satis = fields.Selection(
        [
            ('low', 'Faible'),
            ('medium', 'Moyen'),
            ('high', 'Élevé'),
            ('very_high', 'Très Élevé'),
        ],
        string="Satisfaction au travail",
        store=True,
    )
    work_life = fields.Selection(
        [
            ('poor', 'Mauvais'), ('fair', 'Passable'), ('good', 'Bon'), ('excellent', 'Excellent')
        ],
        string="Équilibre vie pro / perso"
    )
    performance = fields.Selection(
        [('low', 'Faible'), ('below_average', 'Sous la Moyenne'),
         ('average', 'Moyenne'), ('high', 'Élevé')],
        string="Évaluation de performance"
    )
    leadership_opport = fields.Selection(
        [('yes', 'Oui'), ('no', 'Non')],
        string="Opportunités de leadership"
    )
    innovation_opport = fields.Selection(
        [('yes', 'Oui'), ('no', 'Non')],
        string="Opportunités d'innovation"
    )
    company_reput = fields.Selection(
        [('poor', 'Mauvaise'), ('fair', 'Correcte'), ('good', 'Bonne'), ('excellent', 'Excellente')],
        string="Réputation de l'entreprise"
    )
    employee_recog = fields.Selection(
        [('low', 'Faible'), ('medium', 'Moyen'), ('high', 'Élevé'), ('very_high', 'Très Élevé')],
        string="Reconnaissance employé"
    )

    #  Risque prédit via FastAPI
    pred_risk = fields.Selection(
        [('low', 'Faible'), ('medium', 'Moyen'), ('high', 'Élevé'), ('undefined', 'Non défini')],
        string="Risque prédit", readonly=True
    )
    employee_id = fields.Many2one('hr.employee', string="Employee")

