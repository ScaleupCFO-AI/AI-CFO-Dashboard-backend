-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE public.companies (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  name text NOT NULL,
  industry_code text,
  base_currency text NOT NULL DEFAULT 'INR'::text,
  fiscal_year_start_month integer NOT NULL DEFAULT 1,
  created_at timestamp without time zone DEFAULT now(),
  company_domain text CHECK (company_domain IS NULL OR length(company_domain) > 0),
  CONSTRAINT companies_pkey PRIMARY KEY (id)
);
CREATE TABLE public.financial_facts (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  company_id uuid NOT NULL,
  period_id uuid NOT NULL,
  metric_id uuid NOT NULL,
  value numeric,
  source_system text,
  confidence_score double precision,
  created_at timestamp without time zone DEFAULT now(),
  CONSTRAINT financial_facts_pkey PRIMARY KEY (id),
  CONSTRAINT financial_facts_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id),
  CONSTRAINT financial_facts_period_id_fkey FOREIGN KEY (period_id) REFERENCES public.financial_periods(id),
  CONSTRAINT financial_facts_metric_id_fkey FOREIGN KEY (metric_id) REFERENCES public.metric_definitions(id)
);
CREATE TABLE public.financial_periods (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  company_id uuid NOT NULL,
  period_start date NOT NULL,
  period_end date NOT NULL,
  period_type text NOT NULL CHECK (period_type = ANY (ARRAY['month'::text, 'quarter'::text, 'year'::text])),
  fiscal_year integer NOT NULL,
  fiscal_quarter integer,
  created_at timestamp without time zone DEFAULT now(),
  is_adjustment_period boolean DEFAULT false,
  fiscal_month integer,
  CONSTRAINT financial_periods_pkey PRIMARY KEY (id),
  CONSTRAINT financial_periods_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id)
);
CREATE TABLE public.financial_summaries (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  company_id uuid NOT NULL,
  period_id uuid,
  summary_type text NOT NULL,
  content text NOT NULL,
  created_at timestamp without time zone DEFAULT now(),
  CONSTRAINT financial_summaries_pkey PRIMARY KEY (id),
  CONSTRAINT financial_summaries_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id),
  CONSTRAINT financial_summaries_period_id_fkey FOREIGN KEY (period_id) REFERENCES public.financial_periods(id)
);
CREATE TABLE public.metric_definitions (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  metric_key text NOT NULL UNIQUE,
  display_name text NOT NULL,
  statement_type_id uuid NOT NULL,
  unit text,
  polarity text,
  is_derived boolean DEFAULT false,
  description text,
  industry_tags ARRAY,
  aggregation_type text CHECK (aggregation_type = ANY (ARRAY['sum'::text, 'avg'::text, 'ratio'::text, 'last'::text])),
  metric_category text,
  created_at timestamp without time zone DEFAULT now(),
  allowed_grains ARRAY NOT NULL DEFAULT '{}'::text[],
  CONSTRAINT metric_definitions_pkey PRIMARY KEY (id),
  CONSTRAINT metric_definitions_statement_type_id_fkey FOREIGN KEY (statement_type_id) REFERENCES public.statement_types(id)
);
CREATE TABLE public.source_documents (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  company_id uuid NOT NULL,
  source_type text NOT NULL,
  source_name text,
  file_hash text NOT NULL,
  ingestion_status text NOT NULL DEFAULT 'uploaded'::text,
  ingestion_step text,
  ingestion_error text,
  last_processed_at timestamp without time zone,
  metadata jsonb,
  uploaded_at timestamp without time zone DEFAULT now(),
  CONSTRAINT source_documents_pkey PRIMARY KEY (id),
  CONSTRAINT source_documents_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id)
);
CREATE TABLE public.statement_types (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  name text NOT NULL UNIQUE,
  description text,
  CONSTRAINT statement_types_pkey PRIMARY KEY (id)
);
CREATE TABLE public.summary_embeddings (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  summary_id uuid NOT NULL,
  embedding USER-DEFINED,
  created_at timestamp without time zone DEFAULT now(),
  CONSTRAINT summary_embeddings_pkey PRIMARY KEY (id),
  CONSTRAINT summary_embeddings_summary_id_fkey FOREIGN KEY (summary_id) REFERENCES public.financial_summaries(id)
);
CREATE TABLE public.validation_issues (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  company_id uuid NOT NULL,
  period_id uuid,
  metric_id uuid,
  issue_type text NOT NULL,
  severity text NOT NULL CHECK (severity = ANY (ARRAY['info'::text, 'low'::text, 'medium'::text, 'high'::text, 'critical'::text])),
  description text,
  detected_at timestamp without time zone DEFAULT now(),
  is_resolved boolean DEFAULT false,
  resolved_at timestamp without time zone,
  CONSTRAINT validation_issues_pkey PRIMARY KEY (id),
  CONSTRAINT validation_issues_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id),
  CONSTRAINT validation_issues_period_id_fkey FOREIGN KEY (period_id) REFERENCES public.financial_periods(id),
  CONSTRAINT validation_issues_metric_id_fkey FOREIGN KEY (metric_id) REFERENCES public.metric_definitions(id)
);