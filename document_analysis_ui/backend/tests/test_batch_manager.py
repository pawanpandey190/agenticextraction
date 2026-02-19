import pytest
from uuid import uuid4
from datetime import datetime
from app.services.batch_manager import BatchManager, BatchUpload
from app.models.session import Session, SessionStatus

@pytest.fixture
def batch_manager():
    return BatchManager()

@pytest.fixture
def mock_sessions():
    return [
        Session(id=str(uuid4()), status=SessionStatus.COMPLETED),
        Session(id=str(uuid4()), status=SessionStatus.COMPLETED),
        Session(id=str(uuid4()), status=SessionStatus.COMPLETED),
    ]

def test_batch_upload_status_completed(mock_sessions):
    batch = BatchUpload("test-batch", [s.id for s in mock_sessions])
    assert batch.get_status(mock_sessions) == "completed"

def test_batch_upload_status_failed():
    sessions = [
        Session(id=str(uuid4()), status=SessionStatus.FAILED),
        Session(id=str(uuid4()), status=SessionStatus.FAILED),
    ]
    batch = BatchUpload("test-batch", [s.id for s in sessions])
    assert batch.get_status(sessions) == "failed"

def test_batch_upload_status_processing():
    sessions = [
        Session(id=str(uuid4()), status=SessionStatus.COMPLETED),
        Session(id=str(uuid4()), status=SessionStatus.PROCESSING),
    ]
    batch = BatchUpload("test-batch", [s.id for s in sessions])
    assert batch.get_status(sessions) == "processing"

def test_batch_upload_status_partial_failure():
    sessions = [
        Session(id=str(uuid4()), status=SessionStatus.COMPLETED),
        Session(id=str(uuid4()), status=SessionStatus.FAILED),
    ]
    batch = BatchUpload("test-batch", [s.id for s in sessions])
    assert batch.get_status(sessions) == "partial_failure"

def test_batch_upload_count_by_status(mock_sessions):
    sessions = mock_sessions + [
        Session(id=str(uuid4()), status=SessionStatus.PROCESSING),
        Session(id=str(uuid4()), status=SessionStatus.FAILED),
    ]
    batch = BatchUpload("test-batch", [s.id for s in sessions])
    counts = batch.count_by_status(sessions)
    
    assert counts["completed"] == 3
    assert counts["processing"] == 1
    assert counts["failed"] == 1
    assert counts["created"] == 0

def test_batch_manager_create_batch(batch_manager):
    session_ids = [str(uuid4()), str(uuid4())]
    batch = batch_manager.create_batch(session_ids)
    
    assert batch.batch_id in batch_manager._batches
    assert batch.total_students == 2
    assert batch.student_sessions == session_ids

def test_batch_manager_get_batch(batch_manager):
    session_ids = [str(uuid4())]
    created_batch = batch_manager.create_batch(session_ids)
    
    retrieved_batch = batch_manager.get_batch(created_batch.batch_id)
    assert retrieved_batch == created_batch
    
    assert batch_manager.get_batch("non-existent") is None

def test_batch_manager_delete_batch(batch_manager):
    batch = batch_manager.create_batch([str(uuid4())])
    batch_id = batch.batch_id
    
    assert batch_manager.delete_batch(batch_id) is True
    assert batch_manager.get_batch(batch_id) is None
    assert batch_manager.delete_batch(batch_id) is False
