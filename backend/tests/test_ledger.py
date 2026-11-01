import json

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from sqlalchemy import delete, select, update

from app.core import audit_ledger as ledger
from app.db.models import LedgerEntry


def _fill(session, signer, n=4):
    for i in range(n):
        ledger.append_event(session, signer, "TEST", {"i": i}, "uji")
    session.commit()


def _verify(session, signer):
    return ledger.verify_chain(session, {signer.key_id: signer.public_key})


def test_empty_chain_is_valid(session, signer):
    result = _verify(session, signer)
    assert result.ok and result.entries == 0 and result.head_hash is None


def test_chain_verifies_and_reports_head(session, signer):
    _fill(session, signer)
    result = _verify(session, signer)
    last = session.scalars(select(LedgerEntry).order_by(LedgerEntry.seq.desc())).first()
    assert result.ok and result.entries == 4
    assert (result.head_seq, result.head_hash) == (last.seq, last.entry_hash)


def test_first_entry_links_to_genesis(session, signer):
    _fill(session, signer, 1)
    assert session.scalars(select(LedgerEntry)).one().prev_hash == ledger.GENESIS_HASH


def test_modified_body_is_detected(session, signer):
    _fill(session, signer)
    session.execute(update(LedgerEntry).where(LedgerEntry.seq == 2).values(body='{"x":1}'))
    session.commit()
    result = _verify(session, signer)
    assert not result.ok and result.bad_seq == 2 and "diubah" in result.reason


def test_deleted_entry_is_detected(session, signer):
    _fill(session, signer)
    session.execute(delete(LedgerEntry).where(LedgerEntry.seq == 2))
    session.commit()
    result = _verify(session, signer)
    assert not result.ok and result.bad_seq == 3 and "urut" in result.reason


def test_rehashing_after_edit_still_fails_without_the_signing_key(session, signer):
    """Penyerang dengan akses DB menghitung ulang semua hash, tetapi tak bisa menandatangani."""
    _fill(session, signer, 3)
    entries = list(session.scalars(select(LedgerEntry).order_by(LedgerEntry.seq)))
    forged = json.dumps({"event": "TEST", "actor": "palsu", "at": "x", "data": {}})
    prev = entries[0].entry_hash
    for e in entries[1:]:
        e.prev_hash = prev
        e.body = forged if e.seq == 2 else e.body
        e.entry_hash = ledger._entry_hash(e.prev_hash, e.body)
        prev = e.entry_hash
    session.commit()
    result = _verify(session, signer)
    assert not result.ok and result.bad_seq == 2 and "tanda tangan" in result.reason


def test_unknown_signing_key_is_rejected(session, signer):
    _fill(session, signer, 2)
    other = Ed25519PrivateKey.generate().public_key()
    result = ledger.verify_chain(session, {signer.key_id: other})
    assert not result.ok and result.bad_seq == 1 and "tanda tangan" in result.reason
    assert not ledger.verify_chain(session, {}).ok


def test_signer_persists_key_between_loads(tmp_path):
    path = tmp_path / "keys" / "k.pem"
    first = ledger.Signer.load_or_create(path)
    assert ledger.Signer.load_or_create(path).key_id == first.key_id


def test_sequence_has_no_gaps_after_a_rolled_back_transaction(session, signer):
    ledger.append_event(session, signer, "TEST", {}, "uji")
    session.commit()
    ledger.append_event(session, signer, "BATAL", {}, "uji")
    session.rollback()  # transaksi dibatalkan tidak boleh meninggalkan lubang nomor urut
    ledger.append_event(session, signer, "TEST", {}, "uji")
    session.commit()
    assert [e.seq for e in session.scalars(select(LedgerEntry).order_by(LedgerEntry.seq))] == [1, 2]
    assert _verify(session, signer).ok
