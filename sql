-- ============================
-- COMPANIES
-- ============================

create table companies (
  -- Internal unique identifier for the company (never exposed to users)
  id uuid primary key default gen_random_uuid(),

  -- Human-readable company name (display / UI / reporting only)
  -- NOT used for identity or uniqueness
  name text not null,

  -- Email domain used as the TRUE company identity using indexing on this for uniqueness
  -- Example: "restorationhardware.com"
  -- This allows deterministic company matching across users
  company_domain text,

  -- Optional industry classification (free-text or later enum)
  -- Used for agent context, NOT for logic branching
  industry_code text,
  base_currency text not null default 'INR',

  -- Month number (1–12) when the fiscal year starts
  -- Example: 4 = April (India), 1 = January (US)
  fiscal_year_start_month int not null default 1,
  created_at timestamp default now()
);

add constraint company_domain_not_empty
check (company_domain is null or length(company_domain) > 0);
create unique index companies_company_domain_unique
on companies (company_domain);

-- ============================
--  FINANCIAL PERIODS
-- ============================

create table financial_periods (
  id uuid primary key default gen_random_uuid(),
  company_id uuid not null references companies(id) on delete cascade,
  period_start date not null,
  period_end date not null,
  period_type text not null check (period_type in ('month', 'quarter', 'year')),
  fiscal_year int not null,
  fiscal_quarter int,
  created_at timestamp default now(),
  is_adjustment_period boolean default false,
  unique (company_id, period_start, period_type)
);

-- ============================
--  STATEMENT TYPES
-- ============================

create table statement_types (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  description text
);

insert into statement_types (name, description) values
  ('P&L', 'Profit and Loss Statement'),
  ('Balance Sheet', 'Assets, liabilities, equity'),
  ('Cash Flow', 'Cash inflows and outflows'),
  ('KPI', 'Operational and financial KPIs');

-- ============================
-- METRIC DEFINITIONS
-- ============================

create table metric_definitions (
  id uuid primary key default gen_random_uuid(),
  metric_key text not null unique,
  display_name text not null,
  statement_type_id uuid not null references statement_types(id),
  unit text,              -- currency, %, days, ratio
  polarity text,          -- higher_is_better / lower_is_better
  is_derived boolean default false,
  description text,
  industry_tags text[],
  aggregation_type text check (aggregation_type in ('sum','avg','ratio','last')),
  metric_category text,
  created_at timestamp default now()
);

-- ============================
-- FINANCIAL FACTS
-- ============================

create table financial_facts (
  id uuid primary key default gen_random_uuid(),
  company_id uuid not null references companies(id) on delete cascade,
  period_id uuid not null references financial_periods(id) on delete cascade,
  metric_id uuid not null references metric_definitions(id),
  value numeric,
  source_system text,
  confidence_score float,
  created_at timestamp default now(),
  unique (company_id, period_id, metric_id)
);

-- ============================
-- VALIDATION ISSUES
-- ============================

create table validation_issues (
  id uuid primary key default gen_random_uuid(),
  company_id uuid not null references companies(id) on delete cascade,
  period_id uuid references financial_periods(id),
  metric_id uuid references metric_definitions(id),
  issue_type text not null,
  severity text not null check (severity in ('low', 'medium', 'high')),
  description text,
  detected_at timestamp default now(),
  is_resolved boolean default false,
  resolved_at timestamp

);

-- ============================
-- FINANCIAL SUMMARIES
-- ============================

create table financial_summaries (
  id uuid primary key default gen_random_uuid(),
  company_id uuid not null references companies(id) on delete cascade,
  period_id uuid references financial_periods(id),
  summary_type text not null,
  content text not null,
  created_at timestamp default now()
);
-- Enforce idempotency for summaries
create unique index financial_summaries_unique
on financial_summaries (company_id, period_id, summary_type); --1 summary per(company_id, period_id, summary_type)

-- ============================
-- SUMMARY EMBEDDINGS
-- ============================

create table summary_embeddings (
  id uuid primary key default gen_random_uuid(),
  summary_id uuid not null references financial_summaries(id) on delete cascade,
  embedding vector(1536),
  created_at timestamp default now()
);

create table source_documents (
  -- Internal identifier for this upload/job
  id uuid primary key default gen_random_uuid(),

  -- Company that owns this document
  company_id uuid not null references companies(id) on delete cascade,

  -- Type of source (csv, excel, zoho, tally, pdf, api)
  source_type text not null,

  -- Original filename or system name (for display/debug only)
  source_name text,

  -- SHA256 hash of file contents (TRUE identity of the file)
  file_hash text not null,

  -- Ingestion lifecycle status (pipeline progress)
  ingestion_status text not null default 'uploaded',

  -- Step at which ingestion failed (if any)
  ingestion_step text,

  -- Human-readable error message (safe to show user)
  ingestion_error text,

  -- When this file was last processed (for retries/debug)
  last_processed_at timestamp,

  -- Arbitrary metadata (sheet names, row counts, etc.)
  metadata jsonb,

  -- Audit timestamp
  uploaded_at timestamp default now(),

  -- Prevent duplicate uploads of the same file for the same company
  unique (company_id, file_hash)
);

