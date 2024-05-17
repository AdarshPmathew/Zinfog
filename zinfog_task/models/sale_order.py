from odoo import fields,api,models
from odoo.exceptions import UserError, ValidationError

class SaleOrder(models.Model):
    _inherit = "sale.order"

    delivery_charge = fields.Float(string="Delivery Charge (%)", default=10)

    @api.model
    def create(self, vals):
        data = super(SaleOrder, self).create(vals)

        delivery_product = self.env['product.product'].search([('name', '=', 'Delivery Charges')], limit=1)
        if not delivery_product:
            raise UserError("Delivery Charges product not found. Please create it.")

        delivery_product = delivery_product[0]  # Ensure singleton

        delivery_lines = data.order_line.filtered(lambda line: line.is_delivery_charge)

        if data.order_line:
            total_without_delivery = sum(line.price_total for line in data.order_line.filtered(
                lambda line: not line.is_delivery_charge and not line.display_type))

            if not delivery_lines:
                new_delivery_line = self.env['sale.order.line'].create({
                    'order_id': data._origin.id,
                    'name': delivery_product.name,
                    'product_id': delivery_product.id,
                    'price_unit': (total_without_delivery) * (data.delivery_charge / 100),
                    'is_delivery_charge': True,
                    'tax_id': False,
                })
                data.update({'order_line': [(4, new_delivery_line.id)]})
            else:
                delivery_lines.write({
                    'price_unit': (total_without_delivery) * (data.delivery_charge / 100),
                })
        else:
            if delivery_lines:
                for delivery_line in delivery_lines:
                    delivery_line.active = False
        return data

    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        if 'delivery_charge' in vals or 'order_line' in vals:
            for order in self:
                delivery_product = self.env['product.product'].search([('name', '=', 'Delivery Charges')], limit=1)
                if not delivery_product:
                    raise UserError("Delivery Charges product not found. Please create it.")
                delivery_lines = order.order_line.filtered(lambda line: line.is_delivery_charge)
                total_without_delivery = sum(line.price_total for line in order.order_line.filtered(
                    lambda line: not line.is_delivery_charge and not line.display_type))
                if order.order_line:
                    if not delivery_lines:
                        new_delivery_line = self.env['sale.order.line'].create({
                            'order_id': order._origin.id,
                            'name': delivery_product.name,
                            'product_id': delivery_product.id,
                            'price_unit': (total_without_delivery) * (order.delivery_charge / 100),
                            'is_delivery_charge': True,
                            'tax_id': False,
                        })
                        order.update({'order_line': [(4, new_delivery_line.id)]})
                    else:
                        delivery_lines.write({
                            'price_unit': (total_without_delivery) * (order.delivery_charge / 100),
                        })
                else:
                    if delivery_lines:
                        for delivery_line in delivery_lines:
                            delivery_line.active = False
        return res


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    is_delivery_charge = fields.Boolean()
    brand_id = fields.Many2one('product.brand',string="Brand", compute="_compute_brand_id",readonly=False,store=True)
            
    def create(self,vals):
        sale_line = super(SaleOrderLine,self).create(vals)
        for rec in sale_line:
            if rec.price_unit < rec.product_id.minimum_cost:
                raise UserError(f'Unit Price of {rec.name} ({rec.currency_id.symbol}{rec.price_unit}) cannot be less than its Minimum cost ({rec.currency_id.symbol}{rec.product_id.minimum_cost})')
        return sale_line
    
    def write(self,vals):
        if vals.get('product_id'):
            product = self.env['product.product'].browse(vals['product_id'])
        else:
            product = self.product_id
        if vals.get('price_unit'):
            price_unit = vals['price_unit']
        else:
            price_unit = self.price_unit

        if price_unit < product.minimum_cost:
            raise UserError(f'Unit Price of {self.name} ({self.currency_id.symbol}{price_unit}) cannot be less than its Minimum cost ({self.currency_id.symbol}{product.minimum_cost})')
        sale_line = super(SaleOrderLine,self).write(vals)
        return sale_line

    @api.depends('product_id')
    def _compute_brand_id(self):
        for record in self:
            if record.product_id:
                data = self.env['product.template'].search([('id', '=', record.product_id.id)], limit=1)
                if data:
                    record.brand_id = data.brand_id.id
                else:
                    pass


