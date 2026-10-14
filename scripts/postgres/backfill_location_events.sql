-- Initial placements of the migrated samples and containers (sample-service ADR 0024 decision 11; owner decision
-- 2026-10-14: the location history is backfilled, not started empty).
--
-- The Makefile switches the location triggers off for the bulk load (a load-time event would carry the load time, not
-- the time the legacy row was created) and runs this script once the samples and containers are in. For every sample and
-- container that is placed and has no location event yet, it writes the first event: from nothing to where it is, under
-- the task SYSTEM-DEFAULT, at the time the row was created, linked to one MIGRATION row of the change log. Safe to run
-- again: rows that already have an event are skipped. Run as the migration user (a superuser or a member of audit_owner).
DO $$
DECLARE
    v_log  bigint;
    v_task bigint;
BEGIN
    SELECT id INTO v_task FROM sample.task WHERE name = 'SYSTEM-DEFAULT';
    IF v_task IS NULL THEN
        RAISE EXCEPTION 'The SYSTEM-DEFAULT task is missing; load-target creates it before the import';
    END IF;

    INSERT INTO common.transaction_change_reason (kind, reason, source_component, transaction_id, authid, userstamp)
    VALUES ('MIGRATION', 'sample-service-migration: backfill of initial placements', 'sample-service-migration',
            common.get_transaction_id(), session_user, session_user)
    RETURNING id INTO v_log;

    INSERT INTO sample.location_event (sample_id, to_container_id, to_placecode, task_id, event_time, txlog_id, actor, userstamp)
    SELECT s.id, s.container_id, s.placecode, v_task, s.created, v_log, 'migration', 'migration'
    FROM sample.sample s
    WHERE s.container_id IS NOT NULL
      AND NOT EXISTS (SELECT 1 FROM sample.location_event e WHERE e.sample_id = s.id);

    INSERT INTO sample.location_event (container_id, to_container_id, to_placecode, task_id, event_time, txlog_id, actor, userstamp)
    SELECT c.id, c.parent_container_id, c.placecode, v_task, c.created, v_log, 'migration', 'migration'
    FROM sample.container c
    WHERE c.parent_container_id IS NOT NULL
      AND NOT EXISTS (SELECT 1 FROM sample.location_event e WHERE e.container_id = c.id);
END
$$;
