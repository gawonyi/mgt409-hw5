# AI Prompts Log — HW5: Campus Customs Multi-Agent Operations

Author: Gawon Yi
Vibe coder: Claude (the Claude app, working directly in this project folder on my Mac); Problem 4's MCP tools were also called from Claude Code with the server connected through `.mcp.json`.

This file logs the prompts I gave my AI coding assistant, one section per problem. I typed my prompts in Korean (my working language), mostly restating each problem in my own words as I understood it. Each section shows **the prompt exactly as I typed it** and an English version written for this log.

---

## Problem 1 — Vibe Coder Prompts

**Prompt 1, as I typed it (Korean original):**
> Problem 1. Vibe coder prompts — 5점
> 목적: AI 코딩 도구를 활용한 작업 과정을 문서로 남기는 것.
>
> * 프로젝트 시작 시 `AI_prompts.md` 생성
> * 과제 진행 중 AI에 입력한 프롬프트를 계속 기록
> * 각 Problem마다 별도 섹션 작성
> * 각 섹션에 다음 내용 포함
>    * Problem 번호 및 제목
>    * 본인이 직접 작성한 프롬프트 최소 1개
>    * 추가 프롬프트가 필요했다면 해당 프롬프트
>    * 첫 번째 AI 응답에서 무엇이 부족했는지 설명하는 문장 1개
> * 과제 요구사항을 AI에 설명할 때 자신의 표현을 사용하는 것이 중요함
>
> 제출 파일: `AI_prompts.md`

**Prompt 1, English version:**
> Problem 1 is about documenting how I work with an AI coding tool. Create `AI_prompts.md` at the start of the project and keep adding the prompts I give you as we go. Make a separate section for each problem. Each section needs the problem number and title, at least one prompt I wrote myself, any follow-up prompt I needed, and one sentence on what was missing from your first response. When I explain the requirements to you, I should use my own words.

**Follow-up prompt:** None needed.

**What was missing from the first response:** Nothing; the first response created the file with the structure I asked for.

---

## Problem 2 — Study the Campus Customs Database

**Prompt 1, as I typed it (Korean original):**
> Problem 2. Study the Campus Customs database — 8점
> 목적: AI Agent가 사용할 데이터베이스의 구조와 실제 업무 티켓을 이해하는 것.
>
> * `data/campus_customs.db`를 열어서 모든 테이블과 컬럼을 조사
> * 원본 DB를 `data/campus_customs_new.db`로 복사
> * 이후 DB 변경 작업은 원본이 아니라 새 복사본에서 수행
> * 데이터베이스에 있는 3개의 미해결 티켓(open tickets) 조사
> * 각 티켓이 어떤 다른 테이블의 데이터와 연결되는지 파악
> * `output/harness.md` 파일 생성
> * 모든 테이블에 대해 컬럼 목록과 해당 테이블이 Agent의 업무에 중요한 이유를 한 줄로 설명
> * `harness.md`는 이후 문제에서 계속 업데이트하는 문서임
>
> 페이지에서 명시적으로 언급된 테이블은 `desk`, `tickets`, `inventory`, `pricing`, `vendors`, `leases`, `cash_accounts`, `payments`, `invoices`야. 다만 실제 DB를 열어 모든 필드를 검증해야 하므로 컬럼명은 임의로 작성하면 안 돼.
> 제출 파일: `data/campus_customs_new.db`, `output/harness.md`

**Prompt 1, English version:**
> For Problem 2, I need to understand the database the agents will use and the real work tickets in it. Open `data/campus_customs.db` and look at every table and column. Copy the original to `data/campus_customs_new.db`; from now on, any database changes happen in the copy, not the original. Look into the three open tickets and figure out which other tables each one connects to. Then create `output/harness.md` that lists every table's columns with one line on why that table matters for the agents' work. The page mentions `desk`, `tickets`, `inventory`, `pricing`, `vendors`, `leases`, `cash_accounts`, `payments`, and `invoices`, but verify every field against the actual database instead of making up column names. `harness.md` will keep growing in later problems.

**Follow-up prompt:** None needed.

**What was missing from the first response:** Nothing; the first response checked the real schema, made the copy, and traced all three tickets.

---

## Problem 3 — Build the MCP Server

