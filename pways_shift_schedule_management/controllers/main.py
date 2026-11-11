# -*- coding: utf-8 -*-
import json
from odoo import http
from odoo.http import content_disposition, request
# from odoo.addons.web.controllers.main import _serialize_exception
from odoo.tools import html_escape


class XLSXReportController(http.Controller):

    @http.route('/xlsx_reports', type='http', auth='user', methods=['GET'], csrf=False)
    def get_report_xlsx(self, **kw):
        try:
            model = kw.get('model')
            options = json.loads(kw.get('options', '{}'))
            output_format = kw.get('output_format')
            report_name = kw.get('report_name') or 'report'

            uid = request.session.uid
            report_obj = request.env[model].with_user(uid)

            if output_format == 'xlsx':
                response = request.make_response(
                    None,
                    headers=[
                        ('Content-Type', 'application/vnd.ms-excel'),
                        ('Content-Disposition', content_disposition(report_name + '.xlsx'))
                    ]
                )
                report_obj.get_xlsx_report(options, response)
                return response

            return request.make_response('Invalid output format.', status=400)
        except Exception as e:
            return request.make_response(str(e), status=500)

