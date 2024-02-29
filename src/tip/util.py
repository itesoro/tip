def parse_package_specifier(package_specifier: str) -> tuple[str, str]:
    """Parse package specifier into package name and package version."""
    try:
        name, version = package_specifier.split('==')
    except ValueError as ex:
        raise ValueError("Package specifier must be '<package_name>==<package_version>'") from ex
    return name, version
