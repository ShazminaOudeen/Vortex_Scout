-- Run in Supabase: SQL Editor -> New query -> paste -> Run.
-- Extends the dev guide's 4 tables with stores, store_id/unit_price on
-- transactions (the ingest endpoint sends them) and an audit_log table.

create table if not exists stores (
  id text primary key,
  name text not null
);

create table if not exists skus (
  id text primary key,
  barcode text unique not null,
  name text not null,
  category text not null,
  aisle text not null,
  bay text not null,
  ledger_stock integer not null default 0,
  unit_cost numeric(10,2) not null default 0,
  unit_price numeric(10,2) not null default 0
);

create table if not exists pos_transactions (
  id bigserial primary key,
  store_id text not null references stores(id),
  sku_id text not null references skus(id),
  ts timestamptz not null,
  quantity_sold integer not null check (quantity_sold > 0),
  unit_price numeric(10,2) not null
);
create index if not exists idx_pos_sku_ts on pos_transactions (sku_id, ts desc);

create table if not exists hourly_velocity (
  store_id text not null references stores(id),
  sku_id text not null references skus(id),
  hour timestamptz not null,
  units integer not null default 0,
  primary key (store_id, sku_id, hour)
);

create table if not exists stockout_anomalies (
  id uuid primary key default gen_random_uuid(),
  store_id text not null references stores(id),
  sku_id text not null references skus(id),
  p_void numeric(4,3) not null check (p_void between 0 and 1),
  hours_since_last_sale numeric(6,1),
  ledger_stock_at_detection integer,
  status text not null default 'open'
    check (status in ('open','restocked','damaged','false_alarm')),
  detected_at timestamptz not null default now(),
  resolved_at timestamptz
);
create index if not exists idx_anom_status on stockout_anomalies (status, detected_at desc);

create table if not exists audit_log (
  id bigserial primary key,
  anomaly_id uuid not null references stockout_anomalies(id),
  action text not null check (action in ('restocked','damaged','false_alarm')),
  associate text,
  units integer,
  created_at timestamptz not null default now()
);
