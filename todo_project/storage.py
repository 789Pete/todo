from whitenoise.storage import CompressedManifestStaticFilesStorage


class StaticFilesStorage(CompressedManifestStaticFilesStorage):
    # Don't error on missing sourcemap files referenced by vendored JS/CSS
    manifest_strict = False
