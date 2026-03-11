import pandas as pd


def categoriser_lignes(categorie):
    return {"categorie": categorie}


def count_by_categorie(categorie, filename="tickets.csv"):
    df = pd.read_csv(filename)
    count = len(df[df["categorie"] == categorie])

    return {
        "categorie": categorie,
        "count": int(count)
    }


def get_examples_by_categorie(categorie, limit=10, filename="tickets.csv"):
    df = pd.read_csv(filename)
    examples = df[df["categorie"] == categorie].head(limit).to_dict(orient="records")

    return {
        "categorie": categorie,
        "examples": examples
    }


def check_factures(categorie, filename="tickets.csv"):
    df = pd.read_csv(filename)

    if "facture_status" not in df.columns:
        df["facture_status"] = ""

    mask = df["categorie"] == categorie

    for idx in df[mask].index:
        result = get_pdf(df.loc[idx].to_dict())
        df.at[idx, "facture_status"] = "facture OK" if result == "OK" else "facture KO"

    df.to_csv(filename, index=False)

    return {
        "categorie": categorie,
        "updated_rows": int(mask.sum())
    }


def get_pdf(row):
    return "OK"