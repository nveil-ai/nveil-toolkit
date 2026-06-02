# SPDX-FileCopyrightText: 2026 NVEIL SAS
# SPDX-FileContributor: Pierre Jacquet
# SPDX-FileContributor: Guillaume Franque
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for engine serialization (dive._engine)."""

import pytest
from dive._engine import _serialize, _deserialize, _serialize_b64, _deserialize_b64


class TestEngineRoundtrip:
    def test_roundtrip(self):
        payload = {"visuspec_xml": "<v/>", "choregraph_xml": "<c/>"}
        blob = _serialize(payload)
        assert isinstance(blob, bytes)
        assert _deserialize(blob) == payload

    def test_roundtrip_unicode(self):
        payload = {"label": "données françaises"}
        assert _deserialize(_serialize(payload)) == payload

    def test_roundtrip_empty(self):
        assert _deserialize(_serialize({})) == {}


class TestEngineBase64:
    def test_roundtrip(self):
        payload = {"key": "value"}
        b64 = _serialize_b64(payload)
        assert isinstance(b64, str)
        assert _deserialize_b64(b64) == payload
