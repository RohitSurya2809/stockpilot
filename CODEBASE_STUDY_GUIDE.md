# StockPilot Codebase Study Guide
**Purpose:** A judge points at a random line and asks "What does this do?"

---

## FRONTEND (React / TypeScript)

### JavaScript Methods

**1. `.toFixed(n)`** — e.g. `result.reorder_point.avg_daily_demand.toFixed(1)` (Analysis.tsx:292)
Rounds a number to `n` decimal places and returns a **string**. `.toFixed(0)` rounds to integer, `.toFixed(2)` gives two decimals.

**2. `.toUpperCase()`** — e.g. `result.risk_assessment.risk_level.toUpperCase()` (Analysis.tsx:148)
Converts a string to all uppercase. Displays "CRITICAL" instead of "critical".

**3. `.toLowerCase()`** — e.g. `riskLevel.toLowerCase()` (Dashboard.tsx:36)
Converts to lowercase. Used to build CSS class names like `risk-badge critical`.

**4. `.toLocaleString()`** — e.g. `inventory.reduce(...).toLocaleString()` (Dashboard.tsx:178)
Formats a number with comma separators. `5234` becomes `"5,234"`.

**5. `.reduce((acc, item) => ..., initialValue)`** — e.g. `forecasts.reduce((a, b) => a + b, 0)` (Analysis.tsx:260)
Iterates an array and reduces to a single value. Here it sums all forecasts. `a` = running total, `b` = current item, `0` = starting value.

**6. `.filter(callback)`** — e.g. `inventory.filter((s) => s.risk_level === 'critical')` (Dashboard.tsx:51)
Creates new array with only items where callback returns true. Used with `.length` to count critical SKUs.

**7. `.map(callback)`** — e.g. `data.alerts.map((a: any) => a.sku_id).join(', ')` (Dashboard.tsx:60)
Creates new array by transforming each item. Here extracts sku_ids, then `.join(', ')` makes a comma-separated string.

**8. `.trim()`** — e.g. `skuId.trim()` (Analysis.tsx:20)
Removes whitespace from both ends. Validates user actually typed something, not just spaces.

**9. `.includes(str)`** — e.g. `trend.toLowerCase().includes('increas')` (Dashboard.tsx:41)
Returns true if string contains the substring. Used to match trend descriptions for display icons.

### TypeScript-Specific

**10. `??` (nullish coalescing)** — e.g. `stockout.days_until_stockout ?? 0` (Analysis.tsx:42)
Returns right side only if left is `null` or `undefined`. Unlike `||` which also catches `0` and `''`.

**11. `?.` (optional chaining)** — e.g. `err?.response?.status` (Analysis.tsx:78)
Safely accesses nested properties. If any part is null/undefined, returns undefined instead of throwing.

**12. `<AnalysisResult | null>`** — e.g. `useState<AnalysisResult | null>(null)` (Analysis.tsx:11)
TypeScript generic. Tells useState the state holds either an AnalysisResult or null. Enables type checking.

**13. `interface` with `?`** — e.g. `interface Props { page: string; pageData?: any; }` (AssistantPanel.tsx:4-7)
Defines object shape. `?` means optional. Components using `<AssistantPanel>` must pass `page` but `pageData` is optional.

**14. `: Promise<SKU[]>`** — e.g. `getAll: async (): Promise<SKU[]>` (api.ts:17)
Return type annotation. Function returns a Promise resolving to array of SKU objects.

**15. Template literals** — e.g. `` `risk-badge ${riskLevel.toLowerCase()}` `` (Dashboard.tsx:36)
Backtick strings with `${}` for embedded expressions. More readable than string concatenation.

### React Hooks

**16. `useState`** — `const [loading, setLoading] = useState(false)` (Analysis.tsx:12)
Component state. Returns [value, setter]. Calling `setLoading(true)` triggers re-render. Array destructuring names both.

**17. `useEffect`** — `useEffect(() => { loadInventory(); }, [])` (Dashboard.tsx:16-18)
Side effects (API calls). Empty `[]` = runs once after first render. `[searchParams]` = runs when searchParams changes.

