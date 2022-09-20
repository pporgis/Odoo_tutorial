import datetime
from openerp.tools import float_compare

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class EstateProperty(models.Model):
    # Private attributes
    _name = "estate.property"
    _description = "Estate property test module"
    _order = "id desc"

    # Default methods

    # Fields declaration
    name = fields.Char(required=True)
    description = fields.Text()
    postcode = fields.Char()
    date_availability = fields.Date(default=fields.Date.today(), copy=False)
    expected_price = fields.Float(required=True)
    selling_price = fields.Float(readonly=True, copy=False)
    bedrooms = fields.Integer(default=2)
    living_area = fields.Integer()
    facades = fields.Integer()
    garage = fields.Boolean()
    garden = fields.Boolean()
    garden_area = fields.Integer()
    garden_orientation = fields.Selection(
        string='Garden Orientation',
        selection=[('north', 'North'), ('south', 'South'), ('east', 'East'), ('west', 'West'), ('empty', '')],
        help="Garden Orientation is used to separate world parties")
    active = fields.Boolean(default=True)
    state = fields.Selection(
        string='State',
        selection=[('new', 'New'), ('received', 'Offer Received'), ('accepted', 'Offer Accepted'), ('sold', 'Sold'),
                   ('canceled', 'Canceled')],
        help="State is used to show state of property",
        required=True,
        copy=False,
        default='new')
    property_type_id = fields.Many2one("estate.property.type", string="Property Type")
    buyer_id = fields.Many2one('res.partner', string="Buyer")
    user_id = fields.Many2one('res.users', string='Salesman', index=True, tracking=True)
    # user_id = fields.Many2one('res.users', string='Salesman', index=True, tracking=True,
    #                           default=lambda self: self.env.user)
    tag_ids = fields.Many2many("estate.property.tag", string="Tags")
    offer_ids = fields.One2many("estate.property.offer", "property_id", string="Offers")
    total_area = fields.Integer(compute="_compute_total_area")
    best_price = fields.Float(compute="_compute_best_price")
    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.company, required="True")

    _sql_constraints = [
        ('check_price', 'CHECK(expected_price >= 0 AND selling_price >= 0)',
         'Price must be positive.')
    ]

    # compute and search fields, in the same order of fields declaration
    @api.depends("living_area", "garden_area")
    def _compute_total_area(self):

        for record in self:
            record.total_area = record.living_area + record.garden_area

    @api.depends("offer_ids")
    def _compute_best_price(self):

        for record in self:
            record.best_price = max(record.offer_ids.mapped('price'), default=0)

    # Constraints and onchanges
    @api.constrains('selling_price')
    def _check_price_percentil(self):
        for record in self:
            if float_compare(float(record.selling_price), float(record.expected_price * 0.90), precision_digits=2) < 0:
                raise ValidationError(_(f"Price must be at least 90% of expected price."))

    @api.onchange("garden")
    def _onchange_garden(self):
        if self.garden is True:
            self.garden_area = 10
            self.garden_orientation = "north"
        else:
            self.garden_area = 0
            self.garden_orientation = "empty"

    # CRUD methods (and name_get, name_search, ...) overrides
    def unlink(self):
        for rec in self:
            if not rec.state == 'new' and not rec.state == 'canceled':
                raise ValidationError(_("Only New or Canceled property can be canceled"))

        return super().unlink()

    # Action methods
    def action_cancel(self):
        if self.state == 'sold':
            message = "Property is already sold."
            if message:
                return {
                    'effect': {
                        'fadeout': 'fast',
                        'message': message,
                        'type': 'rainbow_man',
                    }
                }
        else:
            self.state = 'canceled'
        return True

    def action_sold(self):
        if self.state == 'canceled':
            message = "Property is already canceled."
            if message:
                return {
                    'effect': {
                        'fadeout': 'slow',
                        'message': message,
                        'type': 'rainbow_man',
                    }
                }
        else:
            self.state = 'sold'
        return True

    # Business methods


class EstatePropertyType(models.Model):
    _name = "estate.property.type"
    _description = "Estate property type"
    _order = "name"

    name = fields.Char(required=True)
    property_ids = fields.One2many("estate.property", "property_type_id", string="Property Ids")
    sequence = fields.Integer('Sequence', default=1, help="Used to order stages. Lower is better.")
    offers_count = fields.Integer(compute='_compute_offers_count')

    _sql_constraints = [
        ('name_type_unique', 'unique(name)', 'Type must be unique!')]

    def _compute_offers_count(self):
        for record in self:
            record.offers_count = self.env['estate.property.offer'].search_count(
                [('property_id.property_type_id', '=', self.id)])

    def action_show_offers(self):
        self.ensure_one()

        return self.env['estate.property.offer']._get_offers(self.id)


class EstatePropertyTag(models.Model):
    _name = "estate.property.tag"
    _description = "Estate property tag"
    _order = "name"

    name = fields.Char(required=True)
    color = fields.Integer('color')

    _sql_constraints = [
        ('name_tag_unique', 'unique(name)', 'Tag must be unique!')]


class EstatePropertyOffer(models.Model):
    _name = "estate.property.offer"
    _description = _("Estate property offer")
    _order = "price desc"

    price = fields.Float()
    status = fields.Selection(
        string='Status',
        selection=[('accepted', 'Accepted'), ('refused', 'Refused')],
        copy=False)
    partner_id = fields.Many2one('res.partner', string='Partner', required=True)
    property_id = fields.Many2one('estate.property', string='Property', required=True)
    create_date = fields.Date(default=fields.Date.today())
    validity = fields.Integer(default=7)
    date_deadline = fields.Date(compute="_compute_deadline_date", inverse="_inverse_deadline_date")
    related_property_type_id = fields.Many2one(related="property_id.property_type_id", store=True)

    _sql_constraints = [
        ('check_offer_price', 'CHECK(price >= 0)',
         'Price must be positive.')
    ]

    def _get_offers(self, id):
        """ Select offers for specific property type
        """
        return {
            'name': _('Property Offers'),
            'view_mode': 'list,form',
            'res_model': 'estate.property.offer',
            'domain': [("related_property_type_id", "=", id)],
            'type': 'ir.actions.act_window',
            'context': {'offer': self.ids},
            "target": "self"
        }

    @api.depends("create_date", "validity")
    def _compute_deadline_date(self):

        for record in self:
            record.date_deadline = record.create_date + datetime.timedelta(days=record.validity)

    def _inverse_deadline_date(self):

        for record in self:
            record.validity = (record.date_deadline - record.create_date).days

    def action_accept(self):
        if self.status is not 'accepted' and self.property_id.selling_price == 0.0:
            self.status = 'accepted'
            self.property_id.state = 'accepted'
            self.property_id.buyer_id = self.partner_id
            self.property_id.selling_price = self.price
        else:
            message = _("Property is already accepted.")
            if message:
                return {
                    'effect': {
                        'fadeout': 'slow',
                        'message': message,
                        'type': 'rainbow_man',
                    }
                }
        return True

    def action_refuse(self):
        if self.status is not 'refused':
            self.status = 'refused'
        return True

    @api.model
    def create(self, vals):
        if float_compare(vals['price'], self.env['estate.property'].browse(vals['property_id']).best_price,
                         precision_digits=2) < 0:
            raise ValidationError(_("Offer must be higher then Best price"))

        self.env['estate.property'].browse(vals['property_id']).state = 'received'
        return super().create(vals)