**Prompt 1, as I typed it (Korean original):**
> Problem 3. Build the MCP server — 12점
> 목적: 모든 AI Agent가 공통으로 사용할 데이터 접근 서버를 구축하는 것.
>
> * `mcp_server/` 디렉터리에 FastMCP 기반 서버 작성
> * 서버는 `data/campus_customs_new.db`를 사용
> * 이 단계에서는 서버를 실제 실행하거나 AI 코딩 도구에 연결할 필요는 없음
> * DB에 존재하는 3개 티켓을 처리하는 데 필요한 MCP tool 3개를 우선 구현
> * Tool 이름은 기능을 분명하게 나타내야 함
> * 반환하는 모든 정보는 실제 DB에서 조회한 것이어야 하며 임의의 데이터를 생성하면 안 됨
> * 향후 문제에서 같은 서버에 추가 tool을 구현할 예정
>
> `output/harness.md`에는 초기 MCP tool 3개 각각에 대해 다음을 기록해야 해.
>
> 1. Tool 이름
> 2. 어떤 DB 테이블을 조회하는지
> 3. Ticket 101, 102, 103 중 어떤 티켓 처리에 도움이 되는지
> 4. 그 티켓을 처리하는 데 해당 Tool이 필요한 구체적인 이유
>
> 예를 들어 단순히 "재고를 읽는다"는 설명보다 특정 티켓을 해결하려면 어떤 정보가 필요하고 그 Tool이 왜 적합한지 밝혀야 해.
> 또한 `mcp_server/README.md`를 만들고 MCP 서버의 목적, 사용하는 데이터베이스, 현재 구현된 3개 tool을 설명해야 해.
> 제출 파일: `mcp_server/`, `mcp_server/README.md`, 업데이트된 `output/harness.md`

**Prompt 1, English version:**
> Problem 3 is about building the shared data-access server that every agent will use. Write a FastMCP server in `mcp_server/` that uses `data/campus_customs_new.db`. We don't need to run it or connect it to the coding tool yet. Start with three MCP tools that are needed to handle the three tickets in the database, and give them names that make their job obvious. Everything a tool returns has to come from the real database; never make up data. We'll add more tools to the same server later. In `output/harness.md`, for each of the three tools, record the tool name, which table it reads, which ticket (101, 102, or 103) it helps with, and the specific reason that ticket needs it. Don't just say "reads inventory"; explain what information the ticket needs and why the tool fits. Also create `mcp_server/README.md` explaining the server's purpose, the database it uses, and the three tools.

**Follow-up prompt:** None needed.

**What was missing from the first response:** Nothing; the first response delivered the server, README, and ticket-specific harness rows.

---

## Problem 4 — Connect and Test the MCP Server

**Prompt 1, as I typed it (Korean original):**
> Problem 4. Add the MCP server to vibe coder and test each tool — 8점
> 목적: 만든 MCP 서버가 실제 AI 코딩 도구에서 정상 작동하는지 확인하는 것.
> - Claude Code, Codex, Cursor 등 사용하는 vibe coder에 MCP 서버 연결
> - 프로젝트 루트에 .mcp.json을 만들어 연결 설정을 기록하거나, 사용하는 도구의 로컬 MCP 설정 방식에 맞춰 저장
> - Problem 3에서 구현한 MCP tool 3개를 각각 실제 호출해서 테스트
> - 테스트 증거를 output/mcp_smoke.json에 저장
> 각 tool의 테스트 증거에는 반드시 다음이 있어야 해.
> 필드	포함할 내용
> Prompt	AI 코딩 도구에 실제로 입력한 질문
> Tool name	호출한 MCP tool의 이름
> Tool output	실제로 반환된 결과
> 중요: 반환값은 data/campus_customs_new.db의 값과 일치해야 해. 가상의 실행 결과를 작성하는 것은 요구사항을 충족하지 못해.
> 제출 파일: .mcp.json 또는 동등한 설정, output/mcp_smoke.json

**Prompt 1, English version:**
> Problem 4 is about proving the MCP server actually works inside an AI coding tool. Connect the server to the vibe coder I use (Claude Code, Codex, Cursor, etc.) by creating `.mcp.json` at the project root, or by saving it the way my tool stores local MCP settings. Then actually call each of the three Problem 3 tools and save the evidence in `output/mcp_smoke.json`. For each tool, the evidence must include the prompt I typed, the name of the tool that was called, and the output it really returned. The outputs have to match the values in `data/campus_customs_new.db`; a made-up run doesn't count.

