# 공고 맞춤 판정 서버

30개 공고 분석을 SQLite에 저장하고, 사용자가 입력한 기업정보와 비교해 `신청 가능` 또는
`신청 불가능`만 보여주는 작은 웹 애플리케이션입니다.

```powershell
cd C:\Users\user\OneDrive\Desktop\AI_SOLVERTHON2\server
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\uvicorn app:app --reload
```

`.env`에 기업마당에서 발급받은 인증키를 설정합니다. 인증키는 소스 코드에 직접 넣지 않습니다.

```dotenv
BIZINFO_API_KEY=발급받은_인증키
CODEX_MODEL=gpt-5.6-terra
```

브라우저에서 <http://127.0.0.1:8000>을 엽니다. 최초 실행 시 기본 경로의
`공고_분류_및_회사정보_체크리스트.xlsx`를 읽어 30개 공고 분석을 `announcements.db`에 저장합니다.
다른 파일을 쓰려면 `CHECKLIST_PATH` 환경변수에 절대 경로를 지정합니다.

로그인 후 **전체 공고**에서 **공고 1개 AI 분석·저장** 버튼을 누르면 기업마당 최신 공고 1건을 가져와 Codex CLI로 분석한 뒤 SQLite에 저장합니다. 분석은 서버의 백그라운드 작업으로 실행되므로 다른 페이지에 다녀와도 계속되며, 전체 공고 화면에서 실행 중·완료·실패·취소 상태를 확인할 수 있습니다. 이미 저장된 기업마당 공고는 `external_id` 기준으로 건너뜁니다.
