-- After a load (sample-service ADR 0024): the location triggers are back on and the location log agrees with the
-- columns. Run with ON_ERROR_STOP so that a failure fails `make verify`.
DO $$
DECLARE
    v_enabled integer;
    v_gaps    integer;
BEGIN
    SELECT count(*) INTO v_enabled FROM pg_trigger
    WHERE tgname IN ('location_event_sample_trigger', 'location_event_container_trigger') AND tgenabled = 'O';
    IF v_enabled <> 2 THEN
        RAISE EXCEPTION 'The location triggers are not both enabled (%/2): a load stopped half-way. ALTER TABLE sample.sample ENABLE TRIGGER location_event_sample_trigger; ALTER TABLE sample.container ENABLE TRIGGER location_event_container_trigger;', v_enabled;
    END IF;
    SELECT count(*) INTO v_gaps FROM sample.view_location_event_gaps;
    IF v_gaps > 0 THEN
        RAISE EXCEPTION 'The location log disagrees with the columns in % places (select * from sample.view_location_event_gaps)', v_gaps;
    END IF;
    RAISE NOTICE 'Location log OK: triggers enabled, no gaps';
END
$$;
