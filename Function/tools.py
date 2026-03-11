from Function.constants import CATEGORIES, FACTURE_CATEGORIES

tools = [
    {
        "type": "function",
        "name": "categoriser_lignes",
        "description": "Catégorise un commentaire reçu pour le support niveau 1 de l'espace client Orange. Retourne exactement une valeur de l'enum categorie et choisis le code le plus précis possible.",
        "parameters": {
            "type": "object",
            "properties": {
                "categorie": {
                    "type": "string",
                    "description": "Code unique de catégorisation.",
                    "enum": CATEGORIES
                }
            },
            "required": ["categorie"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "count_by_categorie",
        "description": "Compte le nombre de lignes dans le fichier CSV pour une catégorie donnée.",
        "parameters": {
            "type": "object",
            "properties": {
                "categorie": {
                    "type": "string",
                    "description": "Code catégorie à compter.",
                    "enum": CATEGORIES
                },
                "filename": {
                    "type": "string",
                    "description": "Nom du fichier CSV à analyser."
                }
            },
            "required": ["categorie"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "get_examples_by_categorie",
        "description": "Retourne quelques exemples de lignes correspondant à une catégorie donnée.",
        "parameters": {
            "type": "object",
            "properties": {
                "categorie": {
                    "type": "string",
                    "description": "Code catégorie à filtrer.",
                    "enum": CATEGORIES
                },
                "limit": {
                    "type": "integer",
                    "description": "Nombre maximum d'exemples à retourner.",
                    "default": 10
                },
                "filename": {
                    "type": "string",
                    "description": "Nom du fichier CSV à analyser."
                }
            },
            "required": ["categorie"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "check_factures",
        "description": "Applique une vérification de facture sur toutes les lignes correspondant à une catégorie et ajoute ou met à jour la colonne facture_status dans le CSV.",
        "parameters": {
            "type": "object",
            "properties": {
                "categorie": {
                    "type": "string",
                    "description": "Code catégorie à traiter.",
                    "enum": FACTURE_CATEGORIES
                },
                "filename": {
                    "type": "string",
                    "description": "Nom du fichier CSV à mettre à jour."
                }
           },
            "required": ["categorie"],
            "additionalProperties": False
        }
    }
]