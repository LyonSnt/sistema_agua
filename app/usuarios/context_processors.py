def roles_usuario(request):
    if not request.user.is_authenticated:
        return {}

    grupos = set(
        request.user.groups.values_list("name", flat=True)
    )

    return {
        "es_admin": request.user.is_superuser or "Administrador" in grupos,
        "es_cajero": "Cajero" in grupos,
        "es_lecturista": "Lecturista" in grupos,
        "es_supervisor": "Supervisor" in grupos,
        "es_consulta": "Consulta" in grupos,
    }