# -*- coding: utf-8 -*-
from odoo import http

# class Odoo12task(http.Controller):
#     @http.route('/odoo12task/odoo12task/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/odoo12task/odoo12task/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('odoo12task.listing', {
#             'root': '/odoo12task/odoo12task',
#             'objects': http.request.env['odoo12task.odoo12task'].search([]),
#         })

#     @http.route('/odoo12task/odoo12task/objects/<model("odoo12task.odoo12task"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('odoo12task.object', {
#             'object': obj
#         })