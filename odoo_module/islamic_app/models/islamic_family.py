import logging
from datetime import timedelta
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class IslamicFamilyMember(models.Model):
    _name = 'islamic.family.member'
    _description = 'Family Member (Silat al-Rahim)'
    _order = 'relationship, name'

    app_user_id = fields.Many2one('islamic.app.user', string='User', required=True, ondelete='cascade', index=True)
    name = fields.Char(string='Name', required=True)
    relationship = fields.Selection([
        ('parent', 'Parent'),
        ('child', 'Child'),
        ('sibling', 'Sibling'),
        ('grandparent', 'Grandparent'),
        ('grandchild', 'Grandchild'),
        ('uncle_aunt', 'Uncle/Aunt'),
        ('cousin', 'Cousin'),
        ('nephew_niece', 'Nephew/Niece'),
        ('spouse', 'Spouse'),
        ('in_law', 'In-Law'),
        ('other', 'Other Relative'),
    ], string='Relationship', required=True)
    phone_number = fields.Char(string='Phone Number')
    photo = fields.Binary(string='Photo')
    photo_url = fields.Char(string='Photo URL')
    notes = fields.Text(string='Notes')

    # Contact tracking
    last_contact_date = fields.Date(string='Last Contact Date')
    contact_frequency_days = fields.Integer(string='Remind Every (days)', default=7,
                                             help='How often to remind about contacting this person')
    next_reminder_date = fields.Date(string='Next Reminder', compute='_compute_next_reminder', store=True)
    is_overdue = fields.Boolean(string='Contact Overdue', compute='_compute_is_overdue', store=True)

    # Contact log
    contact_log_ids = fields.One2many('islamic.family.contact.log', 'family_member_id', string='Contact History')
    total_contacts = fields.Integer(string='Total Contacts', compute='_compute_total_contacts')

    active = fields.Boolean(default=True)

    @api.depends('last_contact_date', 'contact_frequency_days')
    def _compute_next_reminder(self):
        for rec in self:
            if rec.last_contact_date and rec.contact_frequency_days:
                rec.next_reminder_date = rec.last_contact_date + timedelta(days=rec.contact_frequency_days)
            elif rec.contact_frequency_days:
                rec.next_reminder_date = fields.Date.today()
            else:
                rec.next_reminder_date = False

    @api.depends('next_reminder_date')
    def _compute_is_overdue(self):
        today = fields.Date.today()
        for rec in self:
            rec.is_overdue = rec.next_reminder_date and rec.next_reminder_date <= today

    @api.depends('contact_log_ids')
    def _compute_total_contacts(self):
        for rec in self:
            rec.total_contacts = len(rec.contact_log_ids)

    def log_contact(self, contact_type='call', notes=''):
        """Log a contact with this family member"""
        self.ensure_one()
        self.env['islamic.family.contact.log'].create({
            'family_member_id': self.id,
            'app_user_id': self.app_user_id.id,
            'contact_type': contact_type,
            'notes': notes,
        })
        self.write({'last_contact_date': fields.Date.today()})

    def to_dict(self):
        self.ensure_one()
        return {
            'id': self.id,
            'name': self.name,
            'relationship': self.relationship,
            'phone': self.phone_number,
            'photo_url': self.photo_url,
            'last_contact': self.last_contact_date.isoformat() if self.last_contact_date else None,
            'next_reminder': self.next_reminder_date.isoformat() if self.next_reminder_date else None,
            'is_overdue': self.is_overdue,
            'contact_frequency_days': self.contact_frequency_days,
            'total_contacts': self.total_contacts,
        }


class IslamicFamilyContactLog(models.Model):
    _name = 'islamic.family.contact.log'
    _description = 'Family Contact Log'
    _order = 'create_date desc'

    family_member_id = fields.Many2one('islamic.family.member', string='Family Member',
                                        required=True, ondelete='cascade')
    app_user_id = fields.Many2one('islamic.app.user', string='User', required=True, ondelete='cascade')
    contact_type = fields.Selection([
        ('call', 'Phone Call'),
        ('visit', 'Visit'),
        ('message', 'Message'),
        ('gift', 'Gift/Charity'),
        ('prayer', 'Prayed For'),
        ('other', 'Other'),
    ], string='Contact Type', default='call')
    notes = fields.Text(string='Notes')
    date = fields.Date(string='Date', default=fields.Date.today)
    duration_minutes = fields.Float(string='Duration (minutes)')

    def to_dict(self):
        self.ensure_one()
        return {
            'id': self.id,
            'contact_type': self.contact_type,
            'notes': self.notes,
            'date': self.date.isoformat() if self.date else None,
            'duration_minutes': self.duration_minutes,
        }
