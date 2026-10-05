from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from typing import Any, Dict, Iterable, List, Optional
from uuid import UUID

from psycopg2.extras import RealDictCursor


# Usuarios excluidos en asignaciones automáticas normales.
EXCLUDED_AUTO_ASSIGN_EMAILS = (
    "gdelhoyo@contalink.com",
    "yaneth.olivo@contalink.com",
    "gdelhoyo@tegik.com",
)


def _query_one(conn, sql: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(sql, params)
        row = cur.fetchone()
        return dict(row) if row is not None else None


def _query_all(conn, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(sql, params)
        return [dict(row) for row in cur.fetchall()]


def _execute(conn, sql: str, params: tuple = ()) -> None:
    with conn.cursor() as cur:
        cur.execute(sql, params)


def _to_json_compatible(value: Any) -> Any:
    """Convierte tipos típicos de psycopg2 al equivalente que produciría JSON."""
    if isinstance(value, dict):
        return {k: _to_json_compatible(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_json_compatible(v) for v in value]
    if isinstance(value, Decimal):
        if value == value.to_integral_value():
            return int(value)
        return float(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, (date, time)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    return value


def _append_unique(values: List[int], value: Optional[int]) -> None:
    if value is not None and value not in values:
        values.append(value)


def _get_actual_date(conn) -> datetime:
    row = _query_one(
        conn,
        "SELECT util_get_actual_date_empresa(578) AS actual_date",
    )
    return row["actual_date"]


def _select_user_id_name_assigned_today(
    conn,
    *,
    email: str,
    require_auto_assignment: bool,
) -> Optional[Dict[str, Any]]:
    auto_filter = "AND u.auto_assignment = true" if require_auto_assignment else ""

    return _query_one(
        conn,
        f"""
        SELECT
            u.id,
            u.name,
            (
                SELECT COUNT(*)
                FROM system_utils.crm_deal
                WHERE assignment_time BETWEEN
                    DATE(util_get_actual_date_empresa(578)) + interval '0 hours'
                    AND DATE(util_get_actual_date_empresa(578)) + interval '23 hours 59 minutes 59 seconds'
                  AND asigned_user_id = u.id
            ) AS asigned_today
        FROM system_utils.crm_users u
        WHERE u.email = %s
          {auto_filter}
        ORDER BY asigned_today
        LIMIT 1
        """,
        (email,),
    )


def _select_random_open_stage_249_user(conn) -> Optional[Dict[str, Any]]:
    return _query_one(
        conn,
        """
        SELECT
            u.id,
            u.name,
            (
                SELECT COUNT(*)
                FROM system_utils.crm_deal
                WHERE assignment_time BETWEEN
                    DATE(util_get_actual_date_empresa(578)) + interval '0 hours'
                    AND DATE(util_get_actual_date_empresa(578)) + interval '23 hours 59 minutes 59 seconds'
                  AND asigned_user_id = u.id
            ) AS asigned_today
        FROM system_utils.crm_users u
        WHERE u.auto_assignment = true
          AND u.email NOT IN (
              'gdelhoyo@contalink.com',
              'yaneth.olivo@contalink.com',
              'gdelhoyo@tegik.com'
          )
        ORDER BY asigned_today
        LIMIT 1
        """,
    )


def _select_random_user(conn) -> Optional[Dict[str, Any]]:
    """Replica la rama final 'random assignment'."""
    return _query_one(
        conn,
        """
        SELECT
            u.id,
            u.name,
            (
                SELECT COUNT(*)
                FROM system_utils.crm_deal
                WHERE assignment_time BETWEEN
                    DATE(util_get_actual_date_empresa(578)) + interval '0 hours'
                    AND DATE(util_get_actual_date_empresa(578)) + interval '23 hours 59 minutes 59 seconds'
                  AND asigned_user_id = u.id
            ) AS asigned_today,
            COALESCE((
                SELECT ROUND(
                    COUNT(*) / system_utils.crm_get_worked_days_in_current_month(asigned_user_id),
                    2
                )
                FROM system_utils.crm_deal
                WHERE assignment_time > (
                    CASE
                        WHEN u.first_date > date_trunc('month', DATE(util_get_actual_date_empresa(578)))
                            THEN u.first_date
                        ELSE date_trunc('month', DATE(util_get_actual_date_empresa(578)))
                    END
                )
                  AND asigned_user_id = u.id
                GROUP BY asigned_user_id
            ), 0) AS promedio_mensual
        FROM system_utils.crm_users u
        WHERE u.auto_assignment = true
          AND u.email NOT IN (
              'gdelhoyo@contalink.com',
              'yaneth.olivo@contalink.com',
              'gdelhoyo@tegik.com'
          )
        ORDER BY asigned_today, promedio_mensual
        LIMIT 1
        """,
    )

def _is_crm_user_active(
    conn,
    user_id: Optional[int],
) -> bool:
    if user_id is None:
        return False

    row = _query_one(
        conn,
        """
        SELECT id
        FROM system_utils.crm_users
        WHERE id = %s
          AND active = 'true'
        LIMIT 1
        """,
        (user_id,),
    )

    return row is not None

def _get_crm_user(conn, user_id: Optional[int]) -> Optional[Dict[str, Any]]:
    if user_id is None:
        return None
    return _query_one(
        conn,
        "SELECT * FROM system_utils.crm_users WHERE id = %s LIMIT 1",
        (user_id,),
    )


def crm_assign_user_to_deal(
    conn,
    deal_id: int,
    *,
    mark_temporal_assigned: bool = True,
    debug: bool = False,
) -> Optional[Dict[str, Any]]:
    """
    Port Python de system_utils.crm_assign_user_to_deal_refactor(integer).

    IMPORTANTE:
    - Esta función NO hace commit ni rollback.
    - El caller controla la transacción.
    - Mantiene las funciones auxiliares existentes en PostgreSQL.
    - La lógica LOST fue simplificada:
        * 1 LOST  -> regresar con el agente que perdió ese deal.
        * 2+ LOST -> misma ronda que "random assignment".
        """

    def log(*args: Any) -> None:
        if debug:
            print("[crm_assign_user_to_deal]", *args)

    # ------------------------------------------------------------------
    # Variables de estado equivalentes al DECLARE de PL/pgSQL.
    # ------------------------------------------------------------------
    count_open_deal = 0
    count_recent_won_deal = 0
    count_won_deal = 0
    count_lost_deal = 0

    count_deal_active_contalink = 0
    count_deal_inactive_contalink = 0

    user_assign_lost: Optional[int] = None
    user_assign_won: Optional[int] = None
    user_assign_open: Optional[int] = None

    pending_fussion_contacts = False
    pending_fussion_deals = False

    person_has_valid_contact_information = False
    valid_phones_found = False

    persons_to_merge: List[int] = []
    aux_persons_to_merge: List[int] = []

    open_deals: List[int] = []
    aux_open_deals: List[int] = []

    # Equivale a v_aux_closest_deal: evita procesar el mismo deal más de una vez
    # cuando varias coincidencias apuntan a la misma persona/deal.
    processed_deals: List[int] = []

    oldest_open_deal: Optional[int] = None
    newest_user_id: Optional[int] = None
    oldest_stage_id: Optional[int] = None

    assignment_type = "specific"
    user_result: Optional[Dict[str, Any]] = None

    actual_date = _get_actual_date(conn)
    won_age = actual_date

    log("START", "DEAL", deal_id)

    # ------------------------------------------------------------------
    # Deal entrante.
    # ------------------------------------------------------------------
    deal = _query_one(
        conn,
        "SELECT * FROM system_utils.crm_deal WHERE id = %s",
        (deal_id,),
    )

    if deal is None:
        # La función SQL terminaría fallando posteriormente al intentar usar
        # campos de v_deal. Para el port hacemos el error explícito.
        raise ValueError(f"No existe system_utils.crm_deal.id={deal_id}")

    if mark_temporal_assigned:
        _execute(
            conn,
            """
            UPDATE system_utils.crm_deal
            SET is_temporal_assigned = true
            WHERE id = %s
            """,
            (deal_id,),
        )

    person = _query_one(
        conn,
        "SELECT * FROM system_utils.crm_person WHERE pipedrive_id = %s",
        (deal.get("person_id"),),
    )

    if person is None:
        raise ValueError(
            f"No existe crm_person para pipedrive_id={deal.get('person_id')}"
        )

    # La función original calcula v_fb_deal, pero actualmente sólo era usado
    # por una condición comentada. No altera el resultado actual.

    validation_row = _query_one(
        conn,
        """
        SELECT system_utils.crm_validate_contact_information(%s) AS validation
        """,
        (person.get("pipedrive_id"),),
    )

    validate_contact_information = (
        validation_row.get("validation") if validation_row else None
    ) or {}

    valid_contacts_value = validate_contact_information.get("valid_contacts")
    if isinstance(valid_contacts_value, str):
        person_has_valid_contact_information = (
            valid_contacts_value.strip().lower() == "true"
        )
    else:
        person_has_valid_contact_information = valid_contacts_value is True

    # PL/pgSQL sólo valida que la llave no sea NULL.
    valid_phones_found = (
        validate_contact_information.get("valid_phones") is not None
    )

    log("VALIDATION", validate_contact_information)

    # ------------------------------------------------------------------
    # Buscar contactos relacionados y analizar su historial.
    # ------------------------------------------------------------------
    if person_has_valid_contact_information:
        related_contacts = _query_all(
            conn,
            """
            SELECT out_value AS value
            FROM system_utils.get_related_contacts_for_deal_id(%s)
            LIMIT 15
            """,
            (person.get("pipedrive_id"),),
        )

        for person_contact in related_contacts:
            contact_value = person_contact.get("value")
            if contact_value is None:
                continue

            contact_value = str(contact_value)

            if "@" in contact_value:
                aux_current_email = contact_value
                # Valor dummy existente en PL/pgSQL.
                aux_current_phone = "811026697052"
            else:
                # Valor dummy existente en PL/pgSQL.
                aux_current_email = "jperez@tegik.com.mx"
                aux_current_phone = contact_value

            coincidences = _query_all(
                conn,
                """
                SELECT *
                FROM system_utils.crm_person_contacts
                WHERE (
                    (
                        regexp_replace(value, '[^0-9]+', '', 'g')::text
                            LIKE '%%' || RIGHT(
                                regexp_replace(%s, '[^0-9]+', '', 'g')::text,
                                10
                            ) || '%%'
                        AND type = 'phone'
                        AND %s
                    )
                    OR
                    (
                        value ILIKE REPLACE(%s, ' ', '')
                        AND type = 'email'
                    )
                )
                  AND value <> ''
                  AND LENGTH(value) > 9
                ORDER BY pipedrive_id ASC
                """,
                (
                    aux_current_phone,
                    valid_phones_found,
                    aux_current_email,
                ),
            )

            for coincidence in coincidences:
                coincidence_person_id = coincidence.get("pipedrive_id")

                # ------------------------------------------------------
                # Personas pendientes de merge.
                # IMPORTANTE: newest_user_id se sobrescribe igual que en
                # PL/pgSQL; no usamos max() global aquí a propósito.
                # ------------------------------------------------------
                if coincidence_person_id != person.get("pipedrive_id"):
                    pending_fussion_contacts = True
                    newest_user_id = coincidence_person_id
                    _append_unique(persons_to_merge, coincidence_person_id)

                person_deals = _query_all(
                    conn,
                    """
                    SELECT *
                    FROM system_utils.crm_deal
                    WHERE person_id = %s
                      AND id <> %s
                    ORDER BY add_time ASC
                    """,
                    (coincidence_person_id, deal_id),
                )

                for person_deal in person_deals:
                    current_deal_id = person_deal.get("id")

                    if current_deal_id in processed_deals:
                        continue

                    processed_deals.append(current_deal_id)

                    status = str(person_deal.get("status") or "").upper()

                    # --------------------------------------------------
                    # LOST
                    # Nueva regla:
                    #   1 LOST  -> mismo agente que perdió ese deal.
                    #   2+ LOST -> random assignment.
                    #
                    # No importa el stage_id en el que se perdió.
                    # --------------------------------------------------
                    if status == "LOST":
                        count_lost_deal += 1

                        # Si al terminar el análisis sólo existe un LOST,
                        # éste será necesariamente el agente que debemos
                        # conservar. Si aparecen más LOST, este valor deja
                        # de ser relevante porque se hará random assignment.
                        if count_lost_deal == 1:
                            user_assign_lost = person_deal.get(
                                "asigned_user_id"
                            )

                    # --------------------------------------------------
                    # WON
                    # --------------------------------------------------
                    elif status == "WON":
                        count_won_deal += 1
                        won_time = person_deal.get("won_time")

                        if won_time is not None:
                            if (actual_date - won_time).days < 30:
                                count_recent_won_deal += 1
                            else:
                                found_status = _query_one(
                                    conn,
                                    """
                                    SELECT ud.status
                                    FROM uc_deals ud
                                    LEFT JOIN uc_contacts uc
                                      ON uc.businesspartner_id = ud.businesspartner_id
                                    LEFT JOIN usuarios us
                                      ON us.uc_deal_id = ud.id
                                    WHERE uc.email ILIKE '%%' || %s || '%%'
                                       OR us.email ILIKE '%%' || %s || '%%'
                                    ORDER BY status
                                    LIMIT 1
                                    """,
                                    (
                                        coincidence.get("value"),
                                        coincidence.get("value"),
                                    ),
                                )

                                found_deal_contalink_status = (
                                    found_status.get("status")
                                    if found_status
                                    else None
                                )

                                if found_deal_contalink_status == "A":
                                    count_deal_active_contalink += 1
                                else:
                                    # La función original cuenta también NULL
                                    # como inactivo en esta rama.
                                    count_deal_inactive_contalink += 1

                            if won_time < won_age:
                                won_age = won_time

                        user_assign_won = person_deal.get("asigned_user_id")

                    # --------------------------------------------------
                    # OPEN
                    # --------------------------------------------------
                    elif status == "OPEN":
                        pending_fussion_deals = True

                        if current_deal_id not in open_deals:
                            open_deals.append(current_deal_id)
                            user_assign_open = person_deal.get(
                                "asigned_user_id"
                            )
                            count_open_deal += 1

                        if oldest_open_deal is None:
                            oldest_open_deal = current_deal_id
                        else:
                            oldest_row = _query_one(
                                conn,
                                """
                                SELECT add_time
                                FROM system_utils.crm_deal
                                WHERE id = %s
                                """,
                                (oldest_open_deal,),
                            )
                            oldest_add_time = (
                                oldest_row.get("add_time")
                                if oldest_row
                                else None
                            )

                            person_deal_add_time = person_deal.get("add_time")
                            if (
                                person_deal_add_time is not None
                                and oldest_add_time is not None
                                and person_deal_add_time < oldest_add_time
                            ):
                                oldest_open_deal = current_deal_id

    # ------------------------------------------------------------------
    # Determinar el deal OPEN más antiguo y cuáles deben fusionarse.
    # ------------------------------------------------------------------
    if pending_fussion_deals:
        open_deals.append(deal.get("id"))

        oldest_row = _query_one(
            conn,
            """
            SELECT add_time
            FROM system_utils.crm_deal
            WHERE id = %s
            """,
            (oldest_open_deal,),
        )
        oldest_add_time = oldest_row.get("add_time") if oldest_row else None

        incoming_add_time = deal.get("add_time")
        if (
            incoming_add_time is not None
            and oldest_add_time is not None
            and incoming_add_time < oldest_add_time
        ):
            oldest_open_deal = deal.get("id")

        aux_open_deals = [
            item
            for item in open_deals
            if item != oldest_open_deal
        ]

    if oldest_open_deal is not None:
        stage_row = _query_one(
            conn,
            "SELECT stage_id FROM system_utils.crm_deal WHERE id = %s",
            (oldest_open_deal,),
        )
        oldest_stage_id = stage_row.get("stage_id") if stage_row else None

    # ------------------------------------------------------------------
    # Determinar la persona más nueva y personas a fusionar.
    # ------------------------------------------------------------------
    if pending_fussion_contacts:
        incoming_person_id = person.get("pipedrive_id")
        persons_to_merge.append(incoming_person_id)

        if newest_user_id is None or (
            incoming_person_id is not None
            and incoming_person_id > newest_user_id
        ):
            newest_user_id = incoming_person_id

        aux_persons_to_merge = [
            item
            for item in persons_to_merge
            if item != newest_user_id
        ]

    log(
        "COUNTS",
        {
            "won": count_won_deal,
            "recent_won": count_recent_won_deal,
            "active_cl": count_deal_active_contalink,
            "inactive_cl": count_deal_inactive_contalink,
            "lost": count_lost_deal,
            "open": count_open_deal,
            "pending_contacts": pending_fussion_contacts,
            "pending_deals": pending_fussion_deals,
        },
    )

    # ------------------------------------------------------------------
    # Reglas de asignación.
    # El orden importa y replica los IF/ELSIF originales.
    # ------------------------------------------------------------------
    if count_won_deal > 0:
        # En PL/pgSQL son tres IF independientes, no ELSIF.
        if count_deal_active_contalink > 0:
            assignment_type = "redirect to support"
            user_result = _select_user_id_name_assigned_today(
                conn,
                email="gdelhoyo@tegik.com",
                require_auto_assignment=True,
            )

        if count_deal_inactive_contalink > 0:
            user_result = _select_user_id_name_assigned_today(
                conn,
                email="dianelis.garcia@contalink.com",
                require_auto_assignment=False,
            )
            assignment_type = "reactivate Dianelis"

        if (
            count_recent_won_deal > 0
            or (
                count_deal_active_contalink == 0
                and count_deal_inactive_contalink == 0
            )
        ):
            user_result = _select_user_id_name_assigned_today(
                conn,
                email="gdelhoyo@tegik.com",
                require_auto_assignment=True,
            )
            assignment_type = "revision Gloria"

    elif (
        count_open_deal > 0
        and oldest_stage_id is not None
        and oldest_stage_id != 249
    ):
        oldest_deal_row = _query_one(
            conn,
            """
            SELECT asigned_user_id
            FROM system_utils.crm_deal
            WHERE id = %s
            """,
            (oldest_open_deal,),
        )
        oldest_user_id = (
            oldest_deal_row.get("asigned_user_id")
            if oldest_deal_row
            else None
        )
        user_result = _get_crm_user(conn, oldest_user_id)
        assignment_type = "Open deal fussion and notify"

    elif count_open_deal > 0 and oldest_stage_id == 249:
        user_result = _select_random_open_stage_249_user(conn)
        assignment_type = "Open deal fussion and assign"

    elif count_lost_deal == 1:
        # Un único LOST siempre regresa con el agente que lo perdió,
        # independientemente de la etapa en la que se haya cerrado.
        user_result = _get_crm_user(conn, user_assign_lost)
        assignment_type = "redirect to last assignment"

    elif count_lost_deal > 1:
        # Dos o más LOST entran exactamente a la misma ronda utilizada
        # por una asignación normal.
        user_result = _select_random_user(conn)
        assignment_type = "random assignment"

    elif not person_has_valid_contact_information:
        user_result = _select_user_id_name_assigned_today(
            conn,
            email="yaneth.olivo@contalink.com",
            require_auto_assignment=True,
        )
        assignment_type = "bad contact information Hiram"

    else:
        user_result = _select_random_user(conn)
        assignment_type = "random assignment"


    # ------------------------------------------------------------------
    # Validación final del usuario asignado.
    #
    # El usuario pudo haber sido seleccionado por cualquier regla:
    # WON, OPEN, LOST, etc.
    #
    # Si ya no está activo en crm_users, hacemos una asignación
    # random normal y cambiamos el escenario.
    # ------------------------------------------------------------------

    assigned_user_id = (
        user_result.get("id")
        if user_result
        else None
    )

    if not _is_crm_user_active(
        conn,
        assigned_user_id,
    ):
        log(
            "INVALID_ASSIGNED_USER",
            {
                "user_id": assigned_user_id,
                "previous_assignment_type": assignment_type,
            },
        )

        user_result = _select_random_user(conn)

        assignment_type = "random_invalid_user"




    # ------------------------------------------------------------------
    # Special Assignment to new lite deals from demo.
    # En la función actual todo el código de esta rama está comentado,
    # por lo tanto no se hace nada.
    # ------------------------------------------------------------------
    if assignment_type == "random assignment":
        title = deal.get("title") or ""
        if "(Lite)" in title:
            pass

    # ------------------------------------------------------------------
    # Límite de merges.
    # ------------------------------------------------------------------
    if aux_persons_to_merge and len(aux_persons_to_merge) > 10:
        return None

    if aux_open_deals and len(aux_open_deals) > 10:
        return None

    result = {
        "user": _to_json_compatible(user_result),
        "assignment_type": assignment_type,
        "peding_contacts": pending_fussion_contacts,
        "person_id": newest_user_id,
        "person_to_merge": aux_persons_to_merge or None,
        "peding_deals": pending_fussion_deals,
        "oldest_stage": oldest_stage_id,
        "oldest_deal": oldest_open_deal,
        "open_deals": aux_open_deals or None,
    }

    log("RESULT", result)
    return result
