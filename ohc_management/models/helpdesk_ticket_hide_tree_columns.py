from odoo import models
from lxml import etree


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    def get_view(self, view_id=None, view_type='form', **options):
        result = super().get_view(view_id=view_id, view_type=view_type, **options)
        if view_type == 'tree':
            fields_to_remove = ['rating', 'feedback', 'feedback_date']
            doc = etree.XML(result['arch'])
            for field_name in fields_to_remove:
                for node in doc.xpath("//field[@name='%s']" % field_name):
                    node.getparent().remove(node)
            result['arch'] = etree.tostring(doc, encoding='unicode')
        return result