**Follow-up prompt, as I typed it:**
> 어떡하라고? 코딩도구에 연결 이거 어떡하는거야? 과제 결과물은 portkey API 요걸로 동작하면 좋겠어

**Follow-up prompt, English version:**
> I don't understand what I'm supposed to do. How do I connect this to a coding tool? I'd like the deliverables to run on my Portkey API.

**What was missing from the first response:** It handed me manual setup steps for an outside coding tool instead of a test I could run with one command on the Portkey gateway my workspace already uses.

**Follow-up prompt 2, as I typed it:**
> (터미널 출력 스크린샷을 붙여넣음: gpt-6-luna가 /v1/chat/completions에서 reasoning_effort와 함께 function tools를 지원하지 않는다는 400 오류)

**Follow-up prompt 2, English version:**
> (Pasted the terminal output: every call failed with a 400 error saying gpt-6-luna does not support function tools with reasoning_effort on /v1/chat/completions.)

**What was missing:** The test script did not set `reasoning_effort` to `none`, which gpt-6-luna on Portkey requires before it will call tools.


**Follow-up prompt 3 (later, during the review), typed into Claude Code with the MCP server connected:**
> Use the campus-customs MCP server tools directly (do not start the server yourself or run any script). Call check_stock_by_sku_size for CC-TEE-WHITE size S, get_lease_rent_due for lease 1, and get_sku_pricing for CC-HOOD-NAVY, one at a time, and show each tool name and raw output.

**What was missing:** The Portkey script proved the server works, but the assignment asks for the tools to be called from a vibe coder. My first try in Claude Code failed because `.mcp.json` started the server with the system `python3` (no `fastmcp`), so I asked here "2단계 결과 이렇다는데 어떻게 해?" ("this is what step 2 returned, what do I do?"); `.mcp.json` was changed to `.venv/bin/python`, and in a new session Claude Code called all three tools directly. That run is the main evidence in `output/mcp_smoke.json` (screenshot: `output/mcp_smoke_claude_code.png`).
---

## Problem 5 — Build the Agent Team and Grow the MCP Tools

**Prompt 1, as I typed it (Korean original):**
> Problem 5. Build the agent team and grow the MCP tools — 15점
> 목적: 전문성이 다른 5개의 Agent를 구성하고, 서로 업무를 위임할 수 있도록 연결하는 것.
> 구현해야 하는 Agent 5개
> Boss Agent
> 업무를 분배하고 다른 Agent에게 위임
> Inventory
> Accounting
> Facilities
> Customer Service
> Shared MCP Server
> campus_customs_new.db
> 개념도: Boss를 중심으로 전문 Agent를 활용하는 구조. 실제 구현은 Agent 간의 상호 위임도 지원해야 함.
> 구현 요구사항
>
> * PydanticAI로 Agent 시스템 구현
> * Boss, Inventory, Accounting, Facilities, Customer Service의 다섯 역할 모두 포함
> * Agent들이 서로 업무를 위임할 수 있는 연결 구조 구축
> * Agent 간 위임을 처리하는 실행 루프 구현
> * `backend/prompts/`에 Agent별 프롬프트 파일을 하나씩 생성
> * `backend/models.py`에 필요한 데이터 타입 정의
> * `backend/` 하위에 Agent 구현 파일 배치 (구체적인 파일 구조는 변경 가능)
> * 모든 Agent에서 `PORTKEY_API_KEY` 사용
> * 모델은 모든 Agent에 `gpt-6-luna`만 사용
>
> Agent 프롬프트
> 각 역할에 필요한 실제 매장 운영 규칙과 업무 범위를 본인의 표현으로 상세하게 작성해야 해.
> 예를 들면 업무 마감일, 미결제 인보이스가 있는 주문의 출고 제한, 사람의 승인이 필요한 결제 같은 규칙을 적절한 Agent에게 부여하는 것이 중요해. 단순한 범용 프롬프트보다는 해당 역할의 책임과 판단 기준을 구체적으로 정의해야 높은 평가를 받을 수 있어.
> MCP와 데이터 접근
>
> * 기존 MCP 서버에 필요한 tool을 추가
> * Agent는 MCP를 통해 `data/campus_customs_new.db`의 정보를 사용해야 함
> * MCP를 우회하여 DB를 직접 접근하는 별도의 shop-tools 계층을 만들면 안 됨
> * 모든 매장 관련 사실은 DB에 근거해야 함
>
> Audit trail
> `output/audit_trail.json`을 만들어 실행 과정의 각 Agent loop step을 기록해야 해.
>
> * 어떤 Agent가 어떤 단계를 수행했는지 나중에 검토할 수 있을 정도로 충분한 정보 기록
> * 매 실행마다 기존 로그에 추가(append)
> * 새 실행을 시작할 때 기존 파일의 로그를 삭제하거나 덮어쓰면 안 됨
>
> 문서 업데이트
> `output/harness.md`에 다음을 추가해야 해.
>
> * 각 Agent 목록
> * 모든 MCP tool 목록 및 사용 테이블
> * 실제 고객과 금전을 다루는 비즈니스에서 필요한 안전장치(guardrails)
> * Token 사용량을 제한하기 위한 방안
>
> 마지막으로 `mcp_server/README.md`도 업데이트해, 추가된 MCP tool이 모두 반영되도록 해야 해.
> 제출 구성: `backend/`, Agent별 prompt, `backend/models.py`, 확장된 `mcp_server/`, `output/audit_trail.json`, 업데이트된 문서

