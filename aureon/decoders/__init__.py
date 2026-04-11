"""Aureon decoder modules — hermetic-to-computational translation layer.

Each decoder translates one civilisation's encoded transmission into a
geographic vector. ``grail_convergence`` combines all vectors across four
relay layers to triangulate the convergence point.

Quick imports::

    from aureon.decoders import (
        AztecDecoder, SumerianDecoder, CelticOghamDecoder,
        EgyptianDecoder, IChingDecoder, JapaneseDecoder,
        MayaDecoder, MingJapanDecoder, MogollonDecoder,
    )
    from aureon.decoders.emerald_spec import map_geometric_pattern
    from aureon.decoders.grail_convergence import triangulate
    from aureon.decoders.maeshowe_seer_decode import OracleMaeshowe
"""

from aureon.decoders.aztec_decoder import AztecDecoder
from aureon.decoders.book_of_ur import (
    SumerianDecoder,
    get_sumerian_decoder,
    get_sumerian_geographic_vector,
)
from aureon.decoders.celtic_ogham import CelticOghamDecoder
from aureon.decoders.egyptian_decoder import EgyptianDecoder
from aureon.decoders.iching_decoder import (
    IChingDecoder,
    get_iching_decoder,
    get_iching_geographic_vector,
)
from aureon.decoders.japanese_decoder import JapaneseDecoder
from aureon.decoders.maya_decoder import MayaDecoder
from aureon.decoders.ming_japan_decoder import MingJapanDecoder
from aureon.decoders.mogollon_decoder import MogollonDecoder

__all__ = [
    # Civilizational decoders
    "AztecDecoder",
    "CelticOghamDecoder",
    "EgyptianDecoder",
    "IChingDecoder",
    "JapaneseDecoder",
    "MayaDecoder",
    "MingJapanDecoder",
    "MogollonDecoder",
    "SumerianDecoder",
    # Convenience factory functions
    "get_iching_decoder",
    "get_iching_geographic_vector",
    "get_sumerian_decoder",
    "get_sumerian_geographic_vector",
]
