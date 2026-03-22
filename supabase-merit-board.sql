-- 在 Supabase SQL Editor 运行此文件

-- 加道名字段
alter table public.member_profiles add column if not exists dao_name text;

-- 功德榜表（首页功德榜从这里读，方便后台随时改）
create table if not exists public.merit_board (
  id uuid primary key default gen_random_uuid(),
  display_name text not null,
  merit_amount integer not null default 0,
  sort_order integer default 0,
  is_visible boolean default true,
  created_at timestamptz default now()
);

alter table public.merit_board enable row level security;

-- 所有人可以读（首页公开显示）
drop policy if exists "merit_board_select_all" on public.merit_board;
create policy "merit_board_select_all"
on public.merit_board
for select
using (true);
