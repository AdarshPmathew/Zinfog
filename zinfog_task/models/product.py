from odoo import models,api,fields
import logging

class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_delivery_charge_product = fields.Boolean()
    minimum_cost = fields.Monetary(string="Minimum Cost")
    brand_id = fields.Many2one('product.brand',string="Brand Name")

class ProductProduct(models.Model):
    _inherit = "product.product"
    minimum_cost = fields.Monetary(string="Minimum Cost")
    brand_id = fields.Many2one('product.brand',string="Brand Name")

    def create(self,vals):
        for rec in vals:
            prod_template = self.env['product.template'].browse(rec.get('product_tmpl_id'))
            rec['minimum_cost'] = prod_template.minimum_cost
            rec['brand_id'] = prod_template.brand_id.id
        return super(ProductProduct,self).create(vals)


class ProductBrand(models.Model):
    _name = "product.brand"
    name = fields.Char("Brand Name")