"""CPU file glue only. No build, model launch, exporter or collector command."""
import argparse
import json
from pathlib import Path

from exposedpath import native_llama as native


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest='action',required=True)
    patch=commands.add_parser('patch-backend')
    patch.add_argument('--source',required=True,type=Path);patch.add_argument('--output',required=True,type=Path)
    prepare=commands.add_parser('prepare')
    for name in ('identity','build','conversion','tokens','gpu','output'):
        prepare.add_argument('--'+name,required=True,type=Path)
    inspect=commands.add_parser('inspect-producer')
    inspect.add_argument('--spec',required=True,type=Path);inspect.add_argument('--producer',required=True,type=Path)
    review=commands.add_parser('review')
    for name in ('canonical','spec','producer','sqlite','preflight','raw','output'):
        review.add_argument('--'+name,required=True,type=Path)
    args=parser.parse_args(argv)
    if args.action=='patch-backend':value=native.instrument_backend(args.source,args.output)
    elif args.action=='prepare':
        value=str(native.prepare_run(args.output,identity=native._read(args.identity),
            build_receipt=args.build,conversion_receipt=args.conversion,token_input=args.tokens,
            expected_gpu=native._read(args.gpu)))
    elif args.action=='inspect-producer':value=native.read_producer(args.spec,args.producer)
    else:
        from exposedpath_v141.native_llama_scope import write_review
        value=str(write_review(args.canonical,args.spec,args.producer,args.sqlite,args.preflight,args.raw,args.output))
    print(json.dumps(value,ensure_ascii=False))
    return 0


if __name__=='__main__':raise SystemExit(main())
