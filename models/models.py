# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp


class odoo12task(models.Model):
    _name = 'odoo12task.odoo12task'
    _order = 'date_order desc, id desc'

    name = fields.Char(string='Order Reference', required=True, copy=False, readonly=True,
                       index=True, default=lambda self: _('New'))
    partner_id = fields.Many2one('res.partner', string='Customer', readonly=False,
                                 required=True,
                                 index=True, track_visibility='always', track_sequence=1)
    date_order = fields.Datetime(string='Order Date', required=True, readonly=True, index=True,
                                 copy=False,
                                 default=fields.Datetime.now)
    order_line = fields.One2many(comodel_name="odoo12task.line", inverse_name="order_id", string="Order Lines",
                                 copy=True)
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env['res.company']._company_default_get(
                                     'odoo12task.odoo12task'))
    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_amount_all',
                                     track_visibility='onchange', track_sequence=5)
    amount_tax = fields.Monetary(string='Taxes', store=True, readonly=True, compute='_amount_all')
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all',
                                   track_visibility='always', track_sequence=6)
    current_user = fields.Many2one('res.users', 'Current User', default=lambda self: self.env.user,
                                   track_visibility="onchange")
    note = fields.Text('Terms and conditions')
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist', required=False, readonly=True,
                                   help="Pricelist for current sales order.")
    currency_id = fields.Many2one("res.currency", related='pricelist_id.currency_id', string="Currency", readonly=True,
                                  required=True)

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'odoo12task.odoo12task') or 'New'
        result = super(odoo12task, self).create(vals)
        return result

    @api.depends('order_line.price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
            order.update({
                'amount_untaxed': amount_untaxed,
                'amount_tax': amount_tax,
                'amount_total': amount_untaxed + amount_tax,
            })


class odoo12taskline(models.Model):
    _name = 'odoo12task.line'
    _order = 'order_id, sequence, id'

    order_id = fields.Many2one(comodel_name="odoo12task.odoo12task", string="Order Reference", required=True,
                               index=True, copy=False)
    name = fields.Text(string='Description', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    price_unit = fields.Float('Unit Price', required=True, digits=dp.get_precision('Product Price'), default=0.0)
    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', readonly=True, store=True)
    price_tax = fields.Float(compute='_compute_amount', string='Total Tax', readonly=True, store=True)
    price_total = fields.Monetary(compute='_compute_amount', string='Total', readonly=True, store=True)
    discount = fields.Float(string='Discount (%)', digits=dp.get_precision('Discount'), default=0.0)
    tax_id = fields.Many2many('account.tax', string='Taxes')
    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)],
                                 change_default=True, ondelete='restrict')
    product_uom_qty = fields.Float(string='Ordered Quantity', digits=dp.get_precision('Product Unit of Measure'),
                                   required=True, default=1.0)
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure')
    currency_id = fields.Many2one(related='order_id.currency_id', depends=['order_id.currency_id'], store=True,
                                  string='Currency', readonly=True)

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty,
                                            product=line.product_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    # @api.onchange('product_id')
    # def onchange_method(self):
    #     self.field_name = ''

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        self.price_unit = self.product_id.lst_price

