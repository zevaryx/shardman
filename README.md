<!-- Generator: Widdershins v4.0.1 -->

<h1 id="shardman">Shardman</h1>

A Discord shard manager to help with autoscaling shards based on load

> Scroll down for code samples, example requests and responses. Select a language for code samples from the tabs above or the mobile navigation menu.

<h1 id="shardman-default">Default</h1>

## connect_connect_get

<a id="opIdconnect_connect_get"></a>

> Code samples

```python
import requests
headers = {
  'Accept': 'application/json'
}

r = requests.get('/connect', params={
  'token': 'string'
}, headers = headers)

print(r.json())

```

`GET /connect`

*Connect*

<h3 id="connect_connect_get-parameters">Parameters</h3>

|Name|In|Type|Required|Description|
|---|---|---|---|---|
|token|query|string|true|none|

> Example responses

> 200 Response

```json
{
  "shard": 0,
  "max_shards": 0,
  "session_id": "string"
}
```

<h3 id="connect_connect_get-responses">Responses</h3>

|Status|Meaning|Description|Schema|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|[ConnectConfirmed](#schemaconnectconfirmed)|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|Too Many Shards|None|
|403|[Forbidden](https://tools.ietf.org/html/rfc7231#section-6.5.3)|Invalid Token|None|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|[HTTPValidationError](#schemahttpvalidationerror)|

<aside class="success">
This operation does not require authentication
</aside>

## beat_beat_get

<a id="opIdbeat_beat_get"></a>

> Code samples

```python
import requests
headers = {
  'Accept': 'application/json'
}

r = requests.get('/beat', params={
  'token': 'string',  'session_id': 'string'
}, headers = headers)

print(r.json())

```

`GET /beat`

*Beat*

<h3 id="beat_beat_get-parameters">Parameters</h3>

|Name|In|Type|Required|Description|
|---|---|---|---|---|
|token|query|string|true|none|
|session_id|query|string|true|none|

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

<h3 id="beat_beat_get-responses">Responses</h3>

|Status|Meaning|Description|Schema|
|---|---|---|---|
|204|[No Content](https://tools.ietf.org/html/rfc7231#section-6.3.5)|Successful Response|None|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|Too Many Shards|None|
|403|[Forbidden](https://tools.ietf.org/html/rfc7231#section-6.5.3)|Invalid Token|None|
|404|[Not Found](https://tools.ietf.org/html/rfc7231#section-6.5.4)|Session Not Found|None|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|[HTTPValidationError](#schemahttpvalidationerror)|

<aside class="success">
This operation does not require authentication
</aside>

# Schemas

<h2 id="tocS_ConnectConfirmed">ConnectConfirmed</h2>
<!-- backwards compatibility -->
<a id="schemaconnectconfirmed"></a>
<a id="schema_ConnectConfirmed"></a>
<a id="tocSconnectconfirmed"></a>
<a id="tocsconnectconfirmed"></a>

```json
{
  "shard": 0,
  "max_shards": 0,
  "session_id": "string"
}

```

ConnectConfirmed

### Properties

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|shard|integer|true|none|none|
|max_shards|integer|true|none|none|
|session_id|string|true|none|none|

<h2 id="tocS_HTTPValidationError">HTTPValidationError</h2>
<!-- backwards compatibility -->
<a id="schemahttpvalidationerror"></a>
<a id="schema_HTTPValidationError"></a>
<a id="tocShttpvalidationerror"></a>
<a id="tocshttpvalidationerror"></a>

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
|detail|[[ValidationError](#schemavalidationerror)]|false|none|none|

<h2 id="tocS_ValidationError">ValidationError</h2>
<!-- backwards compatibility -->
<a id="schemavalidationerror"></a>
<a id="schema_ValidationError"></a>
<a id="tocSvalidationerror"></a>
<a id="tocsvalidationerror"></a>

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
