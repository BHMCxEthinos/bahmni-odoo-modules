from odoo import api, models,fields, _
from odoo.exceptions import UserError

class SaleShop(models.Model):
    _inherit = "sale.shop"

    @api.model
    def create_ohc_shop(self, ohc, warehouse):

        clinic_location = warehouse.lot_stock_id

        immediate_payment = self.env["account.payment.term"].search(
            [("name", "=", "Immediate Payment")],
            limit=1
        )

        shop = self.create({

            "name": ohc.name,

            "warehouse_id": warehouse.id,

            "location_id": clinic_location.id,

            "payment_default_id": immediate_payment.id if immediate_payment else False,

        })

        ohc.write({

            "shop_id": shop.id,

        })

        return shop

class OhcManagement(models.Model):
    _inherit = 'ohc.management'

    shop_id = fields.Many2one(
    'sale.shop',
    string='Shop',
    readonly=True
    )



class OrderTypeShopMapping(models.Model):
    _inherit = "order.type.shop.map"

    @api.model
    def create_ohc_mapping(self, ohc, shop, warehouse):

        clinic_location = warehouse.lot_stock_id

        order_types = self.env["order.type"].search([])

        if not order_types:
            raise UserError(_("No Order Types found."))

        mappings = self.env["order.type.shop.map"]

        for order_type in order_types:

            existing = self.search([
                ("order_type", "=", order_type.id),
                ("shop_id", "=", shop.id),
                ("location_id", "=", clinic_location.id),
            ], limit=1)

            if existing:
                mappings |= existing
                continue

            mapping = self.create({
                "order_type": order_type.id,
                "shop_id": shop.id,
                "location_id": clinic_location.id,
                "location_name": ohc.name,
            })

            mappings |= mapping

        return mappings