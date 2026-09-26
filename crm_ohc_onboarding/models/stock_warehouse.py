from odoo import api, models


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    @api.model
    def create_ohc_warehouse(self, ohc):

        warehouse = self.create({
            "name": ohc.name,
            "code": ohc.ohc_id,
            "company_id": self.env.company.id,
        })

        # Link warehouse to OHC
        ohc.write({
            "warehouse_id": warehouse.id,
        })

       

        clinic_location = warehouse.lot_stock_id

        clinic_location.write({
            "name": "Clinic",
        })

       

        self.env["stock.location"].create({
            "name": "Ambulance",
            "location_id": warehouse.view_location_id.id,
            "usage": "internal",
        })

        warehouse.write({
            "lot_stock_id": clinic_location.id,
        })

        return warehouse