**18. `useRef`** — `const canvasRef = useRef<HTMLCanvasElement>(null)` (ForecastChart.tsx:12)
Holds a mutable reference persisting across renders. Used to access raw DOM elements. Doesn't cause re-renders.

**19. `useNavigate`** — `navigate('/analysis?sku=SKU-004')` (Dashboard.tsx:263)
React Router hook for programmatic navigation. Changes URL without full page reload.

**20. `useSearchParams`** — `searchParams.get('sku')` (Analysis.tsx:10)
Reads URL query parameters. `?sku=SKU-004` in URL returns `"SKU-004"`.

**21. `useLocation`** — `location.pathname` (App.tsx:9)
Returns current URL location. `.pathname` gives `"/"`, `"/analysis"`, etc.

### React Patterns

**22. `&&` conditional rendering** — `{result.needs_reorder && (<div>...</div>)}` (Analysis.tsx:155)
Short-circuit: if left is falsy, renders nothing. If truthy, renders the JSX.

**23. Ternary in JSX** — `{loading ? 'Analyzing...' : 'Analyze'}` (Analysis.tsx:124)
Inline conditional: `condition ? ifTrue : ifFalse`.

**24. `<>...</>` Fragment** — wrapping multiple elements (Analysis.tsx:230)
Groups elements without extra DOM node. Invisible wrapper.

**25. `key` prop** — `<div key={sku.sku_id}>` (Dashboard.tsx:242)
Required on list items. Helps React efficiently track which items changed.

**26. Functional state update** — `setMessages(prev => [...prev, newItem])` (AssistantPanel.tsx:33)
`prev` is previous state. `...prev` spreads old array, adds new item. Avoids stale-state bugs.

### API / Axios

**27. `axios.create({ baseURL, headers })`** — (api.ts:8-12)
Creates reusable HTTP client instance. All requests automatically prepend baseURL and include headers.

**28. `import.meta.env.VITE_API_URL`** — (api.ts:6)
Vite environment variables. Only `VITE_`-prefixed vars are exposed to frontend.

**29. Fire-and-forget** — `axios.post(...).catch(() => {})` (api.ts:119-128)
Sends request without awaiting response. `.catch(() => {})` silently ignores errors. Used for n8n webhooks.

**30. `async/await` with `try/catch/finally`** — (Analysis.tsx:25-55)
`async` = returns Promise. `await` = pauses until resolved. `finally` = always runs (sets loading=false).

### Canvas (ForecastChart)

**31. `canvas.getContext('2d')`** — (ForecastChart.tsx:18)
Gets the 2D drawing API. Returns context with `moveTo`, `lineTo`, `arc`, `fill` methods.

**32. `window.devicePixelRatio`** — (ForecastChart.tsx:22)
Pixel density ratio. 2 on Retina displays. Multiplying canvas size by this makes lines sharp.

**33. `ctx.setLineDash([5, 5])`** — (ForecastChart.tsx:112)
Makes lines dashed: 5px drawn, 5px gap. `setLineDash([])` resets to solid. Dashed = predicted data.

**34. `ctx.arc(x, y, radius, 0, Math.PI * 2)`** — (ForecastChart.tsx:103)
Draws a circle. `Math.PI * 2` = full circle. Used for data point dots.

---

## BACKEND (Python / FastAPI)

### FastAPI / Pydantic

**35. `@router.post("/analysis/{sku_id}/complete")`** — (analysis.py:307)
Decorator registering a POST endpoint. `{sku_id}` = path parameter extracted from URL automatically.

**36. `async def`** — (analysis.py:308)
Asynchronous function. FastAPI serves other requests while one awaits. Even with sync DB calls, async endpoints improve concurrency.

**37. `db: Session = Depends(get_db)`** — (analysis.py:313)
Dependency injection. `Depends(get_db)` creates a DB session, passes it to the function, closes it after response.

**38. `Query(default=30, ge=7, le=90)`** — (procurement.py:49)
Query parameter with validation. `ge` = greater-or-equal, `le` = less-or-equal. Invalid values return 422 error.

