from odoo import api, exceptions, fields, models

class Checkout(models.Model):
    _name = 'library.checkout'
    _description = 'Checkout Request'
    _inherit = ['mail.thread','mail.activity']
    member_image = fields.Binary(related='member_id.partner_id.image')
    member_id = fields.Many2one(
        'library.member',
        required=True)
    user_id = fields.Many2one(
        'res.users',
        'Librarian',
        default=lambda s: s.env.uid)
    request_date = fields.Date(
        default=lambda s: fields.Date.today())
    line_ids = fields.One2many(
        'library.checkout.line',
        'checkout_id',
        string='Borrowed Books')
    checkout_date = fields.Date(readonly=True)
    close_date = fields.Date(readonly=True)
    num_books = fields.Integer(compute='_compute_num_books', store=True)
    num_other_checkouts = fields.Integer(compute='_compute_num_other_checkouts')

    color = fields.Integer('Color Index')
    priority = fields.Selection([('0','Low'),
                                ('1','Normal'),
                                ('2','High')],
                                'Priority',
                                default='1')
    kanban_state = fields.Selection([('normal','In Progress'),
                                    ('blocked','Blocked'),
                                    ('done','Ready for next stage')],
                                    'Kanban State',
                                    default='normal')


    
    def _compute_num_other_checkouts(self):
        for rec in self:
            domain = [
                ('member_id','=',checkout.rec.id),
                ('state','in',['open']),
                ('id','!=',rec.id)]
            rec.num_other_checkouts = self.search_count(domain)

    @api.depends('line_ids')
    def _compute_num_books(self):
        for book in self:
            book.num_books = len(book.line_ids)




    stage_id = fields.Many2one(
        'library.checkout.stage',
        default=_default_stage,
        group_expand=_group_expand_stage_id)

    stage=fields.Selection(related='stage_id.state')

    @api.model
    def create(self, vals):
        #Code before create: should use the vals dict
        if 'stage_id' in vals:
            Stage = self.env['library.checkout.stage']
            new_stage = Stage.browse(vals['stage_id']).stage
            if new_state == 'open':
                vals['checkout_date'] = fields.Date.today()
        new_record = super().create(vals)
        #Code after create: can use the 'new_record' created
        if new_record.state == 'done':
            raise exceptions.UserError(
                'Not allowed to create a checkout in the done state')
        return new_record
    
    @api.multi
    def write(self, vals):
        if 'stage_id' in vals:
            Stage = self.env['library.checkout.state']
            new_state = Stage.browse(vals['stage_id']).stage
            if new_state == 'open' and self.state != 'open':
                vals['checkout_date'] = fields.Date.today()
                if new_stage == 'done' and self.state != 'done':
                    vals['close_date'] = fields.Date.today()
            super().write(vals)
            return True

    @api.model
    def _default_stage(self):
        Stage = self.env['library.checkout.stage']
        return Stage.search([], limit=1)

    @api.model
    def _group_expand_stage_id(self, stages, domain, order):
        return stages.search([], order=order)
    
    

    @api.onchange('member_id')
    def onchange_member_id(self):
        today = fields.Date.today()
        if self.request_date != today:
            self.request_date = fields.Date.today()
            return {
                'warning':{
                    'title':'Changed Request Date',
                    'message':'Request date changed to today.',
                }
            }
    
    def button_done(self):
        Stage = self.env['library.checkout.state']
        done_stage = Stage.search([('state','=','done')], limit=1)
        for checkout in self:
            checkout.stage_id = done_stage
        return True

class CheckoutLine(models.Model):
    _name = 'library.checkout.line'
    _description = 'Borrow Request Line'
    checkout_id = fields.Many2one('library.checkout')
    book_id = fields.Many2one('library.book')
    
    