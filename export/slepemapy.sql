CREATE TABLE tmp_eng_export AS (
    SELECT
        answer.id,
        answer.user_id AS user,
        COALESCE(answer.item_asked_id = item_answered_id, FALSE) AS correct,
        answer.time,
        context.name || ', ' || type.name AS context,
        hua.device_family != 'Other' AS touch_device,
        location.ip_address,
        config.experiment_setup_id AS experiment_id
    FROM proso_models_answer AS answer
    LEFT JOIN proso_user_session AS session
        ON session.id = answer.session_id
    LEFT JOIN proso_user_httpuseragent AS hua
        ON hua.id = session.http_user_agent_id
    LEFT JOIN proso_user_location AS location
        ON location.id = session.location_id
    INNER JOIN proso_models_itemrelation AS context_relation
        ON answer.item_asked_id = context_relation.child_id
    INNER JOIN proso_flashcards_context AS context
        ON context.item_id = context_relation.parent_id
        AND context.lang = 'en'
    INNER JOIN proso_models_itemrelation AS term_relation
        ON answer.item_asked_id = term_relation.child_id
    INNER JOIN proso_flashcards_term AS term
        ON term.item_id = term_relation.parent_id
        AND term.lang = 'en'
    INNER JOIN proso_models_itemrelation AS type_relation
        ON term.item_id = type_relation.child_id
    INNER JOIN proso_flashcards_category AS type
        ON type.item_id = type_relation.parent_id
        AND type.lang = 'en'
        AND type.type = 'flashcard_type'
    LEFT JOIN proso_configab_answerexperimentsetup AS config
        ON answer.id = config.answer_id
    ORDER BY time
);

\copy tmp_eng_export TO '/tmp/eng_export.csv' DELIMITER ';' CSV HEADER;

DROP TABLE tmp_eng_export;
