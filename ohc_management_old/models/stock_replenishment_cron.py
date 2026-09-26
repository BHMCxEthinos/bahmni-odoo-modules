from odoo import models, api
import datetime


class StockReplenishmentCron(models.AbstractModel):
    _name = 'ohc.stock.replenishment.cron'
    _description = 'OHC Stock Replenishment Alert Cron'

    @api.model
    def run_stock_replenishment_alert(self):
        env = self.env
        today_start = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
        default_email = env['ir.config_parameter'].sudo().get_param(
            'inventory_alert.recipient_email', 'salvikishori96@gmail.com'
        )
        orderpoints = env['stock.warehouse.orderpoint'].search([])

        for op in orderpoints:
            product = op.product_id
            warehouse = op.warehouse_id
            forecast_qty = product.with_context(warehouse=warehouse.id).virtual_available

            if forecast_qty <= op.product_min_qty:
                subject = 'Stock Replenishment Alert: %s' % product.display_name

                already_sent = env['mail.mail'].search([
                    ('subject', '=', subject),
                    ('create_date', '>=', today_start),
                ], limit=1)
                if already_sent:
                    continue

                recipient_emails = []

                ohc_record = env['ohc.management'].search([
                    ('warehouse_id', '=', warehouse.id)
                ], limit=1)

                if ohc_record:
                    manager = ohc_record.operation_manager
                    if manager and manager.work_email:
                        recipient_emails.append(manager.work_email)

                    nurses = ohc_record.employee_ids.filtered(
                        lambda e: e.employee_status == 'active'
                        and e.job_id
                        and e.job_id.name.strip().lower() == 'nurse'
                    )
                    for nurse in nurses:
                        if nurse.work_email:
                            recipient_emails.append(nurse.work_email)

                if not recipient_emails:
                    recipient_emails = [default_email]

                body = """
                    <p>Dear Team,</p>
                    <p>Stock for <b>%s</b> at warehouse <b>%s</b> has reached or fallen below the minimum level.</p>
                    <ul>
                        <li>Forecasted Quantity: %s</li>
                        <li>Minimum Quantity: %s</li>
                        <li>Maximum Quantity: %s</li>
                    </ul>
                    <p>Please initiate replenishment.</p>
                """ % (product.display_name, warehouse.name, forecast_qty, op.product_min_qty, op.product_max_qty)

                env['mail.mail'].sudo().create({
                    'subject': subject,
                    'body_html': body,
                    'email_to': ','.join(recipient_emails),
                }).send()