**39. `class AssistantRequest(BaseModel)`** — (assistant.py:19)
Pydantic model for request validation. FastAPI validates incoming JSON against this schema automatically. Wrong types or missing fields = 422 error.

**40. `Optional[Dict[str, Any]] = None`** — (assistant.py:21)
Type hint: dict with string keys and any values, or None. `= None` makes it optional.

**41. `HTTPException(status_code=404, detail=...)`** — (analysis.py:38)
Returns error response. 404 = not found, 400 = bad request, 500 = server error.

**42. `response_model=List[InventorySummaryResponse]`** — (inventory.py:24)
Validates and serializes response. Strips extra fields, converts types, generates OpenAPI docs.

### SQLAlchemy

**43. `db.query(SKU).filter(SKU.id == sku_id).first()`** — (analysis.py:325)
ORM query. `query(SKU)` = SELECT from skus. `.filter()` = WHERE. `.first()` = LIMIT 1 (returns object or None).

**44. `.join(Supplier, SKUSupplier.supplier_id == Supplier.id)`** — (inventory.py:49)
SQL JOIN. Connects tables on matching IDs. Returns combined results.

**45. `.order_by(SalesHistory.date).all()`** — (analysis.py:357)
ORDER BY clause. `.all()` returns list of all matches (vs `.first()` for one).

**46. `func.avg(SalesHistory.quantity_sold)`** — (inventory.py:61)
SQL AVG() function via SQLAlchemy. `.scalar()` extracts the single value.

**47. `yield db` in `get_db()`** — (database.py)
Generator function. `yield` pauses, gives db to caller, resumes when done. `finally: db.close()` ensures cleanup. FastAPI's `Depends` handles this pattern.

**48. `Base = declarative_base()`** — (database.py)
Base class for all ORM models. `class SKU(Base)` maps to database table via `__tablename__`.

**49. `Column(String(50), ForeignKey("skus.id"), nullable=False, index=True)`** — (sales_history.py:23)
Database column: String(50 chars), references skus.id, cannot be NULL, indexed for fast lookups.

**50. `UniqueConstraint('sku_id', 'date')`** — (sales_history.py:16)
Database-level constraint: no duplicate rows with same sku_id AND date. Enforced by the database, not app code.

**51. `relationship("SKU", back_populates="inventory")`** — (inventory.py:31)
ORM relationship. `inventory.sku` gives the related SKU object. `back_populates` creates the reverse link.

**52. `pool_pre_ping=True, pool_size=5`** — (database.py)
Connection pool settings. `pool_pre_ping` tests connections before using (catches stale ones). `pool_size=5` keeps 5 ready.

### FastAPI App Setup

**53. `CORSMiddleware` with `allow_origins=["*"]`** — (main.py:35-41)
Cross-Origin Resource Sharing. Browsers block requests between different origins (localhost:5173 to localhost:8000). This middleware permits it. `"*"` = allow any origin.

**54. `@app.on_event("startup")`** — (main.py:44)
Runs code when app starts. Used to test DB connection and log config. Runs once before any requests.

**55. `app.include_router(router, prefix="/api")`** — (main.py:107)
Mounts sub-router. All routes get `/api` prefix. `tags` groups endpoints in Swagger docs.

**56. `uvicorn.run("api.main:app", host="0.0.0.0", reload=True)`** — (main.py:117)
Starts the ASGI server. `"api.main:app"` = module path to FastAPI instance. `"0.0.0.0"` = listen on all interfaces. `reload=True` = auto-restart on code changes.

### Python / numpy / sklearn

**57. `np.mean(data[:30])`** — (scenario_runner.py:203)
Average of first 30 elements. `data[:30]` = slice from index 0 to 29.

**58. `np.sqrt(mean_squared_error(y_val, y_pred))`** — (ml_forecaster.py:162)
RMSE. `mean_squared_error` gives MSE, `sqrt` converts to same units as data.

**59. `mean_absolute_error(y_val, y_pred)`** — (ml_forecaster.py:158)
Average of absolute differences between predicted and actual. MAE of 2.44 = predictions off by 2.44 units on average.

