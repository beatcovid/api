
def skip_site_packages_logs(record):
    # type: (logging.LogRecord) -> bool
    # This skips the log records that are generated from libraries
    # installed in site packages.
    if 'site-packages' in record.pathname:
        return False
    return True
