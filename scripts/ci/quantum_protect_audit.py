"""
================================================================================
 File: scripts/ci/quantum_protect_audit.py
 Purpose:
   Wrap a CI audit log in SmartCito's quantum-ready hybrid envelope so only the
   encrypted artifact needs to leave the CI runner.
================================================================================
"""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "citosmart"))

from app.schemas.quantum import HybridEnvelopeIn, PqcKemAlgorithm, QkdKeyImportIn
from app.services.quantum_security import quantum_security_service


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python3 scripts/ci/quantum_protect_audit.py <input> <output>")

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    plaintext = input_path.read_text()

    key_material = os.getenv("SMARTCITO_QKD_KEY_B64")
    if not key_material:
        key_material = base64.b64encode(os.urandom(32)).decode("utf-8")

    key_id = f"ci-audit-{uuid4()}"
    metadata = quantum_security_service.import_qkd_key(
        QkdKeyImportIn(
            key_id=key_id,
            source="ci-ephemeral-qkd",
            key_material_b64=key_material,
            metadata={"stage": os.getenv("GITHUB_JOB", "local")},
        )
    )
    envelope = quantum_security_service.create_hybrid_envelope(
        HybridEnvelopeIn(
            plaintext=plaintext,
            purpose="ci-audit-log",
            pqc_kem=PqcKemAlgorithm.ML_KEM_768,
            qkd_key_id=metadata.key_id,
            associated_data=os.getenv("GITHUB_SHA", "local"),
        )
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(
            {
                "source": str(input_path),
                "encrypted_at": os.getenv("GITHUB_RUN_ID", "local-run"),
                "qkd_key_id": metadata.key_id,
                "fingerprint": envelope.fingerprint,
                "ciphertext_b64": envelope.ciphertext_b64,
                "pqc_kem": envelope.pqc_kem.value,
            },
            indent=2,
        )
    )
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())