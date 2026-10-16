# -*- coding: utf-8 -*-

from odoo import models, fields,api


class ProjectProject(models.Model):
    _inherit = 'project.project'

    ohc_id = fields.Many2one(
        'ohc.management',
        string='OHC'
    )
    
class ProjectProject(models.Model):
    _inherit = 'project.project'

    ohc_id = fields.Many2one(
        'ohc.management',
        string='OHC'
    )

    @api.model
    def create(self, vals):

        project = super().create(vals)

        if project.ohc_id:
            project.ohc_id.update_project_details(project)

        return project

    def write(self, vals):

        res = super().write(vals)

        for rec in self:

            if rec.ohc_id:
                rec.ohc_id.update_project_details(rec)

        return res
    

