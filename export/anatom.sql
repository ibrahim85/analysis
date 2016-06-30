CREATE TABLE tmp_eng_export AS (
    SELECT
        answer.id,
        answer.user_id AS user,
        COALESCE(answer.item_asked_id = item_answered_id, FALSE) AS correct,
        answer.time,
        answer.context_id AS context,
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
    LEFT JOIN proso_configab_answerexperimentsetup AS config
        ON answer.id = config.answer_id
    ORDER BY time
);

\copy tmp_eng_export TO '/tmp/eng_export.csv' DELIMITER ';' CSV HEADER;

DROP TABLE tmp_eng_export;


CREATE TABLE tmp_eng_context AS (
	SELECT id, content AS name
	FROM proso_models_practicecontext
);

\copy tmp_eng_context TO '/tmp/tmp_eng_context.csv' DELIMITER ';' CSV HEADER;

DROP TABLE tmp_eng_context;
