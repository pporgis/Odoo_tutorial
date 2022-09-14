from odoo import fields, models, api


class ResUsers(models.Model):
    _inherit = "res.users"

    property_ids = fields.One2many("estate.property", "user_id", domain="['|', ('state', '=', 'offer received'), ('state', '=', 'new')]")
    nam = fields.Char()