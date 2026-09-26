# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class OhcWasteCollection(models.Model):
    _name = 'ohc.waste.collection'
    _description = 'Biomedical Waste Collection Log'
    _order = 'date_time desc'
    _rec_name = 'name'

    name = fields.Char(string='Receipt No', copy=False)
    ohc_id = fields.Many2one(
        'ohc.management', string='OHC', required=True,
        ondelete='cascade', index=True)
    date_time = fields.Datetime(
        string='Date & Time', required=True, default=fields.Datetime.now)

    # --- Bag counts (text on the form so they start genuinely blank; each
    # has a hidden numeric twin below purely so the list view can sum it) ---
    red_bags = fields.Char(string='Red Bags')
    white_bags = fields.Char(string='White Bags')
    black_bags = fields.Char(string='Black Bags')
    yellow_bags = fields.Char(string='Yellow Bags')
    blue_bags = fields.Char(string='Blue Bags')

    red_bags_num = fields.Integer(
        string='Red Bags', compute='_compute_bag_nums', store=True)
    white_bags_num = fields.Integer(
        string='White Bags', compute='_compute_bag_nums', store=True)
    black_bags_num = fields.Integer(
        string='Black Bags', compute='_compute_bag_nums', store=True)
    yellow_bags_num = fields.Integer(
        string='Yellow Bags', compute='_compute_bag_nums', store=True)
    blue_bags_num = fields.Integer(
        string='Blue Bags', compute='_compute_bag_nums', store=True)
    total_bags = fields.Integer(
        string='Total Bags', compute='_compute_bag_nums', store=True)

    # --- Bag weights (kg) — same text-field + numeric-twin pattern ---
    red_weight = fields.Char(string='Red Bags Weight (kg)')
    white_weight = fields.Char(string='White Bags Weight (kg)')
    black_weight = fields.Char(string='Black Bags Weight (kg)')
    yellow_weight = fields.Char(string='Yellow Bags Weight (kg)')
    blue_weight = fields.Char(string='Blue Bags Weight (kg)')

    red_weight_num = fields.Float(
        string='Red Weight (kg)', compute='_compute_bag_weights', store=True)
    white_weight_num = fields.Float(
        string='White Weight (kg)', compute='_compute_bag_weights', store=True)
    black_weight_num = fields.Float(
        string='Black Weight (kg)', compute='_compute_bag_weights', store=True)
    yellow_weight_num = fields.Float(
        string='Yellow Weight (kg)', compute='_compute_bag_weights', store=True)
    blue_weight_num = fields.Float(
        string='Blue Weight (kg)', compute='_compute_bag_weights', store=True)
    total_weight = fields.Float(
        string='Total Weight (kg)', compute='_compute_bag_weights', store=True)

    zero_bag_reason = fields.Char(string='Reason (if zero bags)')
    remarks = fields.Text(string='Remarks')

    receipt_copy = fields.Binary(string='Receipt Copy', attachment=True)
    receipt_copy_filename = fields.Char(string='Receipt Filename')

    supervisor = fields.Char(string='Supervisor')
    vehicle_number = fields.Char(string='Vehicle Number')
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company)

    _BAG_FIELDS = [
        ('red_bags', 'red_bags_num', 'Red Bags'),
        ('white_bags', 'white_bags_num', 'White Bags'),
        ('black_bags', 'black_bags_num', 'Black Bags'),
        ('yellow_bags', 'yellow_bags_num', 'Yellow Bags'),
        ('blue_bags', 'blue_bags_num', 'Blue Bags'),
    ]

    _WEIGHT_FIELDS = [
        ('red_weight', 'red_weight_num', 'Red Bags Weight'),
        ('white_weight', 'white_weight_num', 'White Bags Weight'),
        ('black_weight', 'black_weight_num', 'Black Bags Weight'),
        ('yellow_weight', 'yellow_weight_num', 'Yellow Bags Weight'),
        ('blue_weight', 'blue_weight_num', 'Blue Bags Weight'),
    ]

    @staticmethod
    def _to_int(value):
        value = (value or '').strip()
        return int(value) if value.isdigit() else 0

    @staticmethod
    def _to_float(value):
        value = (value or '').strip()
        try:
            f = float(value)
            return f if f >= 0 else 0.0
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _is_valid_count(value):
        """Non-negative whole number, as typed by a user (e.g. '0', '4')."""
        return value.isdigit()

    @staticmethod
    def _is_valid_weight(value):
        """Non-negative number, decimals allowed (e.g. '0', '2.5')."""
        try:
            return float(value) >= 0
        except (TypeError, ValueError):
            return False

    @api.depends('red_bags', 'white_bags', 'black_bags', 'yellow_bags', 'blue_bags')
    def _compute_bag_nums(self):
        for rec in self:
            total = 0
            for char_field, num_field, _label in rec._BAG_FIELDS:
                n = rec._to_int(getattr(rec, char_field))
                setattr(rec, num_field, n)
                total += n
            rec.total_bags = total

    @api.depends('red_weight', 'white_weight', 'black_weight', 'yellow_weight', 'blue_weight')
    def _compute_bag_weights(self):
        for rec in self:
            total = 0.0
            for char_field, num_field, _label in rec._WEIGHT_FIELDS:
                w = rec._to_float(getattr(rec, char_field))
                setattr(rec, num_field, w)
                total += w
            rec.total_weight = total

    @api.constrains(
        'red_bags', 'white_bags', 'black_bags', 'yellow_bags', 'blue_bags',
        'red_weight', 'white_weight', 'black_weight', 'yellow_weight', 'blue_weight',
    )
    def _check_bag_fields_filled(self):
        for rec in self:
            for fname, _num, label in rec._BAG_FIELDS:
                value = (getattr(rec, fname) or '').strip()
                if not value:
                    raise ValidationError(_(
                        "%s cannot be left blank — enter 0 if none were collected."
                    ) % label)
                if not rec._is_valid_count(value):
                    raise ValidationError(_(
                        "%s must be a whole number (0 or more)."
                    ) % label)
            for fname, _num, label in rec._WEIGHT_FIELDS:
                value = (getattr(rec, fname) or '').strip()
                if not value:
                    raise ValidationError(_(
                        "%s cannot be left blank — enter 0 if none were collected."
                    ) % label)
                if not rec._is_valid_weight(value):
                    raise ValidationError(_(
                        "%s must be a number (0 or more), e.g. 2.5."
                    ) % label)

    @api.constrains('total_bags', 'zero_bag_reason')
    def _check_zero_bag_reason(self):
        for rec in self:
            if rec.total_bags == 0 and not rec.zero_bag_reason:
                raise ValidationError(_(
                    'Please provide a reason when no bags were collected '
                    '(all bag counts are zero).'
                ))
