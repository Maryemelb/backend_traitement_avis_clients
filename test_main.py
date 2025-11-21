from fastapi import Depends
from fastapi.testclient import TestClient
import pytest
from database import sessionLocal
from main import app
from schemas import CreateComment
@pytest.fixture
def token():
 return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJtYXJ5ZW1AZ21haWwuY29tIn0.2KUk2Qj0jn3Jo_8jN3d7kbXNZYtHL42pbNJg2pvotyk"
def getdb():
    db=sessionLocal()
    try:
        yield db
    finally:
        db.close
@pytest.fixture
def test_client():
    return TestClient(app)

def test_score_comment(test_client, token):
     
     payload= {
     "comment": "testing comment",
     "id_user": 1
      }
     headers= {
         "Authorization": f"Bearer {token}"

     }
     
     response = test_client.post('/predict', json=payload, headers= headers)
     score, user_id= response.json()

     assert response.status_code == 200
    #  assert max_score_label
     print(user_id)
     assert isinstance(score, str)
     