**Prompt 1, English version:**
> Problem 5 is about building five agents with different expertise and wiring them so they can hand work to each other. Build it in PydanticAI with Boss (splits up the work and delegates), Inventory, Accounting, Facilities, and Customer Service. The diagram shows Boss in the middle, but the real system has to let agents delegate to each other too, with a run loop that handles those hand-offs. Put one prompt file per agent in `backend/prompts/`, the data types in `backend/models.py`, and the agent code under `backend/`. Every agent uses `PORTKEY_API_KEY` and only `gpt-6-luna`. The prompts need real shop rules and scope for each role, for example deadlines, holding orders that have an unpaid invoice, and payments that need a human to approve, given to the right agent; specific beats generic. Add the tools the agents need to the existing MCP server. Agents must get data from `data/campus_customs_new.db` through MCP only, with no separate shop-tools layer that goes around it, and every shop fact has to come from the database. Write `output/audit_trail.json` with every agent-loop step, enough to review later who did what; append on every run and never delete or overwrite old entries. Add to `output/harness.md` the agent list, every MCP tool with the tables it uses, guardrails for a business that handles real customers and real money, and how token use is limited. Finally, update `mcp_server/README.md` so it lists every tool.

**Follow-up prompt:** None needed.

**What was missing from the first response:** Nothing I had to ask for, though testing showed the restock tool would let a purchase order go through when cash was short, so it got a server-side check.

---

## Problem 6 — Plan the Three Tickets

**Prompt 1, as I typed it (Korean original):**
> Problem 6. Plan the three tickets — 8점
> 목적: Agent를 실제로 실행하기 전에 세 개의 티켓에 대한 예상 처리 과정을 설계하는 것.
>
> * `output/desk_tickets.html` 생성
> * 브라우저에서 파일을 더블클릭해 바로 열 수 있는 HTML 페이지로 구현
> * Ticket 101, 102, 103 각각에 대한 탭 생성
> * 추후 문제를 위해 Cash와 Reflection 탭도 생성
> * 현재 Cash와 Reflection 탭은 빈 상태 또는 짧은 안내 문구만 있어도 됨
>
> 각 티켓에는 우선 Expected 섹션만 작성하고, 실행 이후 채울 Actual 섹션을 위한 공간을 남겨야 해.
> Expected에는 다음 내용이 필요해.
>
> 1. Boss가 가장 먼저 호출할 Agent와 그 이유
> 2. 예상되는 모든 Agent 간 위임(delegation)의 순서 및 관계
> 3. 실행 중 사용할 것으로 예상되는 MCP tool
>
> 중요: Boss가 모든 전문 Agent를 무조건 호출하도록 계획하면 낮은 점수를 받을 수 있어. 각 티켓 해결에 필요한 Agent만 선택하고, 전문 Agent 사이에 필요한 위임 관계를 구체적으로 설계해야 해.
> 제출 파일: `output/desk_tickets.html`

**Prompt 1, English version:**
> Problem 6 is about planning how the agents should handle the three tickets before we actually run them. Create `output/desk_tickets.html` as a page I can double-click to open in a browser, with a tab for each of Ticket 101, 102, and 103, plus Cash and Reflection tabs for later problems (those two can be empty or have a short note for now). On each ticket tab, fill in only the Expected section and leave space for an Actual section we'll fill after the run. Expected needs: which agent the Boss calls first and why, every delegation we expect between agents and in what order, and which MCP tools we expect the run to use. Don't plan for the Boss to call every specialist; pick only the agents each ticket needs and spell out the hand-offs between specialists.

