from math import ceil


def simula(compradors, conversio, comandes, preu, cost_variable, cac, fix, inversio):
    clients = compradors * conversio / 100
    ingressos = clients * comandes * preu
    contribucio = clients * comandes * (preu - cost_variable)
    marge_client = comandes * (preu - cost_variable) - cac
    resultat = contribucio - clients * cac - fix
    return {
        "Clients esperats": clients,
        "Ingressos anuals (€)": ingressos,
        "Contribució abans de captació i fixos (€)": contribucio,
        "Resultat operatiu del primer any (€)": resultat,
        "Resultat del primer any després de la inversió (€)": resultat - inversio,
        "Clients per cobrir fixos i inversió el primer any":
            ceil((fix + inversio) / marge_client) if marge_client > 0 else None,
        "Recuperació simple (mesos)": inversio / resultat * 12 if resultat > 0 else None,
    }
