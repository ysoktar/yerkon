"""Where the ground and the buildings come from.

Three sources, one seam. A GeoTIFF on disk, an elevation service, and
OpenStreetMap all answer the same two questions: how high is the ground
here, and what is standing on it. The rest of the codebase asks a
:class:`~yerkon.site.model.Site` and never learns which source answered.

ADR-0008 keeps fetching and reading apart. Only :mod:`yerkon.site.fetch`
opens a socket, and it writes into a cache; everything else reads the
cache offline. That is what makes a run reproducible by someone else.
"""

from yerkon.site.model import Buildings, Site, SiteManifest
from yerkon.site.cache import SiteCache

__all__ = ["Buildings", "Site", "SiteCache", "SiteManifest"]