**Follow-up prompt:** None needed.

**What was missing from the first response:** Nothing; the plans named only the agents each ticket needs and the specialist-to-specialist hand-offs.

---

## Problem 7 — Backend Routes

**Prompt 1, as I typed it (Korean original):**
> Problem 7. Backend routes — 7점
> 목적: React 대시보드에서 Agent를 실행하고 결과를 받아볼 수 있도록 FastAPI 백엔드를 구축하는 것.
> backend/main.py에 FastAPI를 사용해 다음 기능을 제공하는 API route들을 구현해야 해.
> API 기능	상세 요구사항
> List tickets	티켓 101, 102, 103과 각각의 상태(open/resolved) 반환
> Run ticket	Ticket ID를 입력받아 해당 티켓에 대한 Agent team 실행
> Agent events	최근 Agent 이벤트, Agent별 발언과 사용한 tool 정보 반환
> Approve payment	사람의 승인 클릭 이후에만 결제 또는 구매 처리
> Cash balance	cash_accounts의 현재 checking balance 반환
> Reset database	테스트를 위해 DB를 원래 상태로 초기화
> 특히 결제는 Agent가 준비할 수 있지만, 실제 현금 잔액 변경은 사람의 승인 이후에만 수행되어야 해.
> 실행 조건
> backend/ 디렉터리에서 다음 명령어로 서버 실행:
> uvicorn main:app --reload --port 8000
> 백엔드는 http://localhost:8000에서 실행되며, 다음 Problem의 프런트엔드가 이 API를 호출하게 돼.
> 또한 output/harness.md에 각 API route의 URL과 기능을 한 줄씩 기록해야 해. 다만 구체적인 endpoint 경로명은 과제에서 지정하지 않았으므로 직접 설계할 수 있어.
> 제출 파일: backend/main.py, 업데이트된 output/harness.md

**Prompt 1, English version:**
> Problem 7 is about building a FastAPI backend so the React dashboard can run the agents and get results back. In `backend/main.py`, add API routes that: list tickets 101, 102, and 103 with their status (open/resolved); take a ticket ID and run the agent team on it; return recent agent events, including what each agent said and which tools it used; process a payment or purchase only after a human clicks approve; return the current checking balance from `cash_accounts`; and reset the database to its original state for testing. Agents can prepare payments, but the cash balance may only change after a person approves. The server runs from `backend/` with `uvicorn main:app --reload --port 8000` at http://localhost:8000, and the next problem's frontend will call it. Also add one line per route to `output/harness.md` with its URL and what it does; the exact endpoint paths are up to us.

**Follow-up prompt:** None needed.

**What was missing from the first response:** Nothing; all six functions were covered and the approve route was tested to be the only thing that changes cash.

---

## Problem 8 — Agent Dashboard

**Prompt 1, as I typed it (Korean original):**
> Problem 8. Agent dashboard — 12점
> 목적: 티켓과 Agent의 실시간 업무 진행을 시각적으로 확인하고, 사람이 결제를 승인할 수 있는 대시보드를 만드는 것.
> 기술 요건
>
> * `frontend/` 폴더에 구현
> * React + Vite + TypeScript 사용
> * Problem 7에서 만든 백엔드 API 호출
> * 백엔드 URL: `http://localhost:8000`
> * 백엔드 CORS 설정에서 Vite 개발 서버의 origin(일반적으로 `http://localhost:5173`) 허용
>
> 대시보드 필수 기능
>
> * 티켓 3개를 모두 표시
> * 사용자가 하나의 티켓을 선택하고 Agent 실행을 시작할 수 있어야 함
> * 실행 중 각 Agent가 무슨 말을 하거나 어떤 작업을 수행하는지 표시
> * 실행이 끝난 티켓의 상태를 resolved로 변경
> * 각 티켓에서 Agent별 수행 내용을 짧게 요약
> * 사람이 결제 또는 구매를 승인할 수 있는 인터페이스 제공
> * 현재 checking balance 표시
> * 승인된 결제 후 실제로 cash balance가 감소하는 것을 확인할 수 있어야 함
>
> UI 디자인 평가
> 기능뿐 아니라 디자인도 평가 대상이야.
>
> * 대시보드의 레이아웃과 사용성을 고려할 것
> * Agent들의 업무 활동을 알아보기 쉽게 구분할 것
> * 실제 직원이 사용할 법한 운영 대시보드처럼 구성할 것
> * 기본 Vite 템플릿 수준에 머무르지 말고 창의적인 디자인 요소를 적용할 것
>
> 실행 및 문서
> npm run dev
>
> `output/design.md`에 아래 사항을 작성해야 해.
>
> * 대시보드 레이아웃을 선택한 이유
> * Agent별 정보 표현 방식을 다르게 구성한 방법
> * Resolved ticket과 cash balance를 보여주는 방식
> * 사용성과 시각적 완성도를 높이기 위한 창의적 선택과 그 이유
>
> 제출 파일: `frontend/`, `output/design.md`

