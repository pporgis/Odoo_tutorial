from odoo import fields, models, api
from odoo.exceptions import UserError, AccessError
from itertools import groupby
from odoo import Command

class EstateProperty(models.Model):
    _inherit = "estate.property"

    def action_sold(self):
        # self.sudo()._create_invoices()
        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.buyer,
            'journal_id': self.env['account.move'].with_context(
                default_move_type='out_invoice')._get_default_journal().id,
            'invoice_line_ids': [
                (0, 0, {
                    "name": "Property",
                    "quantity": "1",
                    "price_unit": self.selling_price,
                }), (0, 0, {
                    "name": "Provision",
                    "quantity": "1",
                    "price_unit": self.selling_price * 0.06
                }), (0, 0, {
                    "name": "Administrative fees",
                    "quantity": "1",
                    "price_unit": 100
                })],
        }
        moves = self.env['account.move'].create(invoice_vals)
        return super().action_sold()