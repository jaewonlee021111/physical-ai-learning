-- CI 전용: Supabase 호환 역할을 갖춘 일회성 PostgreSQL에서 실행한다.
\set ON_ERROR_STOP on
begin;
insert into public.lab_devices(id,key_hash) values
('00000000-0000-0000-0000-000000000001',extensions.digest('test-capability-key-device-one-only','sha256')),
('00000000-0000-0000-0000-000000000002',extensions.digest('test-capability-key-device-two-only','sha256'));
set local role anon;
do $$
declare result jsonb;
begin
  result:=public.lab_read('00000000-0000-0000-0000-000000000001','test-capability-key-device-one-only');
  if result->>'desired' <> 'false' then raise exception 'initial state failed'; end if;
  perform public.lab_set_led('00000000-0000-0000-0000-000000000001','test-capability-key-device-one-only',true);
  perform public.lab_report('00000000-0000-0000-0000-000000000001','test-capability-key-device-one-only',true,12345);
  result:=public.lab_read('00000000-0000-0000-0000-000000000001','test-capability-key-device-one-only');
  if result->>'desired' <> 'true' or result->>'touched' <> 'true' or result->>'raw' <> '12345' or result->>'reported_at' is null then
    raise exception 'command/report roundtrip failed';
  end if;
  begin
    perform public.lab_read('00000000-0000-0000-0000-000000000001','wrong-key');
    raise exception 'test failed: wrong key accepted';
  exception when raise_exception then
    if sqlerrm <> 'invalid device capability' then raise; end if;
  end;
  begin
    perform public.lab_set_led('00000000-0000-0000-0000-000000000002','test-capability-key-device-one-only',true);
    raise exception 'test failed: cross-device write accepted';
  exception when raise_exception then
    if sqlerrm <> 'invalid device capability' then raise; end if;
  end;
  begin
    perform public.lab_report('00000000-0000-0000-0000-000000000001','test-capability-key-device-one-only',false,-1);
    raise exception 'test failed: negative raw accepted';
  exception when raise_exception then
    if sqlerrm <> 'invalid raw value' then raise; end if;
  end;
  begin
    perform public.lab_report('00000000-0000-0000-0000-000000000001','test-capability-key-device-one-only',false,4294967296);
    raise exception 'test failed: overflow raw accepted';
  exception when raise_exception then
    if sqlerrm <> 'invalid raw value' then raise; end if;
  end;
  begin
    perform 1 from public.lab_devices;
    raise exception 'test failed: direct table read accepted';
  exception when insufficient_privilege then null;
  end;
  begin
    update public.lab_devices set desired=true;
    raise exception 'test failed: direct table update accepted';
  exception when insufficient_privilege then null;
  end;
end; $$;
reset role;
rollback;
\echo 'PASS: RPC roundtrip, invalid key, device isolation, raw bounds, direct access denied'
