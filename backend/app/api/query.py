from app.services.common import parse_id


def optional_id(args, name):
    value = args.get(name)
    return parse_id(value, name) if value not in (None, "") else None


def limit_arg(args, default=100, maximum=100):
    value = args.get("limit")
    if value in (None, ""):
        return default
    limit = parse_id(value, "limit")
    return min(limit, maximum)