**Prompt 1, English version:**
> Problem 8 is about building a dashboard where we can see the tickets and the agents' work in real time, and where a person can approve payments. Build it in `frontend/` with React + Vite + TypeScript, calling the Problem 7 API at http://localhost:8000, and allow the Vite dev server origin (usually http://localhost:5173) in the backend's CORS. The dashboard must show all three tickets, let me pick one and start the agent team, show what each agent is saying or doing while it runs, change the ticket to resolved when it's done, give a short summary of what each agent did, let a human approve a payment or purchase, show the current checking balance, and make it visible that the cash balance actually drops after an approved payment. Design is graded too: think about layout and usability, make each agent's activity easy to tell apart, make it feel like an operations dashboard a real employee would use, and go beyond the default Vite template with creative design choices. It starts with `npm run dev`. Also write `output/design.md` explaining why I chose the layout, how each agent's information is shown differently, how resolved tickets and the cash balance are shown, and the creative choices for usability and polish and why.

**Follow-up prompt:** None needed.

**What was missing from the first response:** Nothing I had to ask for; screenshot testing caught a slow refresh after approval and a sideways scroll on phones, which were fixed before handing it over.

---

## Problem 9 — Resolve the Tickets

**Prompt 1, as I typed it (Korean original):**
> Problem 9. Resolve the tickets — 10점
> 목적: 완성한 Multi-Agent System을 실제 데이터로 실행해 티켓 3개를 모두 해결하고 그 결과를 검증하는 것.
> 1. DB 초기화 및 티켓 실행
> - data/campus_customs_new.db를 원래 데이터 상태로 다시 초기화
> - 초기 checking balance 기록
> - 대시보드에서 Ticket 101, 102, 103을 모두 실행
> - 세 티켓 모두 resolved 상태가 될 때까지 처리
> 2. Expected vs. Actual
> Problem 6에서 만든 output/desk_tickets.html을 다시 열어 각 티켓의 Actual 섹션을 작성해야 해.
> - 실제로 참여한 Agent
> - 실제 Agent 간 업무 위임 관계
> - 실제 사용한 MCP tool
> - 이전에 작성한 Expected 계획은 그대로 유지
> - 계획과 실제 실행 결과를 비교할 수 있어야 함
> 3. Cash tab
> Cash 탭에는 모든 티켓의 현금 흐름을 설명해야 해.
> (Starting balance / Ticket 101 / Ticket 102 / Ticket 103 / Ending balance: 현금 변동액 및 발생 이유)
> 각 티켓에서 실제로 발생한 결제나 구매에 대해 어떤 거래 때문에 얼마가 변동했는지 기록해야 해.
> 최종 잔액은 DB의 cash_accounts에 기록된 금액과 반드시 같아야 해. 대시보드에서 모든 티켓이 resolved로 표시되더라도 현금 계산이 틀리면 감점 대상이야.
> 4. 결과 증빙 파일
> output/resolved_tickets.json에 각 티켓별로 다음 항목을 저장해야 해.
> - Ticket ID
> - 최종 상태
> - 처리 결과를 설명하는 짧은 요약
> - 각 Agent의 기여 내용
> - 사람의 결제 승인 여부 및 관련 내역
> output/resolved_board.html에는 다음을 포함해야 해.
> - 더블클릭하여 브라우저에서 열 수 있는 HTML 페이지
> - Ticket 101, 102, 103의 해결 완료 상태를 보여주는 React 대시보드 스크린샷
> 그 외에도 실제 실행 기록을 output/audit_trail.json에 누적하고, output/harness.md를 최종 완성해야 해.
> 최종 harness에는 데이터베이스 테이블, MCP tool, 5개 Agent, API route, 대시보드, 안전 규칙이 모두 포함되어야 해.
> 제출 파일: output/desk_tickets.html, output/resolved_tickets.json, output/resolved_board.html, output/audit_trail.json, output/harness.md

