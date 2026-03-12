# REST API assessment for FlaskLibrary

## Scope
Оцінка виконана для поточної архітектури з розділенням SSR та API:
- SSR-маршрути: `app/web_routes.py`.
- REST API-маршрути: `app/api_routes.py`.
- Сервісний шар: `app/services/*.py`.
- Контракт API: `openapi.yaml`.

## Executive summary
Проєкт працює у **гібридній моделі SSR + REST API**:
- HTML/UX обслуговується SSR-роутами.
- Інтеграційний шар винесено в JSON API під `/api/v1/*`.

Стан на зараз: **стабільний базовий REST-контур із HTTP caching для read endpoint-ів**, плюс write-операції для reviews/annotations. Для production-grade рівня залишаються кроки у напрямку API auth strategy, розширення OpenAPI та concurrency controls для mutate-операцій.

## Що вже зроблено (відносно плану)

### 1) Окремий API namespace `/api/v1` — ✅
Реалізовано окремим blueprint в `app/api_routes.py`.

### 2) Read endpoint-и — ✅
Реалізовано:
- `GET /api/v1/books`
- `GET /api/v1/books/<id>`
- `GET /api/v1/readers/<id>`
- `GET /api/v1/reviews/<id>`

### 3) Write endpoint-и — ✅
Реалізовано:
- `POST /api/v1/books/<id>/reviews`
- `POST /api/v1/books/<id>/annotations`
- `PATCH /api/v1/reviews/<id>`
- `DELETE /api/v1/reviews/<id>`
- `PATCH /api/v1/annotations/<id>`
- `DELETE /api/v1/annotations/<id>`

### 4) HTTP-коди та JSON error envelope — ✅
Є уніфікований JSON error envelope та коректні статус-коди для основних сценаріїв (`200/201/204/400/401/403/404/422`).

### 5) HTTP caching для публічних read endpoint-ів — ✅
Реалізовано:
- `ETag` для GET-відповідей.
- `Cache-Control: public, max-age=60`.
- Conditional requests через `If-None-Match` → `304 Not Modified`.
- Серверний in-memory TTL кеш (без Redis) для read-відповідей.
- Інвалідація API-кешу після mutating-операцій (`POST/PATCH/DELETE`).

### 6) Розділення SSR/API по відповідальностях — ✅
Реалізовано через `app/web_routes.py` (HTML) та `app/api_routes.py` (JSON) з повторним використанням `app/services/*`.

## Що ще НЕ закрито / частково закрито

1. **OpenAPI покриття та деталізація** — 🟡  
   Специфікація є, але бажано розширити `components/schemas`, приклади успішних та error-відповідей, уніфіковані response-компоненти, а також явно задокументувати cache headers/304 сценарії.

2. **Єдина стратегія auth для зовнішніх API-клієнтів** — 🟡  
   Поточний підхід достатній для web/session сценаріїв, але для зовнішніх інтеграцій зазвичай потрібна token-based схема (Bearer/JWT/API key) з чітким lifecycle.

3. **Concurrency/idempotency для mutate endpoint-ів** — 🟡  
   Для GET вже є conditional caching (`ETag`/`If-None-Match`), але для змін даних ще немає `If-Match`/optimistic locking policy.

4. **Rate limiting та операційні API-політики** — 🟡  
   Не зафіксовані політики throttling/quotas, audit/correlation-id, та deprecation/versioning policy для майбутніх змін (`/api/v2`).

5. **Контрактна стандартизація success-відповідей** — 🟡  
   Error envelope уніфіковано, але корисно зафіксувати стиль success payload (resource-first vs envelope-first) на рівні style-guide.

## Оновлена оцінка зрілості
- **REST API compliance: 8.3 / 10**
- **SSR UX maturity: 8.5 / 10**
- **Загалом архітектура: 8.4 / 10**

## Рекомендовані наступні кроки (коротко)
1. Розширити `openapi.yaml` (schemas/components/security/responses/examples + cache/304 semantics).
2. Визначити auth policy для API-клієнтів (session-only vs token-based).
3. Додати contract-тести на стабільність полів/headers (включно з 304 flow).
4. Додати concurrency policy для mutate endpoint-ів (`If-Match`/version field).
5. Зафіксувати API style-guide та deprecation policy для майбутнього `/api/v2`.

## Notes
Поточний підхід (SSR для UI + REST для інтеграцій) залишається практичним і низькоризиковим: не ламає web UX і дає стабільний JSON-контракт для клієнтів.
