import os
import pathlib
import ssl


COMMON_CA_BUNDLES = (
    # Arch / CachyOS
    "/etc/ca-certificates/extracted/tls-ca-bundle.pem",
    # Debian / Ubuntu and many others
    "/etc/ssl/certs/ca-certificates.crt",
    # Fedora / RHEL
    "/etc/pki/tls/certs/ca-bundle.crt",
    "/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem",
    # Alpine
    "/etc/ssl/cert.pem",
)


def create_verified_ssl_context():
    # Respect explicit user/system overrides first.
    for variable in (
        "SSL_CERT_FILE",
        "REQUESTS_CA_BUNDLE",
        "CURL_CA_BUNDLE",
    ):
        value = os.environ.get(variable)

        if (
            value
            and pathlib.Path(value).is_file()
        ):
            return ssl.create_default_context(
                cafile=value
            )

    # certifi is optional. Use it when it exists in a packaged build.
    try:
        import certifi

        bundle = certifi.where()

        if (
            bundle
            and pathlib.Path(bundle).is_file()
        ):
            return ssl.create_default_context(
                cafile=bundle
            )

    except (
        ImportError,
        OSError,
    ):
        pass

    # PyInstaller builds on Arch/CachyOS can sometimes fail to discover
    # the host certificate bundle automatically. Try known system paths.
    for candidate in COMMON_CA_BUNDLES:
        if pathlib.Path(candidate).is_file():
            return ssl.create_default_context(
                cafile=candidate
            )

    # Final fallback uses Python/OpenSSL's normal discovery.
    return ssl.create_default_context()
