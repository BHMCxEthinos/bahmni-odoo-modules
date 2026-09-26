# -*- coding: utf-8 -*-
from odoo import fields, models


class OhcManagement(models.Model):
    _inherit = 'ohc.management'

    waste_collection_ids = fields.One2many(
        'ohc.waste.collection', 'ohc_id', string='Waste Collections')
    waste_collection_count = fields.Integer(
        compute='_compute_waste_collection_stats')
    last_waste_pickup_datetime = fields.Datetime(
        compute='_compute_waste_collection_stats')

    def _compute_waste_collection_stats(self):
        for rec in self:
            collections = rec.waste_collection_ids
            rec.waste_collection_count = len(collections)
            rec.last_waste_pickup_datetime = (
                max(collections.mapped('date_time')) if collections else False
            )

    def action_view_waste_collections(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Waste Collection',
            'res_model': 'ohc.waste.collection',
            'view_mode': 'tree,form',
            'domain': [('ohc_id', '=', self.id)],
            'context': {
                'default_ohc_id': self.id,
                'search_default_this_week': 1,
            },
        }
