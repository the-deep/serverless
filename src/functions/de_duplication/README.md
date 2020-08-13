## API
### Query Params
- `project`: **number**. Project Id to which the lead belongs
- `source_key`: **string** generated using website url or s3 url of the lead

### Response
```json
{
    "results": [
        { "lead_id": 1, "similarity_score": 0.8 },
        { "lead_id": 2, "similarity_score": 0.7 },
        ...
    ],
    "max_score": 0.8
}
```

## Lambda Environment
- `ES_ENDPOINT`: The aws endpoint of the elasticsearch api.
- `AWS_REGION`: Region where the elasticsearch is deployed. Defaults to `us-east-1`
