from backend.scripts.mongodb.backfill_document_subject_employee import parse_args, run


if __name__ == "__main__":
    args = parse_args()
    import asyncio
    import json

    result = asyncio.run(run(document_id=args.document_id, dry_run=args.dry_run))
    print(json.dumps(result, indent=2))
