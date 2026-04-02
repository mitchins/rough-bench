create table if not exists checkpoints (
    source text primary key,
    cursor text not null,
    updated_at text not null
);

create table if not exists items (
    item_id text primary key,
    payload text not null,
    seen_at text not null
);
