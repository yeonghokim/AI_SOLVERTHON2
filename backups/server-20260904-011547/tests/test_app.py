from fastapi.testclient import TestClient
import app as module
from app import app

client = TestClient(app)

def test_health_has_seeded_announcements():
    assert client.get('/api/health').json()['announcements'] >= 30

def test_empty_profile_does_not_become_ineligible():
    body = client.post('/api/matches', json={}).json()
    assert body['total'] == client.get('/api/health').json()['announcements']
    assert body['ineligible'] == 0
    assert body['items'][0]['fitStatus'] == 'UNAVAILABLE'
    assert body['items'][0]['fitScore'] is None
    assert body['items'][0]['fitMissingInfo']

def test_complete_fit_profile_returns_explained_score():
    body = client.post('/api/matches', json={
        'currentProblems': '생산 자동화와 해외 판로 확보',
        'supportPriorities': '설비 R&D 수출 마케팅',
        'businessGoals': '매출 확대와 신규 고용',
        'desiredSupportAmount': 100000000,
        'availableStaff': 3,
        'maxContribution': 30000000,
        'fundUsagePlan': '자동화 설비 도입과 해외 인증',
        'applicationIntent': '높음',
        'industry': '자동차 부품 제조',
        'products': '모빌리티 부품',
    }).json()
    item = body['items'][0]
    assert item['fitStatus'] == 'AVAILABLE'
    assert 0 <= item['fitScore'] <= 100
    assert len(item['fitReasons']) == 4

def test_clear_conflicts_become_ineligible():
    body = client.post('/api/matches', json={'operatingStatus':'폐업','sanctions':'있음'}).json()
    assert body['ineligible'] == body['total']

def test_demo_login_and_profile_are_ready():
    login = client.post('/api/auth/login', json={
        'email': 'admin@demo.local', 'password': 'demo1234'
    })
    assert login.status_code == 200
    assert login.json()['role'] == 'ADMIN'
    profile = client.get('/api/profile').json()
    assert profile['companyName'] == '그린모빌리티랩 주식회사'
    assert profile['operatingStatus'] == '계속사업'

def test_import_endpoint_analyzes_and_deduplicates(monkeypatch, tmp_path):
    monkeypatch.setattr(module, 'DB_PATH', tmp_path / 'announcements.db')
    module.initialize_database()
    item = {'pblancId':'TEST_API_001','pblancNm':'테스트 공고','bsnsSumryCn':'<p>중소기업 지원</p>',
            'trgetNm':'중소기업','pldirSportRealmLclasCodeNm':'기술','jrsdInsttNm':'테스트기관',
            'reqstBeginEndDe':'2026-09-01 ~ 2026-09-30','pblancUrl':'https://example.test/notice'}
    analysis = {'externalId':'TEST_API_001','summary':'테스트 분석','target':'중소기업',
                'requirements':[{'type':'CLASSIFICATION','values':['중소기업'],'evidence':'중소기업 지원'}]}
    monkeypatch.setattr(module, 'fetch_bizinfo', lambda limit=5: [item])
    monkeypatch.setattr(module, 'analyze_with_ai', lambda items: [analysis])
    started = client.post('/api/announcements/import')
    assert started.status_code == 202
    first = client.get('/api/announcements/import/status').json()
    module.initialize_database()  # 서버 재시작을 흉내 내도 가져온 공고가 남아야 한다.
    client.post('/api/announcements/import')
    second = client.get('/api/announcements/import/status').json()
    assert first['status'] == 'SUCCEEDED'
    assert first['imported'] in (0, 1)
    assert second['status'] == 'SUCCEEDED'
    assert second['skipped'] == 1

def test_bizinfo_items_accepts_current_and_documented_shapes():
    item = {'pblancId': 'PBLN_1'}
    assert module._bizinfo_items({'jsonArray': [item]}) == [item]
    assert module._bizinfo_items({'jsonArray': {'item': [item]}}) == [item]

def test_plain_text_removes_api_html():
    assert module._plain_text('<p>지원&nbsp;대상</p><p>중소기업</p>') == '지원 대상 중소기업'

def test_application_info_uses_official_source_fields():
    info = module.application_info_from_source({
        'reqstBeginEndDe': '2026-09-01 ~ 2026-09-30',
        'reqstMthPapersCn': '<p>온라인 접수</p>',
        'refrncNm': '기업지원팀 02-123-4567',
        'fileNm': '신청서.hwp@사업계획서.docx',
        'bsnsSumryCn': '<p>최대 1억원 지원</p>',
        'excInsttNm': '테스트 수행기관',
    })
    assert info['applicationMethod'] == '온라인 접수'
    assert info['attachments'] == ['신청서.hwp', '사업계획서.docx']
    assert info['contact'] == '기업지원팀 02-123-4567'
    assert info['supportDetails'] == '최대 1억원 지원'

def test_reviews_are_stored_per_account_and_company(monkeypatch, tmp_path):
    monkeypatch.setattr(module, 'DB_PATH', tmp_path / 'announcements.db')
    module.initialize_database()
    demo = {'Authorization': 'Bearer demo-session'}
    assert client.get('/api/reviews').status_code == 401
    saved = client.put('/api/reviews/1', headers=demo, json={'decision': 'ON_HOLD'})
    assert saved.status_code == 200
    assert client.get('/api/reviews', headers=demo).json() == {'1': 'ON_HOLD'}

    with module.connect() as db:
        db.execute("INSERT INTO companies(id,name) VALUES(2,'다른 기업')")
        db.execute("INSERT INTO users(id,email,display_name,password) VALUES(2,'other@test.local','다른 사용자','test')")
        db.execute("INSERT INTO company_memberships VALUES(2,2,'ADMIN')")
        db.execute("INSERT INTO auth_sessions VALUES('other-session',2,2)")
        db.commit()
    other = {'Authorization': 'Bearer other-session'}
    assert client.get('/api/reviews', headers=other).json() == {}
    client.put('/api/reviews/1', headers=other, json={'decision': 'NOT_INTERESTED'})
    assert client.get('/api/reviews', headers=demo).json() == {'1': 'ON_HOLD'}
    assert client.get('/api/reviews', headers=other).json() == {'1': 'NOT_INTERESTED'}
