create extension if not exists vector;

create table if not exists knowledge_base (
  id text primary key,
  topic text not null,
  question text,
  answer text,
  intent text,
  content text,
  embedding vector(768),
  updated_at timestamptz default now()
);

alter table knowledge_base
  add column if not exists intent text;

create index if not exists knowledge_base_embedding_idx
  on knowledge_base
  using ivfflat (embedding vector_cosine_ops)
  with (lists = 100);

create or replace function match_knowledge(
  query_embedding vector(768),
  match_count int,
  match_threshold float
)
returns table (
  id text,
  topic text,
  question text,
  answer text,
  intent text,
  similarity float
)
language sql
stable
as $$
  select
    id,
    topic,
    question,
    answer,
    intent,
    1 - (embedding <=> query_embedding) as similarity
  from knowledge_base
  where 1 - (embedding <=> query_embedding) > match_threshold
  order by similarity desc
  limit match_count;
$$;
