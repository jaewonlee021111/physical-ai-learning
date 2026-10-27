-- 사용자 Supabase SQL Editor에서 실행할 실습 스키마. 이 파일만으로 외부 DB를 변경하지 않는다.
create schema if not exists extensions;
create extension if not exists pgcrypto with schema extensions;

create table if not exists public.lab_devices (
  id uuid primary key,
  key_hash bytea not null,
  desired boolean not null default false,
  touched boolean not null default false,
  raw_value bigint not null default 0,
  reported_at timestamptz
);
alter table public.lab_devices enable row level security;
revoke all on public.lab_devices from anon, authenticated;

-- 로그인 UI 없이도 장치별 capability key가 필요하다. anon에게 전체 테이블을 공개하지 않는다.
create or replace function public.lab_read(p_id uuid, p_key text)
returns jsonb language plpgsql security definer set search_path = '' as $$
declare result jsonb;
begin
  select jsonb_build_object('desired', desired, 'touched', touched,
                           'raw', raw_value, 'reported_at', reported_at)
    into result from public.lab_devices
    where id=p_id and key_hash=extensions.digest(p_key,'sha256');
  if result is null then raise exception 'invalid device capability'; end if;
  return result;
end; $$;

create or replace function public.lab_set_led(p_id uuid, p_key text, p_on boolean)
returns jsonb language plpgsql security definer set search_path = '' as $$
begin
  update public.lab_devices set desired=p_on
    where id=p_id and key_hash=extensions.digest(p_key,'sha256');
  if not found then raise exception 'invalid device capability'; end if;
  return jsonb_build_object('ok',true);
end; $$;

create or replace function public.lab_report(p_id uuid, p_key text, p_touch boolean, p_raw bigint)
returns jsonb language plpgsql security definer set search_path = '' as $$
begin
  if p_raw < 0 or p_raw > 4294967295 then raise exception 'invalid raw value'; end if;
  update public.lab_devices set touched=p_touch, raw_value=p_raw, reported_at=now()
    where id=p_id and key_hash=extensions.digest(p_key,'sha256');
  if not found then raise exception 'invalid device capability'; end if;
  return jsonb_build_object('ok',true);
end; $$;

revoke all on function public.lab_read(uuid,text) from public;
revoke all on function public.lab_set_led(uuid,text,boolean) from public;
revoke all on function public.lab_report(uuid,text,boolean,bigint) from public;
grant execute on function public.lab_read(uuid,text) to anon, authenticated;
grant execute on function public.lab_set_led(uuid,text,boolean) to anon, authenticated;
grant execute on function public.lab_report(uuid,text,boolean,bigint) to anon, authenticated;

-- 예: 로컬에서 secrets.token_urlsafe(32)로 만든 키의 SHA-256만 저장한다.
-- insert into public.lab_devices(id,key_hash)
-- values ('직접 생성한 UUID',extensions.digest('직접 생성한 32자 이상 키','sha256'));
-- service_role 키를 브라우저나 펌웨어에 넣지 않는다.
