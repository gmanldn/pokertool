# SmartHelper API Documentation

**Version:** 100.3.0
**Base URL:** `http://localhost:8000` (development)
**Author:** PokerTool Team
**Created:** 2025-10-22

SmartHelper provides real-time poker decision assistance using GTO strategy, opponent profiling, and exploitative adjustments. This API powers the SmartHelper frontend with recommendations, equity calculations, and live updates via WebSocket.

---

## Table of Contents

1. [Authentication](#authentication)
2. [REST Endpoints](#rest-endpoints)
   - [POST /api/smarthelper/recommend](#post-apismarthelperrecommend)
   - [GET /api/smarthelper/factors](#get-apismarthelperfactors)
   - [POST /api/smarthelper/equity](#post-apismarthelperequity)
3. [WebSocket API](#websocket-api)
   - [Connection](#websocket-connection)
   - [Message Types](#websocket-message-types)
4. [Data Models](#data-models)
5. [Error Handling](#error-handling)
6. [Rate Limiting](#rate-limiting)
7. [Caching](#caching)

---

## Authentication

All SmartHelper endpoints require user authentication via JWT tokens or session cookies.

**Required Headers:**
```http
Authorization: Bearer <jwt_token>
```

**Permissions Required:**
- `USE_AI_ANALYSIS` - For recommendation and equity endpoints
- `USE_AI_CHAT` - For chat-based features (future)

---

## REST Endpoints

### POST /api/smarthelper/recommend

Get a strategic recommendation for the current poker situation.

**Endpoint:** `/api/smarthelper/recommend`
**Method:** `POST`
**Permission:** `USE_AI_ANALYSIS`

#### Request Body

```json
{
  "heroCards": ["As", "Kh"],
  "communityCards": ["Qh", "Jd", "9c"],
  "heroPosition": "BTN",
  "heroStack": 1000.0,
  "potSize": 150.0,
  "betToCall": 50.0,
  "street": "flop",
  "opponents": [
    {
      "name": "Villain1",
      "position": "BB",
      "stack": 800.0,
      "vpip": 28.5,
      "pfr": 22.0,
      "aggression": 1.8,
      "player_type": "TAG"
    }
  ],
  "actionHistory": [
    {
      "player": "Hero",
      "action": "RAISE",
      "amount": 30.0,
      "street": "preflop"
    },
    {
      "player": "Villain1",
      "action": "CALL",
      "amount": 30.0,
      "street": "preflop"
    }
  ]
}
```

**Field Descriptions:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `heroCards` | `string[]` | Yes | Hero's hole cards (e.g., `["As", "Kh"]`) |
| `communityCards` | `string[]` | No | Community cards (empty for preflop) |
| `heroPosition` | `string` | Yes | Position: `UTG`, `MP`, `CO`, `BTN`, `SB`, `BB` |
| `heroStack` | `number` | Yes | Hero's remaining stack in chips |
| `potSize` | `number` | Yes | Current pot size |
| `betToCall` | `number` | No | Amount to call (0 if first to act) |
| `street` | `string` | Yes | Current street: `preflop`, `flop`, `turn`, `river` |
| `opponents` | `Opponent[]` | No | Array of opponent profiles |
| `actionHistory` | `Action[]` | No | Previous actions in this hand |

#### Response

```json
{
  "action": "RAISE",
  "amount": 125.0,
  "confidence": 78.5,
  "net_confidence": 73.2,
  "strategic_reasoning": "Strong hand with excellent equity against villain's range. Villain folds to c-bets 65% - exploit with aggressive betting.",
  "factors": [
    {
      "name": "hand_strength",
      "score": 85.0,
      "weight": 0.30,
      "description": "Top pair with nut flush draw"
    },
    {
      "name": "pot_odds",
      "score": 72.0,
      "weight": 0.25,
      "description": "Getting 4:1 pot odds, need 20% equity"
    },
    {
      "name": "opponent_tendency",
      "score": 68.0,
      "weight": 0.20,
      "description": "Villain folds to c-bet 65% of the time"
    }
  ],
  "gto_frequencies": {
    "fold": 5.0,
    "check": 0.0,
    "call": 20.0,
    "bet": 60.0,
    "raise": 15.0,
    "all_in": 0.0
  },
  "equity": {
    "hero_equity": 68.5,
    "villain_equity": 31.5,
    "tie_equity": 0.0
  },
  "exploitative_adjustment": {
    "enabled": true,
    "weight": 35.0,
    "adjustments": [
      "Increased bet frequency vs tight folder"
    ]
  },
  "calculation_time_ms": 45.2,
  "cache_hit": false
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `action` | `string` | Recommended action: `FOLD`, `CHECK`, `CALL`, `BET`, `RAISE`, `ALL_IN` |
| `amount` | `number` | Bet/raise amount (null for fold/check/call) |
| `confidence` | `number` | Raw confidence (0-100%) |
| `net_confidence` | `number` | Adjusted confidence after exploitative weighting |
| `strategic_reasoning` | `string` | Human-readable explanation |
| `factors` | `Factor[]` | Decision factors with scores and weights |
| `gto_frequencies` | `object` | GTO action frequencies (%) |
| `equity` | `object` | Equity breakdown |
| `exploitative_adjustment` | `object` | Exploitative adjustments applied |
| `calculation_time_ms` | `number` | Computation time |
| `cache_hit` | `boolean` | Whether result was cached |

#### Example cURL

```bash
curl -X POST http://localhost:8000/api/smarthelper/recommend \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "heroCards": ["As", "Kh"],
    "communityCards": ["Qh", "Jd", "9c"],
    "heroPosition": "BTN",
    "heroStack": 1000.0,
    "potSize": 150.0,
    "betToCall": 50.0,
    "street": "flop",
    "opponents": [
      {"name": "Villain1", "position": "BB", "stack": 800.0}
    ]
  }'
```

---

### GET /api/smarthelper/factors

Retrieve available decision factors with their default weights.

**Endpoint:** `/api/smarthelper/factors`
**Method:** `GET`
**Permission:** `USE_AI_ANALYSIS`

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `street` | `string` | No | Filter by street: `preflop`, `flop`, `turn`, `river` |
| `position` | `string` | No | Filter by position: `UTG`, `MP`, `CO`, `BTN`, `SB`, `BB` |

#### Response

```json
{
  "factors": [
    {
      "name": "hand_strength",
      "display_name": "Hand Strength",
      "description": "Relative strength of hero's hand vs villain's range",
      "default_weight": 0.30,
      "category": "equity",
      "applicable_streets": ["preflop", "flop", "turn", "river"],
      "range": [0.0, 100.0]
    },
    {
      "name": "pot_odds",
      "display_name": "Pot Odds",
      "description": "Price being offered to continue in the hand",
      "default_weight": 0.25,
      "category": "math",
      "applicable_streets": ["preflop", "flop", "turn", "river"],
      "range": [0.0, 100.0]
    },
    {
      "name": "opponent_tendency",
      "display_name": "Opponent Tendency",
      "description": "Exploitative adjustments based on opponent stats",
      "default_weight": 0.20,
      "category": "exploitative",
      "applicable_streets": ["preflop", "flop", "turn", "river"],
      "range": [0.0, 100.0]
    },
    {
      "name": "position",
      "display_name": "Positional Advantage",
      "description": "Advantage from acting last",
      "default_weight": 0.15,
      "category": "strategic",
      "applicable_streets": ["preflop", "flop", "turn", "river"],
      "range": [0.0, 100.0]
    },
    {
      "name": "stack_to_pot_ratio",
      "display_name": "Stack-to-Pot Ratio",
      "description": "Remaining stack relative to pot size (SPR)",
      "default_weight": 0.10,
      "category": "math",
      "applicable_streets": ["preflop", "flop", "turn", "river"],
      "range": [0.0, 20.0]
    }
  ],
  "total_weight": 1.0
}
```

#### Example cURL

```bash
curl -X GET "http://localhost:8000/api/smarthelper/factors?street=flop" \
  -H "Authorization: Bearer <token>"
```

---

### POST /api/smarthelper/equity

Calculate equity for hero's hand vs opponent's hand or range.

**Endpoint:** `/api/smarthelper/equity`
**Method:** `POST`
**Permission:** `USE_AI_ANALYSIS`

#### Request Body

```json
{
  "heroCards": ["As", "Kh"],
  "villainCards": ["Qd", "Qc"],
  "villainRange": null,
  "communityCards": ["Jh", "Ts", "9d"],
  "num_simulations": 10000
}
```

**Field Descriptions:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `heroCards` | `string[]` | Yes | Hero's hole cards |
| `villainCards` | `string[]` | Conditional | Villain's specific hand (or use `villainRange`) |
| `villainRange` | `string[]` | Conditional | Villain's hand range (e.g., `["AA", "KK", "AKs"]`) |
| `communityCards` | `string[]` | No | Board cards (can be partial or empty) |
| `num_simulations` | `number` | No | Monte Carlo simulations (default: 10,000) |

**Note:** Either `villainCards` or `villainRange` must be provided, but not both.

#### Response

```json
{
  "hero_equity": 68.45,
  "villain_equity": 31.35,
  "tie_equity": 0.20,
  "simulations_run": 10000,
  "calculation_time_ms": 124.5,
  "equity_category": "Very Strong",
  "board_texture": {
    "straight_possible": true,
    "flush_possible": false,
    "paired": false
  }
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `hero_equity` | `number` | Hero's win probability (%) |
| `villain_equity` | `number` | Villain's win probability (%) |
| `tie_equity` | `number` | Tie probability (%) |
| `simulations_run` | `number` | Number of simulations executed |
| `calculation_time_ms` | `number` | Computation time |
| `equity_category` | `string` | Category: `Very Strong`, `Strong`, `Medium`, `Weak`, `Very Weak` |
| `board_texture` | `object` | Board analysis |

#### Example cURL

```bash
curl -X POST http://localhost:8000/api/smarthelper/equity \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "heroCards": ["As", "Kh"],
    "villainRange": ["QQ", "JJ", "TT", "AQ", "AJ"],
    "communityCards": ["Jh", "Ts", "9d"],
    "num_simulations": 10000
  }'
```

---

## WebSocket API

### WebSocket Connection

Real-time updates are delivered via WebSocket for live table monitoring.

**Endpoint:** `ws://localhost:8000/ws/smarthelper`
**Protocol:** WebSocket

#### Connection Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `connection_id` | Yes | Unique connection identifier |
| `user_id` | Yes | Authenticated user ID |
| `table_id` | No | Specific table to subscribe to |

#### Connection URL Example

```
ws://localhost:8000/ws/smarthelper?connection_id=conn-123456&user_id=user-789&table_id=table-abc
```

#### Connection Flow

1. **Client initiates connection** with query parameters
2. **Server sends `connection_ack`** confirming connection
3. **Server flushes queued messages** (if any from previous disconnection)
4. **Heartbeat begins** - Client sends `ping` every 30s, server responds with `pong`
5. **Server broadcasts updates** - Recommendations, table state, equity updates

#### Reconnection

- **Auto-reconnect:** Client should implement exponential backoff
- **Max attempts:** 5 (configurable)
- **Reconnect interval:** 3 seconds (default)
- **Message queue:** Server queues up to 100 messages during disconnection

---

### WebSocket Message Types

All WebSocket messages follow this structure:

```json
{
  "type": "message_type",
  "data": { ... },
  "timestamp": 1698765432000,
  "session_id": "session-xyz"
}
```

#### 1. connection_ack

Sent by server immediately after connection.

```json
{
  "type": "connection_ack",
  "data": {
    "connection_id": "conn-123456",
    "user_id": "user-789",
    "table_id": "table-abc",
    "timestamp": 1698765432000
  },
  "timestamp": 1698765432000
}
```

#### 2. recommendation

Broadcast when new recommendation is calculated.

```json
{
  "type": "recommendation",
  "data": {
    "action": "RAISE",
    "amount": 125.0,
    "confidence": 78.5,
    "strategic_reasoning": "...",
    "factors": [...],
    "gto_frequencies": {...}
  },
  "timestamp": 1698765432123,
  "session_id": "session-xyz"
}
```

#### 3. table_state

Updates when table state changes (new cards, player actions).

```json
{
  "type": "table_state",
  "data": {
    "table_id": "table-abc",
    "street": "flop",
    "pot_size": 200.0,
    "community_cards": ["Qh", "Jd", "9c"],
    "active_players": 4
  },
  "timestamp": 1698765432456
}
```

#### 4. equity_update

Real-time equity calculation updates.

```json
{
  "type": "equity_update",
  "data": {
    "hero_equity": 68.5,
    "villain_equity": 31.5,
    "outs": 12,
    "equity_category": "Strong"
  },
  "timestamp": 1698765432789
}
```

#### 5. factor_update

Updates to decision factor scores.

```json
{
  "type": "factor_update",
  "data": {
    "factor_name": "opponent_tendency",
    "score": 72.0,
    "description": "Villain folding more frequently"
  },
  "timestamp": 1698765433000
}
```

#### 6. ping / pong

Heartbeat mechanism for connection health.

**Client sends:**
```json
{
  "type": "ping",
  "timestamp": 1698765433111
}
```

**Server responds:**
```json
{
  "type": "pong",
  "data": {
    "timestamp": 1698765433112
  },
  "timestamp": 1698765433112
}
```

**Latency calculation:** `server_timestamp - client_timestamp`

#### 7. error

Error messages from server.

```json
{
  "type": "error",
  "data": {
    "error": "Invalid game state",
    "code": "INVALID_STATE",
    "details": "Hero cards cannot be empty"
  },
  "timestamp": 1698765433333
}
```

---

## Data Models

### Card Notation

Cards are represented as 2-character strings:
- **Rank:** `2`, `3`, `4`, `5`, `6`, `7`, `8`, `9`, `T`, `J`, `Q`, `K`, `A`
- **Suit:** `c` (clubs), `d` (diamonds), `h` (hearts), `s` (spades)

**Examples:** `As` (Ace of spades), `Kh` (King of hearts), `Tc` (Ten of clubs)

### Hand Notation

Preflop hands use standard poker notation:
- **Pairs:** `AA`, `KK`, `QQ`, ..., `22`
- **Suited:** `AKs`, `KQs`, `T9s`, etc.
- **Offsuit:** `AKo`, `KQo`, `T9o`, etc.

### Position

Valid positions: `UTG`, `MP`, `CO`, `BTN`, `SB`, `BB`

### Street

Valid streets: `preflop`, `flop`, `turn`, `river`

### Action Types

Valid actions: `FOLD`, `CHECK`, `CALL`, `BET`, `RAISE`, `ALL_IN`

### Player Types

Classification based on VPIP/PFR:
- `LAG` - Loose Aggressive (VPIP > 25%, PFR > 20%)
- `TAG` - Tight Aggressive (VPIP 15-25%, PFR 12-20%)
- `LP` - Loose Passive (VPIP > 25%, PFR < 15%)
- `TP` - Tight Passive (VPIP < 20%, PFR < 12%)
- `BALANCED` - Balanced (moderate stats)

---

## Error Handling

### HTTP Status Codes

| Code | Description |
|------|-------------|
| `200` | Success |
| `400` | Bad Request - Invalid input parameters |
| `401` | Unauthorized - Missing or invalid authentication |
| `403` | Forbidden - Insufficient permissions |
| `429` | Too Many Requests - Rate limit exceeded |
| `500` | Internal Server Error |

### Error Response Format

```json
{
  "error": "Invalid game state",
  "code": "INVALID_HERO_CARDS",
  "details": "Hero cards must be exactly 2 cards",
  "timestamp": 1698765434000
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| `INVALID_HERO_CARDS` | Hero cards format invalid |
| `INVALID_COMMUNITY_CARDS` | Community cards format invalid |
| `INVALID_POSITION` | Position not recognized |
| `INVALID_STREET` | Street not recognized |
| `MISSING_REQUIRED_FIELD` | Required field missing from request |
| `DUPLICATE_CARDS` | Same card appears multiple times |
| `INSUFFICIENT_PERMISSIONS` | User lacks required permission |
| `RATE_LIMIT_EXCEEDED` | Too many requests |

---

## Rate Limiting

SmartHelper API implements rate limiting to prevent abuse:

- **Recommendation endpoint:** 60 requests/minute per user
- **Equity endpoint:** 120 requests/minute per user
- **Factors endpoint:** 180 requests/minute per user (cached heavily)

**Rate limit headers:**
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1698765500
```

---

## Caching

SmartHelper uses Redis caching for performance:

| Endpoint | Cache Key | TTL | Strategy |
|----------|-----------|-----|----------|
| `/recommend` | `rec:{game_state_hash}` | 5s | SHA256 hash of game state |
| `/equity` | `equity:{cards_hash}` | 30s | SHA256 hash of hero+villain+board |
| `/factors` | `factors:{street}:{position}` | 1h | Direct key |
| GTO solutions | `gto:{scenario_hash}` | 24h | SHA256 hash of GTO scenario |

**Cache headers:**
```http
X-Cache-Hit: true
X-Cache-Age: 2.3
```

**Cache invalidation:**
- Manual: `DELETE /api/cache/clear?type=recommendations`
- Automatic: TTL expiration
- Pattern-based: `rec:*`, `equity:*`, etc.

---

## Usage Examples

### React Integration

```typescript
import { useSmartHelperWebSocket } from '@/hooks/useSmartHelperWebSocket';

function SmartHelperPanel() {
  const { status, subscribe, sendMessage } = useSmartHelperWebSocket({
    url: 'ws://localhost:8000/ws/smarthelper',
    userId: currentUser.id,
    tableId: currentTable.id,
    autoConnect: true
  });

  useEffect(() => {
    const unsubscribe = subscribe('recommendation', (data) => {
      console.log('New recommendation:', data);
      setRecommendation(data);
    });

    return unsubscribe;
  }, [subscribe]);

  return (
    <div>
      <p>Connection: {status.connected ? 'Connected' : 'Disconnected'}</p>
      <p>Latency: {status.latency}ms</p>
    </div>
  );
}
```

### Python Client

```python
import requests
import websocket

# REST API call
def get_recommendation(game_state, token):
    response = requests.post(
        'http://localhost:8000/api/smarthelper/recommend',
        headers={'Authorization': f'Bearer {token}'},
        json=game_state
    )
    return response.json()

# WebSocket connection
def connect_websocket(user_id, table_id):
    ws = websocket.WebSocket()
    ws.connect(f'ws://localhost:8000/ws/smarthelper?user_id={user_id}&table_id={table_id}')

    while True:
        message = ws.recv()
        data = json.loads(message)
        if data['type'] == 'recommendation':
            print(f"Action: {data['data']['action']}")
```

---

## Support

For issues or questions:
- **GitHub Issues:** [pokertool/issues](https://github.com/pokertool/pokertool/issues)
- **Documentation:** [docs/README.md](../README.md)
- **Email:** support@pokertool.com

---

**Last Updated:** 2025-10-22
**API Version:** v1.0.0
**Changelog:** See [CHANGELOG.md](../CHANGELOG.md)
