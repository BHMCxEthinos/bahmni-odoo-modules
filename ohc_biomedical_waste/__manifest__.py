{
    'name': 'OHC Biomedical Waste Management',
    'version': '16.0.1.0.0',
    'summary': 'Track biomedical waste pickup/collection logs for OHC centers',
    'description': """
Biomedical Waste Management (CR#1)
===================================
Adds a Waste Collection log to the OHC Management module.

* Log each waste pickup with date & time, colour-coded bag counts and
  weights (Red, White, Black, Yellow, Blue), receipt number, remarks and a
  receipt attachment (PDF/image).
* Smart button on the OHC form showing the last pickup date & time.
* Entries can be edited later to attach the receipt copy once available.
* Access rights inherit the OHC Management module's security groups.

NOTE: This module depends on an existing "OHC Management" module
(model assumed here as `ohc.center`). Update the `depends` list and
the `_inherit` / view-inherit references below to match the real
technical names in your codebase before installing.
""",
    'category': 'Services/OHC',
    'author': 'Your Company',
    'license': 'LGPL-3',
    # TODO: replace 'ohc_management' with the actual technical name of your existing OHC module
    'depends': ['base', 'mail', 'ohc_management'],
    'data': [
        'security/ir.model.access.csv',
        'views/waste_collection_views.xml',
        'views/ohc_management_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
