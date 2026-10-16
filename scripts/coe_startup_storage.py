"""Fresh participating-volume resources only; never enumerates historical YLQ."""
import argparse
import ctypes
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import shutil
import stat
import uuid

VERSION='coe-startup-resources/0.1.0'
REQUIRED=12884901888


def safe_directory(path):
    p=Path(os.path.abspath(path))
    for q in (p,*p.parents):
        s=q.lstat()
        if stat.S_ISLNK(s.st_mode) or getattr(s,'st_file_attributes',0)&0x400:
            raise OSError('Reparse path: '+str(q))
    if not p.is_dir():raise NotADirectoryError(str(p))
    return p


def volume_identity(path):
    if os.name!='nt':return 'DEV:'+str(os.stat(path).st_dev)
    from ctypes import wintypes
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.GetVolumePathNameW.argtypes=[wintypes.LPCWSTR,wintypes.LPWSTR,wintypes.DWORD]
    k.GetVolumePathNameW.restype=wintypes.BOOL
    k.GetVolumeNameForVolumeMountPointW.argtypes=[wintypes.LPCWSTR,wintypes.LPWSTR,wintypes.DWORD]
    k.GetVolumeNameForVolumeMountPointW.restype=wintypes.BOOL
    mount=ctypes.create_unicode_buffer(32768);name=ctypes.create_unicode_buffer(32768)
    if not k.GetVolumePathNameW(str(path),mount,len(mount)):raise ctypes.WinError(ctypes.get_last_error())
    if not k.GetVolumeNameForVolumeMountPointW(mount.value,name,len(name)):raise ctypes.WinError(ctypes.get_last_error())
    return name.value.casefold()


def write_probe(directory):
    # Only this newly created, exclusive probe leaf is removed. Never evidence.
    p=directory/('.coe-write-probe-'+uuid.uuid4().hex)
    with p.open('xb') as f:f.write(b'COE_STARTUP_WRITE_PROBE');f.flush();os.fsync(f.fileno())
    p.unlink()


def check(output_directory,temporary_directories,archive):
    result=dict(schema_version=VERSION,status='STARTUP_RESOURCES_BLOCKED',
        utc=datetime.now(timezone.utc).isoformat(),locations=[],volumes=[],errors=[],
        temporary_required_bytes=REQUIRED,reservation_rule='EACH_DISTINCT_PARTICIPATING_VOLUME_NO_SUMMATION',
        historical_ylq_total_bytes=None,long_term_status='UNKNOWN_NOT_PROVEN',
        long_term_target_exclusive_bytes=50000000000,historical_walk_performed=False,
        acl_queried=False,automatic_cleanup=False,collection_authorized=False,
        new_output_guard='LAUNCHER_EXCLUSIVE_CREATE_AND_ARCHIVE_MUST_NOT_EXIST')
    archive=Path(archive)
    if archive.exists():result['errors'].append(dict(reason='ARCHIVE_ALREADY_EXISTS',path=str(archive)))
    places=[('output',Path(output_directory)),*[(f'temporary-{i}',Path(p)) for i,p in enumerate(temporary_directories)],('archive-parent',archive.parent)]
    if not temporary_directories:result['errors'].append(dict(reason='TEMPORARY_DIRECTORY_MISSING',path=None))
    volumes={};probed=set()
    for role,path in places:
        row=dict(role=role,path=str(path),writable='UNKNOWN',volume=None);result['locations'].append(row)
        try:path=safe_directory(path)
        except OSError as e:
            reason='TEMPORARY_DIRECTORY_MISSING' if role.startswith('temporary') and isinstance(e,FileNotFoundError) else 'PATH_UNAVAILABLE_OR_REPARSE'
            result['errors'].append(dict(reason=reason,path=str(path),type=type(e).__name__,message=str(e)));continue
        try:
            key=os.path.normcase(str(path))
            if key not in probed:write_probe(path);probed.add(key)
            row['writable']='OBSERVED'
        except OSError as e:result['errors'].append(dict(reason='PATH_NOT_WRITABLE',path=str(path),type=type(e).__name__,message=str(e)))
        try:identity=volume_identity(path);row['volume']=identity
        except OSError as e:
            result['errors'].append(dict(reason='VOLUME_IDENTITY_UNKNOWN',path=str(path),type=type(e).__name__,message=str(e)));continue
        if identity in volumes:continue
        value=dict(identity=identity,queried_at_path=str(path),status='UNKNOWN',free_bytes=None,total_bytes=None)
        volumes[identity]=value;result['volumes'].append(value)
        try:
            usage=shutil.disk_usage(path)
            if type(usage.free) is not int or usage.free<0:raise OSError('Invalid free-byte observation')
            value.update(status='OBSERVED',free_bytes=usage.free,total_bytes=usage.total)
            if usage.free<REQUIRED:result['errors'].append(dict(reason='FREE_SPACE_INSUFFICIENT',volume=identity,free_bytes=usage.free,required_bytes=REQUIRED))
        except OSError as e:result['errors'].append(dict(reason='FREE_SPACE_UNKNOWN',volume=identity,type=type(e).__name__,message=str(e)))
    if not result['errors']:result['status']='STARTUP_RESOURCES_READY'
    return result


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-directory',type=Path,required=True)
    p.add_argument('--temporary-directory',type=Path,action='append',required=True)
    p.add_argument('--archive',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True)
    a=p.parse_args(argv);value=check(a.output_directory,a.temporary_directory,a.archive)
    with a.receipt.open('x',encoding='utf8') as f:json.dump(value,f,indent=2)
    print(value['status']+':'+','.join(v['reason'] for v in value['errors']),flush=True)
    return 0 if value['status']=='STARTUP_RESOURCES_READY' else 2


if __name__=='__main__':raise SystemExit(main())
