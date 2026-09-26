from odoo import api, fields, models


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    calibration_ids = fields.One2many(
        'servia.calibration.log', 'equipment_id', string='Calibration Records')

    # Stored + computed so it can be added as a plain column to any tree
    # view (Equipments list, OHC Equipment tab, etc.) and used in
    # sort/group/filter without extra joins.
    next_calibration_date = fields.Date(
        string='Next Calibration Date',
        compute='_compute_next_calibration_date',
        store=True,
    )

    @api.depends('calibration_ids.next_due', 'calibration_ids.cal_date', 'calibration_ids.state')
    def _compute_next_calibration_date(self):
        for equipment in self:
            confirmed_logs = equipment.calibration_ids.filtered(lambda l: l.state == 'confirmed')
            latest_log = confirmed_logs.sorted('cal_date', reverse=True)[:1]
            equipment.next_calibration_date = latest_log.next_due if latest_log else False

    def action_view_calibrations(self):
        self.ensure_one()
        existing = self.env['servia.calibration.log'].search(
            [('equipment_id', '=', self.id)], limit=1)
        action = {
            'name': 'Calibration Records',
            'type': 'ir.actions.act_window',
            'res_model': 'servia.calibration.log',
            'domain': [('equipment_id', '=', self.id)],
            'context': {'default_equipment_id': self.id},
        }
        if existing:
            action['view_mode'] = 'tree,form'
        else:
            action['view_mode'] = 'form'
            action['target'] = 'current'
        return action