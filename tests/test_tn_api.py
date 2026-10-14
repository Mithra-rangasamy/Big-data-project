import requests

def test_tamilnadu_districts():
    res = requests.get('http://localhost:5000/api/tamilnadu/districts')
    assert res.status_code == 200
    data = res.json()
    assert data['status'] == 'success'
    assert data['state'] == 'Tamil Nadu'
    assert data['total_districts'] == 30
    assert len(data['districts']) == 30
    for d in data['districts']:
        assert 'district_name' in d
        assert 'risk_score' in d
        assert 'risk_level' in d
        assert 'avg_aqi' in d
