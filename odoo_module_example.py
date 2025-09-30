"""
Exemple de module Odoo pour l'intégration avec l'application de génération de rapports

Structure du module Odoo :
/addons/tmh_report_generator/
    __manifest__.py
    models/
        __init__.py
        report_access.py
    views/
        report_access_views.xml
    security/
        ir.model.access.csv

"""

# __manifest__.py
MANIFEST = {
    'name': 'TMH Report Generator',
    'version': '1.0',
    'author': 'TMH',
    'category': 'Tools',
    'summary': 'Accès sécurisé à l\'application de génération de rapports',
    'description': """
    Module permettant d'accéder de manière sécurisée à l'application
    de génération de rapports externe via des tokens temporaires.
    """,
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/report_access_views.xml',
    ],
    'installable': True,
    'application': False,
}

# models/report_access.py
MODEL_CODE = """
from odoo import models, fields, api
import uuid
from datetime import datetime, timedelta
import requests

class ReportAccess(models.Model):
    _name = 'tmh.report.access'
    _description = 'Accès aux rapports TMH'

    name = fields.Char(string='Nom', required=True)
    token = fields.Char(string='Token', readonly=True)
    expiry_date = fields.Datetime(string='Date d\'expiration', readonly=True)
    report_url = fields.Char(string='URL de l\'application',
                            default='http://94.103.211.39:8000')

    def generate_access_token(self):
        '''Génère un token temporaire et redirige vers l'application'''
        for record in self:
            # Générer un token unique
            token = str(uuid.uuid4())
            expiry = datetime.now() + timedelta(hours=1)

            # Sauvegarder le token
            record.write({
                'token': token,
                'expiry_date': expiry
            })

            # Construire l'URL avec le token
            redirect_url = f"{record.report_url}/auth?token={token}"

            # Retourner une action de redirection
            return {
                'type': 'ir.actions.act_url',
                'url': redirect_url,
                'target': 'new',  # Ouvre dans un nouvel onglet
            }

    @api.model
    def verify_token(self, token):
        '''Vérifie si un token est valide (appelé par l'application externe)'''
        record = self.search([
            ('token', '=', token),
            ('expiry_date', '>', datetime.now())
        ], limit=1)

        return bool(record)

    def open_report_app(self):
        '''Bouton pour ouvrir l'application de rapports'''
        return self.generate_access_token()
"""

# views/report_access_views.xml
VIEW_XML = """
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_report_access_form" model="ir.ui.view">
        <field name="name">tmh.report.access.form</field>
        <field name="model">tmh.report.access</field>
        <field name="arch" type="xml">
            <form string="Accès Rapports TMH">
                <header>
                    <button name="open_report_app"
                            string="Ouvrir l'application de rapports"
                            type="object"
                            class="btn-primary"/>
                </header>
                <sheet>
                    <group>
                        <field name="name"/>
                        <field name="report_url"/>
                        <field name="token" readonly="1"/>
                        <field name="expiry_date" readonly="1"/>
                    </group>
                </sheet>
            </form>
        </field>
    </record>

    <record id="view_report_access_tree" model="ir.ui.view">
        <field name="name">tmh.report.access.tree</field>
        <field name="model">tmh.report.access</field>
        <field name="arch" type="xml">
            <tree string="Accès Rapports TMH">
                <field name="name"/>
                <field name="expiry_date"/>
                <button name="open_report_app"
                        string="Ouvrir Rapports"
                        type="object"
                        icon="fa-external-link"/>
            </tree>
        </field>
    </record>

    <record id="action_report_access" model="ir.actions.act_window">
        <field name="name">Génération de Rapports</field>
        <field name="res_model">tmh.report.access</field>
        <field name="view_mode">tree,form</field>
    </record>

    <menuitem id="menu_report_access_root"
              name="Rapports TMH"
              sequence="100"/>
    <menuitem id="menu_report_access"
              name="Génération de Rapports"
              parent="menu_report_access_root"
              action="action_report_access"
              sequence="10"/>
</odoo>
"""

# security/ir.model.access.csv
SECURITY_CSV = """
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_tmh_report_access,tmh.report.access,model_tmh_report_access,base.group_user,1,1,1,1
"""