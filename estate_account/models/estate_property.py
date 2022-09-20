from odoo import fields, models, api, _
from odoo.exceptions import UserError, AccessError
from itertools import groupby


class EstateProperty(models.Model):
    _inherit = "estate.property"

    def _create_invoices(self):
        if not self.env["account.move"].check_access_rights("write"):
            raise AccessError(_("You have no permission for this operation, contact manager."))
        if not (self.env["account.move"].check_access_rule("write")) is None:
            raise AccessError(_("You have no permission for this operation, contact manager."))

        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.buyer_id,
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

    def action_sold(self):
        print(" reached ".center(100, '='))

        self.sudo()._create_invoices()
        return super().action_sold()