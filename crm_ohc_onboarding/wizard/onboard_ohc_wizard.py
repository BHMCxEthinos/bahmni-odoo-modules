from odoo import api, fields, models, _
from odoo.exceptions import UserError,ValidationError


class OnboardOhcWizard(models.TransientModel):
    _name = "onboard.ohc.wizard"
    _description = "OHC Onboarding Wizard"

    lead_id = fields.Many2one(
        'crm.lead',
        required=True
    )

    ohc_name = fields.Char(
        string="Project / OHC Name",
        required=True
    )

    # customer_id = fields.Many2one(
    #     'res.partner',
    #     string="Customer",
       
    # )

    operation_manager = fields.Many2one(
        'hr.employee',
        string="Operation Manager"
    )

  
    customer_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        domain=[('is_company', '=', True)]
        )

    email = fields.Char()

    mobile = fields.Char()

    project_manager = fields.Many2one(
        'res.users',
        string="Project Manager",
        default=lambda self: self.env.user
    )

    def action_create(self):

        self.ensure_one()

        lead = self.lead_id

        # if lead.new_ohc:
        #     raise UserError(_("Already onboarded."))
        existing_ohc = self.env['ohc.management'].search([
                ('name', '=ilike', self.ohc_name.strip()),
            ], limit=1)
        
        if existing_ohc:
                    raise ValidationError(_(
                        "OHC Name '%s' is already existing. "
                        "Please enter a different OHC Name."
                    ) % self.ohc_name)
     

        ohc = self.env['ohc.management'].create({
        'name': self.ohc_name,
        'company_id': self.customer_id.id,  
        'operation_manager': self.operation_manager.id,
        'email': self.email,
        'mobile': self.mobile,
        })

     

        # project = self.env['project.project'].create({

        #     'name': self.ohc_name,

        #     'partner_id': self.customer_id.id,

        #     'ohc_id': ohc.id,

        # })
        template = self.env['project.task.template'].browse(1)

        if not template.exists():
            raise UserError(_(
                "New OHC onboarding template was not found."
            ))

       

        # ---------------------------------------------------------
        # 3. CREATE PROJECT
        # ---------------------------------------------------------
        project = self.env['project.project'].create({
            'name': self.ohc_name,
            'partner_id': self.customer_id.id,
            'ohc_id': ohc.id,
            'user_id': self.project_manager.id,
            'project_template_id': template.id,
        })

        # ---------------------------------------------------------
        # 4. CALL THE SAME METHOD AS
        #    CREATE PROJECT FROM TEMPLATE
        # ---------------------------------------------------------
        project.action_create_project_from_template()


       

        project.write({
            'is_favorite': False,
        })

     
        
        

        warehouse = self.env["stock.warehouse"].create_ohc_warehouse(ohc)
        shop = self.env["sale.shop"].create_ohc_shop(
            ohc,
            warehouse
        )

        self.env["order.type.shop.map"].create_ohc_mapping(
            ohc,
            shop,
            warehouse,
        )

       

        ohc.sync_openmrs_location()

       

        lead.write({

            'ohc_id': ohc.id,

            'project_id': project.id,
            

        })

        return {
            'type': 'ir.actions.act_window_close'
        }