**Prompt 1, English version:**
> Problem 9 is about running the finished multi-agent system on the real data, resolving all three tickets, and checking the results. Reset `data/campus_customs_new.db` to the original data, record the starting checking balance, run tickets 101, 102, and 103 from the dashboard, and keep going until all three are resolved. Then reopen `output/desk_tickets.html` and fill in each ticket's Actual section with the agents that actually took part, the real delegations between them, and the MCP tools they actually used, keeping the Expected plans so the two can be compared. The Cash tab needs the starting balance after reset, how cash changed for each ticket and why (which payment or purchase, how much), and the ending balance, which must equal `cash_accounts` in the database. Save `output/resolved_tickets.json` with each ticket's ID, final status, a short outcome, each agent's contribution, and any human payment approvals, and `output/resolved_board.html` as a double-clickable page with screenshots of the React board showing 101, 102, and 103 resolved. Keep appending real runs to `output/audit_trail.json` and finish `output/harness.md` so it covers the tables, MCP tools, five agents, API routes, dashboard, and safety rules.

**Follow-up prompt, as I typed it:**
> 돌렸는데 티켓 2,3은 이래 ㅠㅠ  (102와 103이 Open으로 남은 대시보드 스크린샷 첨부)

**Follow-up prompt, English version:**
> I ran them, but tickets 2 and 3 ended up like this. (Pasted screenshots: 102 and 103 finished but stayed Open.)

**What was missing from the first response:** The agent prompts were too strict for the real tickets: Facilities required the rent email's amount to match even though the email has no amount, and the Boss would not resolve a price quote while waiting on the customer, so both rules had to be clarified before a clean rerun.

---

## Problem 10 — Reflection

**Prompt 1, as I typed it (Korean original):**
> Problem 10. Reflection — 10점
> 목적: Multi-Agent System이 실제 업무에 얼마나 효과적이었는지, 설계한 업무 위임 방식이 적절했는지 평가하는 것.
> 별도의 Reflection 문서를 만드는 대신 `output/desk_tickets.html`의 Reflection 탭을 완성해야 해.
> 작성해야 하는 다섯 가지 질문
>
> 1. Agent performance evaluation: 각 티켓에서 Agent가 얼마나 잘 수행했는지, 그 평가의 근거가 무엇인지 설명
> 2. Actual vs. Expected: Ticket 101, 102, 103 각각에서 실제 Agent 위임과 실행 결과가 사전 계획과 어떻게 달랐는지 비교
> 3. Single-agent alternative: 여러 Agent가 아닌 Tool을 사용하는 단일 Agent로 구현했다면 어떤 부분이 더 간단했을지, 그 이유 설명
> 4. Three solvable new problems: Campus Customs가 향후 직면할 수 있는 새로운 문제 중 현재 구현한 Agent와 Tool로 해결 가능한 문제 3개 제시
> 5. Three unsolvable new problems: 현재 시스템으로 해결할 수 없는 새로운 문제 3개 제시하고, 이를 해결하려면 어떤 새로운 Tool과 Agent가 필요한지 설명
>
> 평가상 중요한 조건
>
> * 실제 구축한 Campus Customs 애플리케이션과 연결해서 작성
> * 세 티켓의 실제 실행 결과를 근거로 설명
> * 티켓별 Expected / Actual 및 Cash 탭을 증거로 활용
> * 구체적인 티켓 번호와 상황 제시
> * 일반적인 AI의 장단점을 나열하는 추상적인 에세이는 피할 것
>
> 제출 파일: Reflection 탭이 완성된 `output/desk_tickets.html`

