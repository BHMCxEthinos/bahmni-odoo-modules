# -*- coding: utf-8 -*-
from odoo import fields, models


class ServiaCalibrationLog(models.Model):
    _name = 'servia.calibration.log'
    _description = 'Equipment Calibration Log'
    _order = 'cal_date desc'

    name = fields.Char('Equipment / Instrument', required=True)
    cal_date = fields.Date('Calibration Date', default=fields.Date.context_today)
    calibrated_by = fields.Char('Calibrated By')
    cert_no = fields.Char('Certificate No')
    result = fields.Selection([
        ('pass', 'Pass'), ('fail', 'Fail'), ('adjusted', 'Adjusted'),
    ], string='Result', default='pass')
    next_due = fields.Date('Next Due')
    note = fields.Text('Notes')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
    ], default='draft')
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.user.company_id)

    def action_confirm(self):
        for rec in self:
            rec.write({'state': 'confirmed'})

    def action_reset(self):
        for rec in self:
            rec.write({'state': 'draft'})
