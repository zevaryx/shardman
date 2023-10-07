<!-- Generator: Widdershins v4.0.1 -->

# Shardman

A Discord shard manager to help with autoscaling shards based on load

## How to use

On bot startup, make a request to `/connect` with the header `Authorization: <secret>`, where `<secret>` is the same as `SECRET` in your .env

Once you have connected with your shard, you'll need to make sure you make a request to `/beat` every few seconds, less than `MAX_SECONDS` specified in your .env

This will keep the shard alive and maintained in the manager, so new shards don't try to connect in its place.

## API documentation

**Note: all endpoints require the `Authorization: <secret>` header**

### `GET /connect`

```python
import requests
headers = {
  'Accept': 'application/json',
  'Authorization': 'SECRET',
}

r = requests.get('/connect', headers = headers)

print(r.json())

```

> Example responses

> 200 Response

```json
{
  "shard_id": 0,
  "max_shards": 0,
  "session_id": "string"
}
```

### Responses

|Status|Meaning|Description|Schema|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|ConnectConfirmed|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|No Shards Available|None|
|403|[Forbidden](https://tools.ietf.org/html/rfc7231#section-6.5.3)|Invalid Token|None|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|HTTPValidationError|

## `POST /beat`

```python
import requests
headers = {
  'Accept': 'application/json',
  'Authorization': 'SECRET',
}

r = requests.post('/beat', json={
  'session_id': 'string'
}, headers = headers)

print(r.json())

```

### Parameters

|Name|In|Type|Required|Description|
|---|---|---|---|---|
|session_id|data|string|true|Session ID provided by `/connect`|
|guild_count|data|int|false|Number of guilds the shard sees|
|latency|data|float|false|Current shard latency|
|extra|data|Any|false|Extra data to store for shard|

> Example responses

> 422 Response

```json
{
  "detail": [
    {
      "loc": [
        "string"
      ],
      "msg": "string",
      "type": "string"
    }
  ]
}
```

### Responses

|Status|Meaning|Description|Schema|
|---|---|---|---|
|204|[No Content](https://tools.ietf.org/html/rfc7231#section-6.3.5)|Successful Response|None|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|No Shards Available|None|
|403|[Forbidden](https://tools.ietf.org/html/rfc7231#section-6.5.3)|Invalid Token|None|
|404|[Not Found](https://tools.ietf.org/html/rfc7231#section-6.5.4)|Session Not Found|None|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|HTTPValidationError|

## Schemas

### ConnectConfirmed

```json
{
  "shard_id": 0,
  "max_shards": 0,
  "session_id": "string"
}

```

ConnectConfirmed

### Properties

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|shard_id|integer|true|none|Shard ID to connect with|
|max_shards|integer|true|none|Max number of shards|
|session_id|string|true|none|Session ID for `/beat`|

### HTTPValidationError

```json
{
  "detail": [
    {
      "loc": [
        "string"
      ],
      "msg": "string",
      "type": "string"
    }
  ]
}

```

HTTPValidationError

### Properties

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|detail|ValidationError|false|none|none

```json
{
  "loc": [
    "string"
  ],
  "msg": "string",
  "type": "string"
}

```

ValidationError

### Properties

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|loc|[anyOf]|true|none|none|

anyOf

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|string|false|none|none|

or

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|integer|false|none|none|

continued

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|msg|string|true|none|none|
|type|string|true|none|none|