**Prompt 1, English version:**
> Problem 10 is about judging how well the multi-agent system actually worked and whether the way we split up and delegated the work made sense. Don't make a separate document; finish the Reflection tab in `output/desk_tickets.html`. Answer five questions: how well the agents performed on each ticket and what that judgment is based on; how the real delegation and results differed from the plan for tickets 101, 102, and 103; what would have been simpler with a single agent using tools instead of several agents, and why; three new problems Campus Customs might face that the current agents and tools can already solve; and three it can't solve, with the new tools and agents that would be needed. Tie everything to the Campus Customs app we actually built, use the real results of the three runs and the Expected/Actual and Cash tabs as evidence, name specific ticket numbers and situations, and avoid a generic essay about AI pros and cons.

**Follow-up prompt:** None needed.

**What was missing from the first response:** Nothing; every answer cites ticket numbers, run ids, tool counts, and the Cash tab.

---

## Problem 11 — Submit to GitHub

**Prompt 1, as I typed it (Korean original):**
> Problem 11. Submit to GitHub — 5점
> 목적: 평가자가 프로젝트를 다운로드해서 재현할 수 있도록 GitHub 저장소와 제출 패키지를 완성하는 것.
>
> * 프로젝트 코드를 Public GitHub Repository에 업로드
> * GitHub 저장소 URL을 Canvas에 제출
> * 같은 URL을 `output/github_url.txt`에도 기록
> * 실제 API Key 등이 포함된 `.env`는 GitHub에 업로드하지 말 것
> * 대신 `.env.example` 포함
> * `data/campus_customs.db` 원본과 `data/campus_customs_new.db` 작업본 모두 포함
>
> (요구되는 프로젝트 구조: AI_prompts.md, requirements.txt, .env.example, .gitignore, .mcp.json, README.md, data/, mcp_server/, frontend/, backend/, output/)
>
> 루트의 `README.md`에는 다음 재현 절차를 설명해야 해.
>
> * Original DB를 working copy로 복사하는 방법
> * MCP 서버 실행 방법
> * FastAPI 백엔드 실행 방법
> * React 대시보드 실행 방법
> * 세 티켓의 전체 테스트를 시작하기 전에 DB를 초기화하는 방법
>
> 제출: Public GitHub URL을 Canvas 및 `output/github_url.txt`에 기록

**Prompt 1, English version:**
> Problem 11 is about packaging the project so a grader can download it and reproduce it. Upload the code to a public GitHub repository, and I'll submit the URL on Canvas; also write the same URL in `output/github_url.txt`. Don't upload the `.env` with my real API key; include `.env.example` instead. Include both `data/campus_customs.db` (original) and `data/campus_customs_new.db` (working copy). Follow the required layout: `AI_prompts.md`, `requirements.txt`, `.env.example`, `.gitignore`, `.mcp.json`, `README.md` at the root, plus `data/`, `mcp_server/` (`server.py`, `README.md`), `frontend/`, `backend/` (`main.py`, `models.py`, `prompts/` with the five agent prompts), and `output/` with all the deliverables. The root README has to explain how to copy the original DB to the working copy, run the MCP server, run the FastAPI backend, run the React dashboard, and reset the DB before a full three-ticket test.

**Follow-up prompt:** None needed.

**What was missing from the first response:** Nothing; it also checked that no file contains the real API key before uploading.

---

## Review and Revision (after the first GitHub upload)

**Prompt 1, as I typed it (Korean original):**
> 이 과제가 요구사항을 모두 충족하는지 교수님 입장에서 채점하고 평가해봐

**Prompt 1, English version:**
> Grade this assignment from the professor's point of view and evaluate whether it meets every requirement.

**Prompt 2, as I typed it:**
> 고치기 이전에 이런 피드백도 있어 이것도 반영할만한지 확인해서 고쳐야될 점을 모두 리스트업해  (다른 리뷰어의 피드백 파일 첨부)

**Prompt 2, English version:**
> Before fixing anything, here is more feedback. Check whether it is worth applying and list everything that needs to be fixed. (Attached another reviewer's feedback.)

**Prompt 3, as I typed it:**
> 모두 업데이트해봐!!

**Prompt 3, English version:**
> Update all of it!

**What the review found and what changed:** Ticket 101 had been resolved without a reply to the customer, the rent-first rule had only held by luck, the Problem 4 evidence did not come from a vibe coder, and this log showed English rewrites instead of what I actually typed. Fixes: server-side guards (a customer order needs a saved reply before it can wait for approval or resolve; rent due within 7 days is held back before any other payment), a new `list_leases` tool, sharper Boss and Accounting prompts, the Korean originals in this file, and a full clean rerun of all three tickets (Problem 9 and 10 outputs updated).