**60. `RandomForestRegressor(n_estimators=100, max_depth=10, n_jobs=-1)`** — (ml_forecaster.py:142)
100 decision trees, max depth 10 (prevents overfitting), use all CPU cores (`-1`).

**61. `model.fit(X_train, y_train)`** — (ml_forecaster.py:151)
Trains the model. X_train = feature matrix, y_train = target values. After this, model has "learned" patterns.

**62. `model.predict(X)[0]`** — (ml_forecaster.py:226)
Predicts using trained model. `X` = one row of features. `.predict()` returns array, `[0]` extracts single value.

**63. `df['lag_1'] = df['demand'].shift(1)`** — (ml_forecaster.py:62)
Creates feature where each value = previous row's demand. `shift(7)` = 7 days ago. No data leakage: day N only sees past data.

**64. `.rolling(window=7, min_periods=3).mean()`** — (ml_forecaster.py:67)
Rolling window average over last 7 values. `min_periods=3` = still calculates with fewer than 7 values.

**65. `df.dropna()`** — (ml_forecaster.py:78)
Removes rows with NaN values. Lag/rolling features create NaN in first rows (no "previous day" for first record).

**66. `int(len(df) * 0.8)` — chronological split** — (ml_forecaster.py:121)
80/20 split by time order (first 80% train, last 20% test). Critical for time-series: random splitting = data leakage.

**67. List comprehension** — `[float(s.quantity_sold) for s in sales]` (analysis.py:365)
Creates list by transforming each item. Equivalent to for loop but concise.

**68. f-string** — `f"SKU {sku_id} not found"` (analysis.py:327)
Formatted string. Variables inside `{}` are evaluated. Cleaner than concatenation.

**69. `@property` + `@abstractmethod`** — (tools/base.py)
`@property` = access method like attribute (`tool.input_schema` not `tool.input_schema()`). `@abstractmethod` = subclass must implement it.

**70. `ABC` (Abstract Base Class)** — `class Tool(ABC)` (tools/base.py)
Cannot be instantiated. Forces subclasses to implement all abstract methods. Ensures every Tool has `_execute`, `input_schema`, `output_schema`.

**71. `class AgentDecisionType(str, Enum)`** — (agents/base.py)
Enum inheriting from str. Values are strings ("reorder", "monitor") but behave as enum members. `str` makes them JSON-serializable.

### Architecture Patterns

**72. Tool Registry** — `tool_registry.register(ForecastDemandTool)` (analytics_tools.py:278)
Global dict mapping names to classes. Allows runtime discovery: `tool_registry.get("ForecastDemandTool")`.

**73. `self.use_tool(tool, **kwargs)`** in Skill — (demand_analysis_skill.py:62)
Skill invokes a Tool. Tracks usage in `self.tools_used`. Provides audit trail of execution chain.

**74. `self.use_skill(skill, **kwargs)`** in Agent — (inventory_agent.py:81)
Agent invokes a Skill. Same pattern one level up. Creates full chain: Agent -> Skill -> Tool.

**75. `convert_numpy_types(obj)`** — (api/utils.py)
Recursively converts numpy types (np.int64, np.float64, np.bool_) to Python native types. FastAPI's JSON encoder can't serialize numpy types.

### Ollama / Assistant

**76. `"stream": False`** — (ollama_provider.py:143)
Ollama response mode. `False` = wait for complete answer. `True` = stream chunks as generated (like ChatGPT typing).

**77. `"think": False`** — (ollama_provider.py:144)
Qwen3-specific. Disables internal reasoning tokens before answer. Reduces latency from 10-20s to 3-5s.

**78. `.ilike(f'%{query}%')`** — (stockpilot_assistant.py)
Case-insensitive SQL LIKE. Matches records where field contains the query string. This is the "R" (Retrieval) in our lightweight RAG.

---

## GENERAL / INFRASTRUCTURE

**79. `axios`** — Frontend HTTP client library. Like Python's `requests`. Automatic JSON parsing, baseURL config, interceptors.

**80. `uvicorn`** — ASGI server. Receives HTTP requests and passes to FastAPI. Relationship: uvicorn (server) -> FastAPI (framework) -> your code (handlers).
