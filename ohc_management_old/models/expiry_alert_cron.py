from odoo import models, api
import datetime


class ExpiryAlertCron(models.AbstractModel):
    _name = 'ohc.expiry.alert.cron'
    _description = 'OHC Product Expiry Alert Cron'

    @api.model
    def run_expiry_alert(self):
        env = self.env
        now = datetime.datetime.now()
        today_start = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
        default_email = env['ir.config_parameter'].sudo().get_param(
            'inventory_alert.recipient_email', 'salvikishori96@gmail.com'
        )

        lots = env['stock.lot'].search([
            ('alert_date', '!=', False),
            ('alert_date', '<=', now),
        ])

        for lot in lots:
            if lot.product_qty <= 0:
                continue

            subject = 'Expiry Alert: %s (Lot: %s)' % (lot.product_id.display_name, lot.name)

            already_sent = env['mail.mail'].search([
                ('subject', '=', subject),
                ('create_date', '>=', today_start),
            ], limit=1)
            if already_sent:
                continue

            recipient_emails = []

            quants = env['stock.quant'].search([
                ('lot_id', '=', lot.id),
                ('quantity', '>', 0),
            ], limit=1)

            if quants:
                warehouse = quants[0].location_id.warehouse_id
                if warehouse:
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
                <p>The following item is nearing or has reached its expiry:</p>
                <ul>
                    <li>Product: %s</li>
                    <li>Lot/Serial: %s</li>
                    <li>Expiration Date: %s</li>
                    <li>Alert Date: %s</li>
                    <li>Quantity on Hand: %s</li>
                </ul>
                <p>Please take necessary action.</p>
            """ % (lot.product_id.display_name, lot.name, lot.expiration_date, lot.alert_date, lot.product_qty)

            env['mail.mail'].sudo().create({
                'subject': subject,
                'body_html': body,
                'email_to': ','.join(recipient_emails),
            }).send()