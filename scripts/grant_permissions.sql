-- Change ownership of tables to postgres user
ALTER TABLE documents OWNER TO postgres;
ALTER TABLE conversations OWNER TO postgres;
ALTER TABLE chunks OWNER TO postgres;
ALTER TABLE document_tags OWNER TO postgres;
ALTER TABLE tags OWNER TO postgres;
ALTER TABLE messages OWNER TO postgres;
ALTER TABLE citations OWNER TO postgres;
ALTER TABLE processing_jobs OWNER TO postgres;
ALTER TABLE analytics_queries OWNER TO postgres;
ALTER TABLE background_tasks OWNER TO postgres;
ALTER TABLE folders OWNER TO postgres;

-- Change ownership of sequences (if any)
DO $$
DECLARE
    seq_name text;
BEGIN
    FOR seq_name IN SELECT sequence_name FROM information_schema.sequences WHERE sequence_schema = 'public'
    LOOP
        EXECUTE 'ALTER SEQUENCE ' || seq_name || ' OWNER TO postgres';
    END LOOP;
END $$;

-- Grant permissions on sequences (if any)
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;