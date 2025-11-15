# LinkedIn API Scrapers

# Dataset list

> List all Dataset IDs of all Scraper APIs, you can use this API endpoint to retrieve a list of available datasets.

## OpenAPI

````yaml dca-api GET /datasets/list
paths:
  path: /datasets/list
  method: get
  servers:
    - url: https://api.brightdata.com
  request:
    security:
      - title: bearerAuth
        parameters:
          query: {}
          header:
            Authorization:
              type: http
              scheme: bearer
              description: >-
                Use your Bright Data API Key as a Bearer token in the
                Authorization header. 

                 Get API Key from: https://brightdata.com/cp/setting/users. 

                 **Example**:
                ```Authorization: Bearer
                b5648e1096c6442f60a6c4bbbe73f8d2234d3d8324554bd6a7ec8f3f251f07df```
          cookie: {}
    parameters:
      path: {}
      query: {}
      header: {}
      cookie: {}
    body: {}
  response:
    '200':
      application/json:
        schemaArray:
          - type: array
            items:
              allOf:
                - $ref: '#/components/schemas/DatasetListItem'
            example:
              - id: gd_l1vijqt9jfj7olije
                name: Crunchbase companies information
                size: 2300000
              - id: gd_l1vikfch901nx3by4
                name: Instagram - Profiles
                size: 620000000
        examples:
          example:
            value:
              - id: gd_l1vijqt9jfj7olije
                name: Crunchbase companies information
                size: 2300000
              - id: gd_l1vikfch901nx3by4
                name: Instagram - Profiles
                size: 620000000
        description: List of available datasets
    '401':
      application/json:
        schemaArray:
          - type: object
            properties:
              error:
                allOf:
                  - type: string
                    example: Unauthorized
        examples:
          example:
            value:
              error: Unauthorized
        description: Unauthorized - Invalid or missing API token
    '500':
      application/json:
        schemaArray:
          - type: object
            properties:
              error:
                allOf:
                  - type: string
                    example: Internal server error
        examples:
          example:
            value:
              error: Internal server error
        description: Internal server error
  deprecated: false
  type: path
components:
  schemas:
    DatasetListItem:
      type: object
      required:
        - id
        - name
        - size
      properties:
        id:
          type: string
          description: Unique identifier for the dataset
          example: gd_l1vijqt9jfj7olije
        name:
          type: string
          description: Human-readable name of the dataset
          example: Crunchbase companies information
        size:
          type: integer
          description: Number of records in the dataset
          example: 2300000

````

# Get Dataset Metadata

<Tip>
  Paste your API key to the authorization field. To get an API key, [Create an account](https://brightdata.com/?hs_signup=1\&utm_source=docs\&utm_campaign=playground) and learn [how to generate an API key](/api-reference/authentication#how-do-i-generate-a-new-api-key%3F).
</Tip>

## General Description

* This endpoint retrieves detailed metadata for a specific dataset.
* Metadata includes available fields, data types, and descriptions.
* Use this endpoint to understand the structure of a dataset before querying or downloading it.

## Request

### **Endpoint**

```
GET http://api.brightdata.com/datasets/{dataset_id}/metadata
```

### **Path Parameters**

| Parameter    | Type     | Description                          |
| ------------ | -------- | ------------------------------------ |
| `dataset_id` | `string` | The unique identifier of the dataset |

### **Headers**

| Header          | Type   | Description                     |
| --------------- | ------ | ------------------------------- |
| `Authorization` | string | Your API key for authentication |

## Response

### **Response Example**

```json  theme={null}
{
    "id": "gd_l1vijqt9jfj7olije",
    "fields": {
        "name": {
            "type": "text",
            "active": true,
            "description": "The name of the company"
        },
        "url": {
            "type": "url",
            "required": true,
            "description": "The URL or web address associated with the company"
        },
        "cb_rank": {
            "type": "number",
            "description": "Crunchbase rank assigned to the company"
        }
    }
}
```

### **Response Fields**

| Field    | Type     | Description                                       |
| -------- | -------- | ------------------------------------------------- |
| `id`     | `string` | Unique identifier for the dataset                 |
| `fields` | `object` | Contains metadata about each field in the dataset |

### **Field Metadata**

Each field in the `fields` object contains the following attributes:

| Attribute     | Type      | Description                                            |
| ------------- | --------- | ------------------------------------------------------ |
| `type`        | `string`  | Data type of the field (e.g., `text`, `number`, `url`) |
| `active`      | `boolean` | Indicates if the field is currently active             |
| `required`    | `boolean` | Indicates if the field is mandatory (if applicable)    |
| `description` | `string`  | Brief description of the field                         |

## Example Use Case

### **Fetching Dataset Metadata**

To retrieve metadata for the "Crunchbase companies information" dataset:

#### **Request**

```
GET http://api.brightdata.com/datasets/gd_l1vijqt9jfj7olije/metadata
```

#### **Response**

```json  theme={null}
{
    "id": "gd_l1vijqt9jfj7olije",
    "fields": {
        "name": {
            "type": "text",
            "active": true,
            "description": "The name of the company"
        },
        "url": {
            "type": "url",
            "required": true,
            "description": "The URL or web address associated with the company"
        },
        "cb_rank": {
            "type": "number",
            "description": "Crunchbase rank assigned to the company"
        }
    }
}
```

## Troubleshooting & FAQs

### **Issue: "Unauthorized" response**

**Solution**: Ensure you have included a valid API key in the request header.

### **Issue: "Dataset not found"**

**Solution**: Verify that the `dataset_id` is correct and exists in the dataset list.

### **Issue: "Field missing in metadata"**

**Solution**: Some fields may be inactive or unavailable for certain datasets.

## Related Documentation

* [Get Dataset List](/api-reference/marketplace-dataset-api/get-dataset-list)
* [Dataset Filtering API](/api-reference/marketplace-dataset-api/filter-dataset-with-csv-json-files)
* [Dataset Download API](/datasets/scrapers/custom-scrapers/custom-dataset-api)

# Filter Dataset (BETA)

> Create a dataset snapshot based on a provided filter

## OpenAPI

````yaml dca-api POST /datasets/filter
paths:
  path: /datasets/filter
  method: post
  servers:
    - url: https://api.brightdata.com
  request:
    security:
      - title: bearerAuth
        parameters:
          query: {}
          header:
            Authorization:
              type: http
              scheme: bearer
              description: >-
                Use your Bright Data API Key as a Bearer token in the
                Authorization header. 

                 Get API Key from: https://brightdata.com/cp/setting/users. 

                 **Example**:
                ```Authorization: Bearer
                b5648e1096c6442f60a6c4bbbe73f8d2234d3d8324554bd6a7ec8f3f251f07df```
          cookie: {}
    parameters:
      path: {}
      query:
        dataset_id:
          schema:
            - type: string
              required: false
              description: >-
                ID of the dataset to filter (required in multipart/form-data
                mode)
              example: gd_l1viktl72bvl7bjuj0
        records_limit:
          schema:
            - type: integer
              required: false
              description: Limit the number of records to be included in the snapshot
              example: 1000
      header: {}
      cookie: {}
    body:
      application/json:
        schemaArray:
          - type: object
            properties:
              dataset_id:
                allOf:
                  - type: string
                    description: ID of the dataset to filter
                    example: gd_l1viktl72bvl7bjuj0
              records_limit:
                allOf:
                  - type: integer
                    description: Limit the number of records to be included in the snapshot
                    example: 1000
              filter:
                allOf:
                  - $ref: '#/components/schemas/DatasetFilter'
            required: true
            requiredProperties:
              - dataset_id
              - filter
        examples:
          example:
            value:
              dataset_id: gd_l1viktl72bvl7bjuj0
              records_limit: 1000
              filter:
                name: name
                operator: '='
                value: John
      multipart/form-data:
        schemaArray:
          - type: object
            properties:
              filter:
                allOf:
                  - $ref: '#/components/schemas/DatasetFilter'
            required: true
            refIdentifier: '#/components/schemas/FilterDatasetBody'
            requiredProperties:
              - filter
        examples:
          example:
            value:
              filter:
                name: name
                operator: '='
                value: John
  response:
    '200':
      application/json:
        schemaArray:
          - type: object
            properties:
              snapshot_id:
                allOf:
                  - type: string
                    description: ID of the snapshot
        examples:
          example:
            value:
              snapshot_id: <string>
        description: Job of creating the snapshot successfully started
    '400':
      application/json:
        schemaArray:
          - type: object
            properties:
              validation_errors:
                allOf:
                  - type: array
                    items:
                      type: string
            refIdentifier: '#/components/schemas/ValidationErrorBody'
        examples:
          example:
            value:
              validation_errors:
                - '"filter.filters[0].invalid_prop" is not allowed'
                - '"records_limit" must be a positive number'
        description: Bad request
    '402':
      application/json:
        schemaArray:
          - type: object
            properties:
              error:
                allOf:
                  - &ref_0
                    type: string
            refIdentifier: '#/components/schemas/ErrorBody'
        examples:
          example:
            value:
              error: >-
                Your current balance is insufficient to process this data
                collection request. Please add funds to your account or adjust
                your request to continue. ($1 is missing)
        description: Not enough funds to create the snapshot
    '422':
      application/json:
        schemaArray:
          - type: object
            properties:
              error:
                allOf:
                  - *ref_0
            refIdentifier: '#/components/schemas/ErrorBody'
        examples:
          example:
            value:
              error: Provided filter did not match any records
        description: Provided filter did not match any records
    '429':
      application/json:
        schemaArray:
          - type: object
            properties:
              error:
                allOf:
                  - *ref_0
            refIdentifier: '#/components/schemas/ErrorBody'
        examples:
          example:
            value:
              error: Maximum limit of 100 jobs per dataset has been exceeded
        description: Too many parallel jobs
  deprecated: false
  type: path
components:
  schemas:
    DatasetFilter:
      anyOf:
        - $ref: '#/components/schemas/DatasetFilterItem'
          title: Single field filter
        - $ref: '#/components/schemas/DatasetFilterGroup'
          title: Filters group
        - $ref: '#/components/schemas/DatasetFilterItemNoVal'
          title: Single field filter w/out value
    DatasetFilterGroup:
      type: object
      required:
        - operator
        - filters
      additionalProperties: false
      properties:
        operator:
          type: string
          enum:
            - and
            - or
        combine_nested_fields:
          type: boolean
          description: >-
            For arrays of objects: if true, all filters must match within a
            single object
        filters:
          type: array
          items:
            $ref: '#/components/schemas/DatasetFilter'
      example:
        operator: and
        filters:
          - name: name
            operator: '='
            value: John
          - name: age
            operator: '>'
            value: '30'
    DatasetFilterItem:
      type: object
      required:
        - name
        - operator
        - value
      additionalProperties: false
      properties:
        name:
          type: string
          description: Field name to filter by
        operator:
          type: string
          enum:
            - '='
            - '!='
            - '>'
            - <
            - '>='
            - <=
            - in
            - not_in
            - includes
            - not_includes
            - array_includes
            - not_array_includes
        value:
          description: Value to filter by
          oneOf:
            - type: string
            - type: number
            - type: boolean
            - type: object
            - type: array
              items:
                oneOf:
                  - type: string
                  - type: number
                  - type: boolean
      example:
        name: name
        operator: '='
        value: John
    DatasetFilterItemNoVal:
      type: object
      required:
        - name
        - operator
      additionalProperties: false
      properties:
        name:
          type: string
          description: Field name to filter by
        operator:
          type: string
          enum:
            - is_null
            - is_not_null
      example:
        name: reviews_count
        operator: is_not_null

````

# Filter Dataset (JSON or File Uploads)

> Create a dataset snapshot based on a provided filter

## OpenAPI

````yaml filter-csv-json POST /datasets/filter
paths:
  path: /datasets/filter
  method: post
  servers:
    - url: https://api.brightdata.com
  request:
    security:
      - title: bearerAuth
        parameters:
          query: {}
          header:
            Authorization:
              type: http
              scheme: bearer
              description: >-
                Use your Bright Data API Key as a Bearer token in the
                Authorization header. 

                 Get API Key from: https://brightdata.com/cp/setting/users. 

                 **Example**:
                ```Authorization: Bearer
                b5648e1096c6442f60a6c4bbbe73f8d2234d3d8324554bd6a7ec8f3f251f07df```
          cookie: {}
    parameters:
      path: {}
      query:
        dataset_id:
          schema:
            - type: string
              required: true
              description: >-
                ID of the dataset to filter (required in multipart/form-data
                mode)
              example: gd_l1viktl72bvl7bjuj0
        records_limit:
          schema:
            - type: integer
              required: false
              description: Limit the number of records to be included in the snapshot
              example: 1000
      header: {}
      cookie: {}
    body:
      multipart/form-data:
        schemaArray:
          - type: object
            properties:
              filter:
                allOf:
                  - $ref: '#/components/schemas/DatasetFilter'
            required: true
            refIdentifier: '#/components/schemas/FilterDatasetBody'
            requiredProperties:
              - filter
        examples:
          example:
            value:
              filter:
                name: name
                operator: '='
                value: John
  response:
    '200':
      application/json:
        schemaArray:
          - type: object
            properties:
              snapshot_id:
                allOf:
                  - type: string
                    description: ID of the snapshot
        examples:
          example:
            value:
              snapshot_id: <string>
        description: Job of creating the snapshot successfully started
    '400':
      application/json:
        schemaArray:
          - type: object
            properties:
              validation_errors:
                allOf:
                  - type: array
                    items:
                      type: string
            refIdentifier: '#/components/schemas/ValidationErrorBody'
        examples:
          example:
            value:
              validation_errors:
                - '"filter.filters[0].invalid_prop" is not allowed'
                - '"records_limit" must be a positive number'
        description: Bad request
    '402':
      application/json:
        schemaArray:
          - type: object
            properties:
              error:
                allOf:
                  - &ref_0
                    type: string
            refIdentifier: '#/components/schemas/ErrorBody'
        examples:
          example:
            value:
              error: >-
                Your current balance is insufficient to process this data
                collection request. Please add funds to your account or adjust
                your request to continue. ($1 is missing)
        description: Not enough funds to create the snapshot
    '422':
      application/json:
        schemaArray:
          - type: object
            properties:
              error:
                allOf:
                  - *ref_0
            refIdentifier: '#/components/schemas/ErrorBody'
        examples:
          example:
            value:
              error: Provided filter did not match any records
        description: Provided filter did not match any records
    '429':
      application/json:
        schemaArray:
          - type: object
            properties:
              error:
                allOf:
                  - *ref_0
            refIdentifier: '#/components/schemas/ErrorBody'
        examples:
          example:
            value:
              error: Maximum limit of 100 jobs per dataset has been exceeded
        description: Too many parallel jobs
  deprecated: false
  type: path
components:
  schemas:
    DatasetFilter:
      anyOf:
        - $ref: '#/components/schemas/DatasetFilterItem'
          title: Single field filter
        - $ref: '#/components/schemas/DatasetFilterGroup'
          title: Filters group
        - $ref: '#/components/schemas/DatasetFilterItemNoVal'
          title: Single field filter w/out value
    DatasetFilterGroup:
      type: object
      required:
        - operator
        - filters
      additionalProperties: false
      properties:
        operator:
          type: string
          enum:
            - and
            - or
        combine_nested_fields:
          type: boolean
          description: >-
            For arrays of objects: if true, all filters must match within a
            single object
        filters:
          type: array
          items:
            $ref: '#/components/schemas/DatasetFilter'
      example:
        operator: and
        filters:
          - name: name
            operator: '='
            value: John
          - name: age
            operator: '>'
            value: '30'
    DatasetFilterItem:
      type: object
      required:
        - name
        - operator
        - value
      additionalProperties: false
      properties:
        name:
          type: string
          description: Field name to filter by
        operator:
          type: string
          enum:
            - '='
            - '!='
            - '>'
            - <
            - '>='
            - <=
            - in
            - not_in
            - includes
            - not_includes
            - array_includes
            - not_array_includes
        value:
          description: Value to filter by
          oneOf:
            - type: string
            - type: number
            - type: boolean
            - type: object
            - type: array
              items:
                oneOf:
                  - type: string
                  - type: number
                  - type: boolean
      example:
        name: name
        operator: '='
        value: John
    DatasetFilterItemNoVal:
      type: object
      required:
        - name
        - operator
      additionalProperties: false
      properties:
        name:
          type: string
          description: Field name to filter by
        operator:
          type: string
          enum:
            - is_null
            - is_not_null
      example:
        name: reviews_count
        operator: is_not_null

````

# Get Snapshot Metadata

> Get dataset snapshot metadata

## OpenAPI

````yaml dca-api GET /datasets/snapshots/{id}
paths:
  path: /datasets/snapshots/{id}
  method: get
  servers:
    - url: https://api.brightdata.com
  request:
    security:
      - title: bearerAuth
        parameters:
          query: {}
          header:
            Authorization:
              type: http
              scheme: bearer
              description: >-
                Use your Bright Data API Key as a Bearer token in the
                Authorization header. 

                 Get API Key from: https://brightdata.com/cp/setting/users. 

                 **Example**:
                ```Authorization: Bearer
                b5648e1096c6442f60a6c4bbbe73f8d2234d3d8324554bd6a7ec8f3f251f07df```
          cookie: {}
    parameters:
      path:
        id:
          schema:
            - type: string
              required: true
              description: >-
                A Snapshot ID is a unique identifier for a specific data
                snapshot, used to retrieve results from a data collection job
                triggered via the API. Read more about [Snapshot
                ID](/api-reference/terminology#snapshot-id).
              example: snap_m2bxug4e2o352v1jv1
      query: {}
      header: {}
      cookie: {}
    body: {}
  response:
    '200':
      application/json:
        schemaArray:
          - type: object
            properties:
              id:
                allOf:
                  - type: string
              created:
                allOf:
                  - type: string
                    format: date-time
              status:
                allOf:
                  - type: string
                    enum:
                      - scheduled
                      - building
                      - ready
                      - failed
              dataset_id:
                allOf:
                  - type: string
              customer_id:
                allOf:
                  - type: string
              dataset_size:
                allOf:
                  - type: integer
                    description: Number of records in the snapshot
              file_size:
                allOf:
                  - type: integer
                    description: Size of the snapshot file in bytes
              cost:
                allOf:
                  - type: number
              error:
                allOf:
                  - type: string
              error_code:
                allOf:
                  - type: string
              warning:
                allOf:
                  - type: string
              warning_code:
                allOf:
                  - type: string
              initiation_type:
                allOf:
                  - type: string
            refIdentifier: '#/components/schemas/DatasetSnapshotMeta'
        examples:
          example:
            value:
              id: <string>
              created: '2023-11-07T05:31:56Z'
              status: scheduled
              dataset_id: <string>
              customer_id: <string>
              dataset_size: 123
              file_size: 123
              cost: 123
              error: <string>
              error_code: <string>
              warning: <string>
              warning_code: <string>
              initiation_type: <string>
        description: OK
    '404':
      text/html:
        schemaArray:
          - type: string
            example: snapshot not found
        examples:
          example:
            value: snapshot not found
        description: Snapshot not found
  deprecated: false
  type: path
components:
  schemas: {}

````

# Get Snapshot Parts

> Get dataset snapshot delivery parts. All query parameters used here need to match those used when downloading the snapshot to get accurate parts

## OpenAPI

````yaml dca-api GET /datasets/snapshots/{id}/parts
paths:
  path: /datasets/snapshots/{id}/parts
  method: get
  servers:
    - url: https://api.brightdata.com
  request:
    security:
      - title: bearerAuth
        parameters:
          query: {}
          header:
            Authorization:
              type: http
              scheme: bearer
              description: >-
                Use your Bright Data API Key as a Bearer token in the
                Authorization header. 

                 Get API Key from: https://brightdata.com/cp/setting/users. 

                 **Example**:
                ```Authorization: Bearer
                b5648e1096c6442f60a6c4bbbe73f8d2234d3d8324554bd6a7ec8f3f251f07df```
          cookie: {}
    parameters:
      path:
        id:
          schema:
            - type: string
              required: true
              description: >-
                A Snapshot ID is a unique identifier for a specific data
                snapshot, used to retrieve results from a data collection job
                triggered via the API. Read more about [Snapshot
                ID](/api-reference/terminology#snapshot-id).
              example: s_m4x7enmven8djfqak
      query:
        format:
          schema:
            - type: enum<string>
              enum:
                - json
                - ndjson
                - jsonl
                - csv
              description: Format of the response
              default: json
        compress:
          schema:
            - type: boolean
              description: Whether or not the response will be compressed in gzip format
              default: false
        batch_size:
          schema:
            - type: integer
              description: Number of records that will be included in each response batch
      header: {}
      cookie: {}
    body: {}
  response:
    '200':
      application/json:
        schemaArray:
          - type: object
            properties:
              parts:
                allOf:
                  - type: number
            refIdentifier: '#/components/schemas/DatasetSnapshotParts'
        examples:
          example:
            value:
              parts: 123
        description: OK
    '400':
      text/html:
        schemaArray:
          - type: string
            example: Snapshot is not ready
        examples:
          example:
            value: Snapshot is not ready
        description: Snapshot is not ready
    '404':
      text/html:
        schemaArray:
          - type: string
            example: snapshot not found
        examples:
          example:
            value: snapshot not found
        description: Snapshot not found
  deprecated: false
  type: path
components:
  schemas: {}

````

# Snapshot Content

> Get dataset snapshot content

## OpenAPI

````yaml dca-api GET /datasets/snapshots/{id}/download
paths:
  path: /datasets/snapshots/{id}/download
  method: get
  servers:
    - url: https://api.brightdata.com
  request:
    security:
      - title: bearerAuth
        parameters:
          query: {}
          header:
            Authorization:
              type: http
              scheme: bearer
              description: >-
                Use your Bright Data API Key as a Bearer token in the
                Authorization header. 

                 Get API Key from: https://brightdata.com/cp/setting/users. 

                 **Example**:
                ```Authorization: Bearer
                b5648e1096c6442f60a6c4bbbe73f8d2234d3d8324554bd6a7ec8f3f251f07df```
          cookie: {}
    parameters:
      path:
        id:
          schema:
            - type: string
              required: true
              description: >-
                A Snapshot ID is a unique identifier for a specific data
                snapshot, used to retrieve results from a data collection job
                triggered via the API. Read more about [Snapshot
                ID](/api-reference/terminology#snapshot-id).
              example: snap_m2bxug4e2o352v1jv1
      query:
        format:
          schema:
            - type: enum<string>
              enum:
                - json
                - jsonl
                - csv
              description: Format of the response
        compress:
          schema:
            - type: boolean
              description: Compress the response in gzip format
              default: false
        batch_size:
          schema:
            - type: integer
              description: Number of records to include in each response batch
        part:
          schema:
            - type: integer
              description: Number of batch to return. The numbering starts from 1.
      header: {}
      cookie: {}
    body: {}
  response:
    '200':
      application/json:
        schemaArray:
          - type: object
            properties: {}
            refIdentifier: '#/components/schemas/DatasetSnapshotContent'
            example:
              about: >-
                Bitstamp is the world’s longest-running cryptocurrency exchange,
                continuously supporting the Bitcoin economy since 2011. With a
                proven track record and mature approach to the industry,
                Bitstamp provides a secure and transparent venue to over four
                million customers and enables partners to access emerging crypto
                markets through time-proven infrastructure. NMLS ID: 1905429
                View more on the NMLS website here:
                https://www.nmlsconsumeraccess.org/EntityDetails.aspx/COMPANY/1905429
              affiliated: []
              company_id: '2734818'
              company_size: 501-1,000 employees
              country_code: LU
              crunchbase_url: >-
                https://www.crunchbase.com/organization/bitstamp?utm_source=linkedin&utm_medium=referral&utm_campaign=linkedin_companies&utm_content=profile_cta_anon&trk=funding_crunchbase
              description: "Bitstamp | 30,341 followers on LinkedIn. World&#39;s longest-running crypto exchange | Bitstamp is the world’s longest-running cryptocurrency exchange, continuously supporting the Bitcoin economy since 2011. With a proven track record and mature approach to the industry, Bitstamp provides a secure and transparent venue to over four million customers and enables partners to access emerging crypto markets through time-proven infrastructure.\n\n\n\n\nNMLS ID:\t1905429\nView more on the NMLS website here: https://www.nmlsconsumeraccess.org/EntityDetails.aspx/COMPANY/1905429"
              employees:
                - img: >-
                    https://media.licdn.com/dms/image/D4E03AQGixwSI9R6RuQ/profile-displayphoto-shrink_100_100/0/1701888289576?e=2147483647&v=beta&t=JCC9EZgKl5VWFcV_qdHIlvE7ZScFDTQeMOcrMrmU5TA
                  link: https://ae.linkedin.com/in/jsgreenwood?trk=org-employees
                  subtitle: Executive leadership & digital transformation
                  title: James Greenwood
                - img: >-
                    https://media.licdn.com/dms/image/C4E03AQGD22qBJsQ-qw/profile-displayphoto-shrink_100_100/0/1524161393516?e=2147483647&v=beta&t=OSS74hoSvrpwsPjEuuF0AmafkMxX9gf_-j5w4XHXG8o
                  link: >-
                    https://uk.linkedin.com/in/benjamin-parr-940491?trk=org-employees
                  subtitle: Global CMO in Crypto.
                  title: Benjamin Parr
                - img: >-
                    https://media.licdn.com/dms/image/C4D03AQFdUs4Av5rygg/profile-displayphoto-shrink_100_100/0/1516264422356?e=2147483647&v=beta&t=UOtNggS62Q8IyXGN4PosDnhqOhQjJN8AHRBB78zLlXs
                  link: https://si.linkedin.com/in/dominikznidar?trk=org-employees
                  subtitle: Senior backend developer
                  title: Dominik Znidar
                - img: >-
                    https://media.licdn.com/dms/image/C4D03AQFFTmCpr_pIJQ/profile-displayphoto-shrink_100_100/0/1619005680916?e=2147483647&v=beta&t=Waxiqdk9WwM6YR2zD9c_k3KphlAocoylB8k2FU832pY
                  link: >-
                    https://lu.linkedin.com/in/stephen-bearpark-27aa5b?trk=org-employees
                  subtitle: Chief Financial Officer at Bitstamp
                  title: Stephen Bearpark
              employees_in_linkedin: 365
              followers: 30341
              formatted_locations:
                - Luxembourg, Luxembourg L-2520, LU
              founded: 2011
              funding:
                last_round_date: '2023-06-24T00:00:00.000Z'
                last_round_type: Corporate round
                rounds: 3
              get_directions_url:
                - directions_url: >-
                    https://www.bing.com/maps?where=Luxembourg+L-2520+Luxembourg+LU&trk=org-locations_url
              headquarters: Luxembourg, Luxembourg
              id: bitstamp
              image: >-
                https://media.licdn.com/dms/image/D4D3DAQFefkROuFwk5A/image-scale_191_1128/0/1697616530874/bitstamp_cover?e=2147483647&v=beta&t=R9eU5nQ8J-F3kbGES6-aVLhyLnQQ22lTFwhcNOd0fvg
              industries: Financial Services
              input:
                url: https://www.linkedin.com/company/2734818
              investors:
                - Ripple
              locations:
                - Luxembourg, Luxembourg L-2520, LU
              logo: >-
                https://media.licdn.com/dms/image/D4D0BAQF_ZNbRZzKn0Q/company-logo_200_200/0/1704443361832/bitstamp_logo?e=2147483647&v=beta&t=ON2r3XfdPTbdlCABksfDNCedtHSkO2z9ReQCEI3ihN0
              name: Bitstamp
              organization_type: Privately Held
              similar:
                - Links: https://www.linkedin.com/company/krakenfx?trk=similar-pages
                  subtitle: Financial Services
                  title: Kraken Digital Asset Exchange
                - Links: https://vg.linkedin.com/company/bitfinex?trk=similar-pages
                  subtitle: Financial Services
                  title: Bitfinex
                - Links: https://sc.linkedin.com/company/kucoin?trk=similar-pages
                  subtitle: Financial Services
                  title: KuCoin Exchange
                - Links: >-
                    https://www.linkedin.com/company/bybitexchange?trk=similar-pages
                  subtitle: Financial Services
                  title: Bybit
                - Links: >-
                    https://www.linkedin.com/company/geminitrust?trk=similar-pages
                  location: New York, NY
                  subtitle: Financial Services
                  title: Gemini
                - Links: https://www.linkedin.com/company/coinbase?trk=similar-pages
                  subtitle: Internet Publishing
                  title: Coinbase
                - Links: https://www.linkedin.com/company/binance?trk=similar-pages
                  subtitle: Software Development
                  title: Binance
                - Links: >-
                    https://www.linkedin.com/company/okxofficial?trk=similar-pages
                  subtitle: IT Services and IT Consulting
                  title: OKX
                - Links: https://ky.linkedin.com/company/gateio?trk=similar-pages
                  subtitle: Financial Services
                  title: Gate.io
                - Links: >-
                    https://sc.linkedin.com/company/htxglobalofficial?trk=similar-pages
                  subtitle: Financial Services
                  title: HTX
              slogan: World's longest-running crypto exchange
              specialties: null
              sphere: Financial Services
              stock_info: null
              type: Privately Held
              updates:
                - comments_count: 5
                  external_link: >-
                    https://www.linkedin.com/redir/redirect?url=https%3A%2F%2Fen%2Ethebigwhale%2Eio%2Farticle-en%2Fjean-baptiste-graftieaux-bitstamp-we-are-going-to-launch-a-fully-regulated-derivatives-offering&urlhash=0UL3&trk=organization_guest_main-feed-card_feed-article-content
                  images:
                    - >-
                      https://media.licdn.com/dms/image/sync/D4E27AQEZaBxV1lGFPQ/articleshare-shrink_800/0/1707981346426?e=2147483647&v=beta&t=Y3ZngwpKLa7Xoz6TzgVNzJZYmMk6Fdom59LHlvbZ3Ns
                  likes_count: 89
                  text: >-
                    In an exclusive interview with The Big Whale our CEO, JB
                    Graftieaux discusses our commitment to expanding services
                    for businesses announcing "We are going to launch a fully
                    regulated derivatives offering." JB Graftieaux highlights
                    Bitstamp's role in driving the evolution of payment
                    technology, particularly for businesses looking to embrace
                    cryptocurrencies. With a focus on expanding services for
                    both B2B and B2B2C clients, Bitstamp provides comprehensive
                    solutions to empower businesses with the tools and resources
                    they need to thrive in today's rapidly evolving financial
                    landscape. From partnering with market players like the
                    Stuttgart Stock Exchange and Revolut to offering white-label
                    solutions for banks, Bitstamp is at the forefront of
                    facilitating institutional adoption of cryptocurrencies.
                    With a commitment to regulatory compliance and a
                    customer-centric approach, we're dedicated to providing
                    trusted, secure, and innovative solutions that meet the
                    diverse needs of our clients. Read the full interview here:
                    https://lnkd.in/dgW8FPtN
                  time: 5d
                  title: Bitstamp
                - external_link: >-
                    https://www.linkedin.com/redir/redirect?url=https%3A%2F%2Fconsensus2024%2Ecoindesk%2Ecom%2Fcommunity-session-voting%2F&urlhash=BzoD&trk=organization_guest_main-feed-card_reshare_feed-article-content
                  images:
                    - >-
                      https://media.licdn.com/dms/image/sync/D5627AQE38PPAJZjCag/articleshare-shrink_800/0/1708030264958?e=2147483647&v=beta&t=pv8BCKVgL_XH4cEPcCCGrqax1jHeAGPQ1f16oSN24Bc
                  likes_count: 1
                  text: >-
                    🔔 Today is the last day to vote for our "DeFi for Capital
                    Markets" panel at CoinDesk Consensus 2024! If you haven't
                    had the chance to vote yet, we encourage you to cast your
                    vote now! Your vote can make the difference. 🗳️ #DeFi
                    #Consensus2024
                  time: 5d 3w
                  title: Bitstamp
                - likes_count: 22
                  text: >-
                    From emerging talents to industry leaders. We're committed
                    to empowering each individual's career development. Want to
                    hear from our team members? Check out the video. Want to
                    nurture your potential with us? Explore our current open
                    roles. 🔹 Crypto Team Lead (Slovenia & Croatia):
                    https://lnkd.in/dnMm3XWW 🔹 Senior Software Engineer -
                    Crypto (Slovenia & Croatia): https://lnkd.in/d38sC7Ui 🔹
                    Senior Technical Support Engineer (Slovenia & Croatia):
                    https://lnkd.in/dv3vmP3P 🔹 Cloud Operations Engineer -
                    Crypto (Slovenia & Croatia): https://lnkd.in/d7M7_f5h 🔹
                    Pricing, Liquidity and Markets Manager (Slovenia & UK):
                    https://lnkd.in/dNSB4Tjp 🔹 Business Operations and Strategy
                    Manager - Asset Listing (Slovenia & UK):
                    https://lnkd.in/g_7n_e3T Explore our career page:
                    https://lnkd.in/d6MTnSFi #WorkingAtBitstamp
                  time: 6d
                  title: Bitstamp
                  videos:
                    - null
                - comments_count: 1
                  likes_count: 31
                  text: >-
                    We're introducing our latest listing: LMWR, PEPE, BLUR, and
                    VEXT. LMWR empowers content creators, PEPE adds fun to
                    crypto, BLUR brings novelty to the NFTs and VEXT fuels
                    community decisions. Each carefully selected crypto assets
                    enriches our platform, showcasing our commitment to
                    providing a wide range of options. Learn more about the
                    assets and the listing schedule here:
                    https://lnkd.in/dykJtR4a
                  time: 1w
                  title: Bitstamp
                  videos:
                    - null
                - comments_count: 1
                  images:
                    - >-
                      https://media.licdn.com/dms/image/D4E22AQEKWK29cExlpw/feedshare-shrink_2048_1536/0/1707825435726?e=2147483647&v=beta&t=Iv0y53aveHyYisxmD0PdAiOKe5t15QSrgfR7n5GO2p4
                    - >-
                      https://media.licdn.com/dms/image/D4E22AQEVuGD2tPJufA/feedshare-shrink_800/0/1707825436409?e=2147483647&v=beta&t=jAc4jsRxdEUHfV4Z7jy7JwbaZBieFDRq63UBz9l9tkk
                    - >-
                      https://media.licdn.com/dms/image/D4E22AQE4-eD8H1CzDA/feedshare-shrink_800/0/1707825440601?e=2147483647&v=beta&t=RbJSdDRDxL4mT5-j1UdR4YWjplzdlDBlexmQZTfU8qk
                    - >-
                      https://media.licdn.com/dms/image/D4E22AQEX_VenEJ3dPQ/feedshare-shrink_800/0/1707825438877?e=2147483647&v=beta&t=0bHUwuFXFmgslpdrMxFbdjznxnWpNRPhfhleS_PP3nw
                    - >-
                      https://media.licdn.com/dms/image/D4E22AQEQyP-Yyo1CyQ/feedshare-shrink_800/0/1707825439584?e=2147483647&v=beta&t=EG4XLvIM2-Y7LMTmpoIgG5zerGEVrWkyDG6lUW9mPqo
                  likes_count: 59
                  text: >-
                    Last week marked an exciting chapter for Bitstamp as we
                    co-hosted a groundbreaking roundtable titled "The Evolution
                    of Payment Technology for a New Global and Digital Era" in
                    collaboration with Brunel University London , spearheaded by
                    Qi . During this dynamic event, we explored the future
                    landscape of payments, bridging the worlds of traditional
                    finance and crypto. A heartfelt thank you to our speakers
                    who ignited enlightening discussions: Mann Matharu and
                    Gurnam Selvarajah from Qi , Monomita Nandy from Brunel
                    University London , Nic Verdino from Cardstream , Nick
                    Philpott from Zodia Markets , Charles Kerrigan from CMS Law
                    Firm LLC , Kari Chaudhry from The Atlantic Society , and our
                    very own James Sullivan and Lenart Dolžan from Bitstamp .
                    Our mission? To pave the way for widespread adoption of
                    crypto payments in today's market. With the inaugural
                    roundtable of this series, we've set the stage for
                    transformative change. In partnership with Qi , we're
                    driving the evolution of payment technology, unlocking new
                    possibilities for businesses and consumers alike. With
                    insightful discussions and strategic collaborations, we're
                    shaping the future of finance together. Come join us!
                  time: 1w
                  title: Bitstamp
                - comments_count: 2
                  likes_count: 26
                  text: >-
                    Are you looking for a place where your work is challenging
                    and your time is respected? Where you're encouraged to excel
                    professionally without sacrificing your personal life?
                    That's what we aim for at Bitstamp. Watch the video to see
                    how balance is part of our everyday reality. If this sounds
                    like a perfect environment where you can thrive, check our
                    current open roles: ◼ Product Operations Manager (Slovenia):
                    https://lnkd.in/d2vQ9tPi ◼ Crypto Team Lead (Slovenia &
                    Croatia): https://lnkd.in/dnMm3XWW ◼ Software Engineer -
                    Crypto (Slovenia & Croatia): https://lnkd.in/dxqXTKpk ◼
                    Senior Software Engineer - Crypto (Slovenia & Croatia):
                    https://lnkd.in/d38sC7Ui ◼ Senior Technical Support Engineer
                    (Slovenia & Croatia): https://lnkd.in/dv3vmP3P ◼ QA Engineer
                    - Trading (Slovenia & Croatia): https://lnkd.in/dsQVU7ji ◼
                    Cloud Operations Engineer - Crypto (Slovenia & Croatia):
                    https://lnkd.in/d7M7_f5h ◼ Pricing, Liquidity and Markets
                    Manager (Slovenia & UK): https://lnkd.in/dNSB4Tjp ◼ Business
                    Operations and Strategy Manager - Asset Listing (Slovenia &
                    UK): https://lnkd.in/g_7n_e3T Explore our career page:
                    https://lnkd.in/d6MTnSFi #WorkingAtBitstamp
                  time: 1w
                  title: Bitstamp
                  videos:
                    - null
                - images:
                    - >-
                      https://media.licdn.com/dms/image/D5622AQGaDA-jWHS00w/feedshare-shrink_800/0/1707396968499?e=2147483647&v=beta&t=Edse9Bu4qZfP8yWlB6XM6xhLQYS0D1UUNlyusH-afiM
                  likes_count: 19
                  text: >-
                    We can't wait for tonight's event with Copper.co , where
                    we'll be hosting an exclusive panel and wine tasting
                    experience for our guests. Get ready to explore the latest
                    insights about how to navigate the crypto vineyard. Our Head
                    of Strategic Partnerships and Corp Dev, Eva Gartner , will
                    join our expert panelists in diving deep into key topics
                    such as security, risk mitigation, and liquidity in crypto
                    custody. Raise your glass to a sophisticated blend of
                    insights, as we pair the complexity of crypto custody with
                    the finesse of wine appreciation, creating a symphony of
                    success in the world of digital assets! Please note this
                    evening's event is currently at full capacity. If you are
                    interested in attending, please reach out to the team and
                    you'll be added to the waitlist.
                  time: 1w Edited
                  title: Bitstamp
                - external_link: >-
                    https://www.linkedin.com/redir/redirect?url=https%3A%2F%2Fblog%2Ebitstamp%2Enet%2Fpost%2Fbitstamp-monthly-briefing-january-2024%2F&urlhash=q2zL&trk=organization_guest_main-feed-card_feed-article-content
                  images:
                    - >-
                      https://media.licdn.com/dms/image/sync/D4D27AQHQLNtdTnqyXA/articleshare-shrink_800/0/1707322864200?e=2147483647&v=beta&t=ln_cWSvNOtrGWj2CqbsT2wwV5b-Mx0M44JlUOFmHE2s
                  likes_count: 19
                  text: >-
                    January's crypto insights from Bitstamp are here. ⬇ In this
                    month’s briefing, we delve into the market dynamics
                    reshaping the crypto world and take an in-depth look at the
                    nuances of crypto lending and borrowing. We aim to provide
                    valuable insights into these key areas, preparing our
                    readers for informed decision-making in 2024. Discover our
                    latest insights in the monthly briefing:
                    https://lnkd.in/dEuMg8Rz
                  time: 1w
                  title: Bitstamp
                - comments_count: 2
                  images:
                    - >-
                      https://media.licdn.com/dms/image/D4D22AQF-6xcJCu5tyQ/feedshare-shrink_800/0/1707307881815?e=2147483647&v=beta&t=SeY1P70tTqomRvQanx4bGWuoRQYvVaACw1VzmEwvMDs
                  likes_count: 29
                  text: >-
                    Reminder to Register for Our First LinkedIn Audio Event! 📢
                    🗓️ Coming Up: Thursday, February 8th at 3 PM GMT! Join us
                    as we dive into "Institutional Adoption of Crypto:
                    Regulations and Growth Opportunities in 2024" Featuring an
                    exceptional lineup of speakers: 🎙️ Simon Barnby , Chloé
                    Nightingale , Amor Sexton , Soledad Contreras , Kevin de
                    Patoul , Danny Bailey , Coby L. , Radoslav Poljasevic and
                    Olly Wilson 🤝 Sponsored by Blockchain.com 🔗 Be sure to
                    click "attend" in the event link below
                    https://lnkd.in/dYNDebUY
                  time: 2w
                  title: Zebu Live - London Web3 Conference
                - external_link: >-
                    https://www.linkedin.com/redir/redirect?url=https%3A%2F%2Fcryptonews%2Ecom%2Fexclusives%2Fbobby-zagotta-ceo-of-bitstamp-on-bitcoin-etf-the-halving-defi-for-capital-markets-and-2024-predictions-ep-304%2Ehtm&urlhash=72HL&trk=organization_guest_main-feed-card_feed-article-content
                  images:
                    - >-
                      https://media.licdn.com/dms/image/sync/D5627AQEzMtolOYZaJg/articleshare-shrink_800/0/1708013936402?e=2147483647&v=beta&t=crppgb7R5w6HQ0GUEpkXYLhFsVWBu-K1Y9ta7I7Idn4
                  likes_count: 38
                  text: >-
                    I recently sat down with Matt Zahab from Cryptonews to
                    discuss a range of topics, including the potential of
                    Bitcoin ETFs, the impact of the upcoming Halving, and how
                    DeFi is shaping the future of capital markets. I also shared
                    some thoughts on what 2024 might hold for the crypto space.
                    It was a thought-provoking conversation that I believe
                    offers valuable insights for anyone interested in the future
                    of finance. Dive into the full interview:
                    https://lnkd.in/gtyUtMGt #Podcast #Bitcoin Bitstamp
                  time: 2w
                  title: Bobby Zagotta
              url: https://www.linkedin.com/company/bitstamp
              website: https://www.bitstamp.net/
        examples:
          example:
            value:
              about: >-
                Bitstamp is the world’s longest-running cryptocurrency exchange,
                continuously supporting the Bitcoin economy since 2011. With a
                proven track record and mature approach to the industry,
                Bitstamp provides a secure and transparent venue to over four
                million customers and enables partners to access emerging crypto
                markets through time-proven infrastructure. NMLS ID: 1905429
                View more on the NMLS website here:
                https://www.nmlsconsumeraccess.org/EntityDetails.aspx/COMPANY/1905429
              affiliated: []
              company_id: '2734818'
              company_size: 501-1,000 employees
              country_code: LU
              crunchbase_url: >-
                https://www.crunchbase.com/organization/bitstamp?utm_source=linkedin&utm_medium=referral&utm_campaign=linkedin_companies&utm_content=profile_cta_anon&trk=funding_crunchbase
              description: "Bitstamp | 30,341 followers on LinkedIn. World&#39;s longest-running crypto exchange | Bitstamp is the world’s longest-running cryptocurrency exchange, continuously supporting the Bitcoin economy since 2011. With a proven track record and mature approach to the industry, Bitstamp provides a secure and transparent venue to over four million customers and enables partners to access emerging crypto markets through time-proven infrastructure.\n\n\n\n\nNMLS ID:\t1905429\nView more on the NMLS website here: https://www.nmlsconsumeraccess.org/EntityDetails.aspx/COMPANY/1905429"
              employees:
                - img: >-
                    https://media.licdn.com/dms/image/D4E03AQGixwSI9R6RuQ/profile-displayphoto-shrink_100_100/0/1701888289576?e=2147483647&v=beta&t=JCC9EZgKl5VWFcV_qdHIlvE7ZScFDTQeMOcrMrmU5TA
                  link: https://ae.linkedin.com/in/jsgreenwood?trk=org-employees
                  subtitle: Executive leadership & digital transformation
                  title: James Greenwood
                - img: >-
                    https://media.licdn.com/dms/image/C4E03AQGD22qBJsQ-qw/profile-displayphoto-shrink_100_100/0/1524161393516?e=2147483647&v=beta&t=OSS74hoSvrpwsPjEuuF0AmafkMxX9gf_-j5w4XHXG8o
                  link: >-
                    https://uk.linkedin.com/in/benjamin-parr-940491?trk=org-employees
                  subtitle: Global CMO in Crypto.
                  title: Benjamin Parr
                - img: >-
                    https://media.licdn.com/dms/image/C4D03AQFdUs4Av5rygg/profile-displayphoto-shrink_100_100/0/1516264422356?e=2147483647&v=beta&t=UOtNggS62Q8IyXGN4PosDnhqOhQjJN8AHRBB78zLlXs
                  link: https://si.linkedin.com/in/dominikznidar?trk=org-employees
                  subtitle: Senior backend developer
                  title: Dominik Znidar
                - img: >-
                    https://media.licdn.com/dms/image/C4D03AQFFTmCpr_pIJQ/profile-displayphoto-shrink_100_100/0/1619005680916?e=2147483647&v=beta&t=Waxiqdk9WwM6YR2zD9c_k3KphlAocoylB8k2FU832pY
                  link: >-
                    https://lu.linkedin.com/in/stephen-bearpark-27aa5b?trk=org-employees
                  subtitle: Chief Financial Officer at Bitstamp
                  title: Stephen Bearpark
              employees_in_linkedin: 365
              followers: 30341
              formatted_locations:
                - Luxembourg, Luxembourg L-2520, LU
              founded: 2011
              funding:
                last_round_date: '2023-06-24T00:00:00.000Z'
                last_round_type: Corporate round
                rounds: 3
              get_directions_url:
                - directions_url: >-
                    https://www.bing.com/maps?where=Luxembourg+L-2520+Luxembourg+LU&trk=org-locations_url
              headquarters: Luxembourg, Luxembourg
              id: bitstamp
              image: >-
                https://media.licdn.com/dms/image/D4D3DAQFefkROuFwk5A/image-scale_191_1128/0/1697616530874/bitstamp_cover?e=2147483647&v=beta&t=R9eU5nQ8J-F3kbGES6-aVLhyLnQQ22lTFwhcNOd0fvg
              industries: Financial Services
              input:
                url: https://www.linkedin.com/company/2734818
              investors:
                - Ripple
              locations:
                - Luxembourg, Luxembourg L-2520, LU
              logo: >-
                https://media.licdn.com/dms/image/D4D0BAQF_ZNbRZzKn0Q/company-logo_200_200/0/1704443361832/bitstamp_logo?e=2147483647&v=beta&t=ON2r3XfdPTbdlCABksfDNCedtHSkO2z9ReQCEI3ihN0
              name: Bitstamp
              organization_type: Privately Held
              similar:
                - Links: https://www.linkedin.com/company/krakenfx?trk=similar-pages
                  subtitle: Financial Services
                  title: Kraken Digital Asset Exchange
                - Links: https://vg.linkedin.com/company/bitfinex?trk=similar-pages
                  subtitle: Financial Services
                  title: Bitfinex
                - Links: https://sc.linkedin.com/company/kucoin?trk=similar-pages
                  subtitle: Financial Services
                  title: KuCoin Exchange
                - Links: >-
                    https://www.linkedin.com/company/bybitexchange?trk=similar-pages
                  subtitle: Financial Services
                  title: Bybit
                - Links: >-
                    https://www.linkedin.com/company/geminitrust?trk=similar-pages
                  location: New York, NY
                  subtitle: Financial Services
                  title: Gemini
                - Links: https://www.linkedin.com/company/coinbase?trk=similar-pages
                  subtitle: Internet Publishing
                  title: Coinbase
                - Links: https://www.linkedin.com/company/binance?trk=similar-pages
                  subtitle: Software Development
                  title: Binance
                - Links: >-
                    https://www.linkedin.com/company/okxofficial?trk=similar-pages
                  subtitle: IT Services and IT Consulting
                  title: OKX
                - Links: https://ky.linkedin.com/company/gateio?trk=similar-pages
                  subtitle: Financial Services
                  title: Gate.io
                - Links: >-
                    https://sc.linkedin.com/company/htxglobalofficial?trk=similar-pages
                  subtitle: Financial Services
                  title: HTX
              slogan: World's longest-running crypto exchange
              specialties: null
              sphere: Financial Services
              stock_info: null
              type: Privately Held
              updates:
                - comments_count: 5
                  external_link: >-
                    https://www.linkedin.com/redir/redirect?url=https%3A%2F%2Fen%2Ethebigwhale%2Eio%2Farticle-en%2Fjean-baptiste-graftieaux-bitstamp-we-are-going-to-launch-a-fully-regulated-derivatives-offering&urlhash=0UL3&trk=organization_guest_main-feed-card_feed-article-content
                  images:
                    - >-
                      https://media.licdn.com/dms/image/sync/D4E27AQEZaBxV1lGFPQ/articleshare-shrink_800/0/1707981346426?e=2147483647&v=beta&t=Y3ZngwpKLa7Xoz6TzgVNzJZYmMk6Fdom59LHlvbZ3Ns
                  likes_count: 89
                  text: >-
                    In an exclusive interview with The Big Whale our CEO, JB
                    Graftieaux discusses our commitment to expanding services
                    for businesses announcing "We are going to launch a fully
                    regulated derivatives offering." JB Graftieaux highlights
                    Bitstamp's role in driving the evolution of payment
                    technology, particularly for businesses looking to embrace
                    cryptocurrencies. With a focus on expanding services for
                    both B2B and B2B2C clients, Bitstamp provides comprehensive
                    solutions to empower businesses with the tools and resources
                    they need to thrive in today's rapidly evolving financial
                    landscape. From partnering with market players like the
                    Stuttgart Stock Exchange and Revolut to offering white-label
                    solutions for banks, Bitstamp is at the forefront of
                    facilitating institutional adoption of cryptocurrencies.
                    With a commitment to regulatory compliance and a
                    customer-centric approach, we're dedicated to providing
                    trusted, secure, and innovative solutions that meet the
                    diverse needs of our clients. Read the full interview here:
                    https://lnkd.in/dgW8FPtN
                  time: 5d
                  title: Bitstamp
                - external_link: >-
                    https://www.linkedin.com/redir/redirect?url=https%3A%2F%2Fconsensus2024%2Ecoindesk%2Ecom%2Fcommunity-session-voting%2F&urlhash=BzoD&trk=organization_guest_main-feed-card_reshare_feed-article-content
                  images:
                    - >-
                      https://media.licdn.com/dms/image/sync/D5627AQE38PPAJZjCag/articleshare-shrink_800/0/1708030264958?e=2147483647&v=beta&t=pv8BCKVgL_XH4cEPcCCGrqax1jHeAGPQ1f16oSN24Bc
                  likes_count: 1
                  text: >-
                    🔔 Today is the last day to vote for our "DeFi for Capital
                    Markets" panel at CoinDesk Consensus 2024! If you haven't
                    had the chance to vote yet, we encourage you to cast your
                    vote now! Your vote can make the difference. 🗳️ #DeFi
                    #Consensus2024
                  time: 5d 3w
                  title: Bitstamp
                - likes_count: 22
                  text: >-
                    From emerging talents to industry leaders. We're committed
                    to empowering each individual's career development. Want to
                    hear from our team members? Check out the video. Want to
                    nurture your potential with us? Explore our current open
                    roles. 🔹 Crypto Team Lead (Slovenia & Croatia):
                    https://lnkd.in/dnMm3XWW 🔹 Senior Software Engineer -
                    Crypto (Slovenia & Croatia): https://lnkd.in/d38sC7Ui 🔹
                    Senior Technical Support Engineer (Slovenia & Croatia):
                    https://lnkd.in/dv3vmP3P 🔹 Cloud Operations Engineer -
                    Crypto (Slovenia & Croatia): https://lnkd.in/d7M7_f5h 🔹
                    Pricing, Liquidity and Markets Manager (Slovenia & UK):
                    https://lnkd.in/dNSB4Tjp 🔹 Business Operations and Strategy
                    Manager - Asset Listing (Slovenia & UK):
                    https://lnkd.in/g_7n_e3T Explore our career page:
                    https://lnkd.in/d6MTnSFi #WorkingAtBitstamp
                  time: 6d
                  title: Bitstamp
                  videos:
                    - null
                - comments_count: 1
                  likes_count: 31
                  text: >-
                    We're introducing our latest listing: LMWR, PEPE, BLUR, and
                    VEXT. LMWR empowers content creators, PEPE adds fun to
                    crypto, BLUR brings novelty to the NFTs and VEXT fuels
                    community decisions. Each carefully selected crypto assets
                    enriches our platform, showcasing our commitment to
                    providing a wide range of options. Learn more about the
                    assets and the listing schedule here:
                    https://lnkd.in/dykJtR4a
                  time: 1w
                  title: Bitstamp
                  videos:
                    - null
                - comments_count: 1
                  images:
                    - >-
                      https://media.licdn.com/dms/image/D4E22AQEKWK29cExlpw/feedshare-shrink_2048_1536/0/1707825435726?e=2147483647&v=beta&t=Iv0y53aveHyYisxmD0PdAiOKe5t15QSrgfR7n5GO2p4
                    - >-
                      https://media.licdn.com/dms/image/D4E22AQEVuGD2tPJufA/feedshare-shrink_800/0/1707825436409?e=2147483647&v=beta&t=jAc4jsRxdEUHfV4Z7jy7JwbaZBieFDRq63UBz9l9tkk
                    - >-
                      https://media.licdn.com/dms/image/D4E22AQE4-eD8H1CzDA/feedshare-shrink_800/0/1707825440601?e=2147483647&v=beta&t=RbJSdDRDxL4mT5-j1UdR4YWjplzdlDBlexmQZTfU8qk
                    - >-
                      https://media.licdn.com/dms/image/D4E22AQEX_VenEJ3dPQ/feedshare-shrink_800/0/1707825438877?e=2147483647&v=beta&t=0bHUwuFXFmgslpdrMxFbdjznxnWpNRPhfhleS_PP3nw
                    - >-
                      https://media.licdn.com/dms/image/D4E22AQEQyP-Yyo1CyQ/feedshare-shrink_800/0/1707825439584?e=2147483647&v=beta&t=EG4XLvIM2-Y7LMTmpoIgG5zerGEVrWkyDG6lUW9mPqo
                  likes_count: 59
                  text: >-
                    Last week marked an exciting chapter for Bitstamp as we
                    co-hosted a groundbreaking roundtable titled "The Evolution
                    of Payment Technology for a New Global and Digital Era" in
                    collaboration with Brunel University London , spearheaded by
                    Qi . During this dynamic event, we explored the future
                    landscape of payments, bridging the worlds of traditional
                    finance and crypto. A heartfelt thank you to our speakers
                    who ignited enlightening discussions: Mann Matharu and
                    Gurnam Selvarajah from Qi , Monomita Nandy from Brunel
                    University London , Nic Verdino from Cardstream , Nick
                    Philpott from Zodia Markets , Charles Kerrigan from CMS Law
                    Firm LLC , Kari Chaudhry from The Atlantic Society , and our
                    very own James Sullivan and Lenart Dolžan from Bitstamp .
                    Our mission? To pave the way for widespread adoption of
                    crypto payments in today's market. With the inaugural
                    roundtable of this series, we've set the stage for
                    transformative change. In partnership with Qi , we're
                    driving the evolution of payment technology, unlocking new
                    possibilities for businesses and consumers alike. With
                    insightful discussions and strategic collaborations, we're
                    shaping the future of finance together. Come join us!
                  time: 1w
                  title: Bitstamp
                - comments_count: 2
                  likes_count: 26
                  text: >-
                    Are you looking for a place where your work is challenging
                    and your time is respected? Where you're encouraged to excel
                    professionally without sacrificing your personal life?
                    That's what we aim for at Bitstamp. Watch the video to see
                    how balance is part of our everyday reality. If this sounds
                    like a perfect environment where you can thrive, check our
                    current open roles: ◼ Product Operations Manager (Slovenia):
                    https://lnkd.in/d2vQ9tPi ◼ Crypto Team Lead (Slovenia &
                    Croatia): https://lnkd.in/dnMm3XWW ◼ Software Engineer -
                    Crypto (Slovenia & Croatia): https://lnkd.in/dxqXTKpk ◼
                    Senior Software Engineer - Crypto (Slovenia & Croatia):
                    https://lnkd.in/d38sC7Ui ◼ Senior Technical Support Engineer
                    (Slovenia & Croatia): https://lnkd.in/dv3vmP3P ◼ QA Engineer
                    - Trading (Slovenia & Croatia): https://lnkd.in/dsQVU7ji ◼
                    Cloud Operations Engineer - Crypto (Slovenia & Croatia):
                    https://lnkd.in/d7M7_f5h ◼ Pricing, Liquidity and Markets
                    Manager (Slovenia & UK): https://lnkd.in/dNSB4Tjp ◼ Business
                    Operations and Strategy Manager - Asset Listing (Slovenia &
                    UK): https://lnkd.in/g_7n_e3T Explore our career page:
                    https://lnkd.in/d6MTnSFi #WorkingAtBitstamp
                  time: 1w
                  title: Bitstamp
                  videos:
                    - null
                - images:
                    - >-
                      https://media.licdn.com/dms/image/D5622AQGaDA-jWHS00w/feedshare-shrink_800/0/1707396968499?e=2147483647&v=beta&t=Edse9Bu4qZfP8yWlB6XM6xhLQYS0D1UUNlyusH-afiM
                  likes_count: 19
                  text: >-
                    We can't wait for tonight's event with Copper.co , where
                    we'll be hosting an exclusive panel and wine tasting
                    experience for our guests. Get ready to explore the latest
                    insights about how to navigate the crypto vineyard. Our Head
                    of Strategic Partnerships and Corp Dev, Eva Gartner , will
                    join our expert panelists in diving deep into key topics
                    such as security, risk mitigation, and liquidity in crypto
                    custody. Raise your glass to a sophisticated blend of
                    insights, as we pair the complexity of crypto custody with
                    the finesse of wine appreciation, creating a symphony of
                    success in the world of digital assets! Please note this
                    evening's event is currently at full capacity. If you are
                    interested in attending, please reach out to the team and
                    you'll be added to the waitlist.
                  time: 1w Edited
                  title: Bitstamp
                - external_link: >-
                    https://www.linkedin.com/redir/redirect?url=https%3A%2F%2Fblog%2Ebitstamp%2Enet%2Fpost%2Fbitstamp-monthly-briefing-january-2024%2F&urlhash=q2zL&trk=organization_guest_main-feed-card_feed-article-content
                  images:
                    - >-
                      https://media.licdn.com/dms/image/sync/D4D27AQHQLNtdTnqyXA/articleshare-shrink_800/0/1707322864200?e=2147483647&v=beta&t=ln_cWSvNOtrGWj2CqbsT2wwV5b-Mx0M44JlUOFmHE2s
                  likes_count: 19
                  text: >-
                    January's crypto insights from Bitstamp are here. ⬇ In this
                    month’s briefing, we delve into the market dynamics
                    reshaping the crypto world and take an in-depth look at the
                    nuances of crypto lending and borrowing. We aim to provide
                    valuable insights into these key areas, preparing our
                    readers for informed decision-making in 2024. Discover our
                    latest insights in the monthly briefing:
                    https://lnkd.in/dEuMg8Rz
                  time: 1w
                  title: Bitstamp
                - comments_count: 2
                  images:
                    - >-
                      https://media.licdn.com/dms/image/D4D22AQF-6xcJCu5tyQ/feedshare-shrink_800/0/1707307881815?e=2147483647&v=beta&t=SeY1P70tTqomRvQanx4bGWuoRQYvVaACw1VzmEwvMDs
                  likes_count: 29
                  text: >-
                    Reminder to Register for Our First LinkedIn Audio Event! 📢
                    🗓️ Coming Up: Thursday, February 8th at 3 PM GMT! Join us
                    as we dive into "Institutional Adoption of Crypto:
                    Regulations and Growth Opportunities in 2024" Featuring an
                    exceptional lineup of speakers: 🎙️ Simon Barnby , Chloé
                    Nightingale , Amor Sexton , Soledad Contreras , Kevin de
                    Patoul , Danny Bailey , Coby L. , Radoslav Poljasevic and
                    Olly Wilson 🤝 Sponsored by Blockchain.com 🔗 Be sure to
                    click "attend" in the event link below
                    https://lnkd.in/dYNDebUY
                  time: 2w
                  title: Zebu Live - London Web3 Conference
                - external_link: >-
                    https://www.linkedin.com/redir/redirect?url=https%3A%2F%2Fcryptonews%2Ecom%2Fexclusives%2Fbobby-zagotta-ceo-of-bitstamp-on-bitcoin-etf-the-halving-defi-for-capital-markets-and-2024-predictions-ep-304%2Ehtm&urlhash=72HL&trk=organization_guest_main-feed-card_feed-article-content
                  images:
                    - >-
                      https://media.licdn.com/dms/image/sync/D5627AQEzMtolOYZaJg/articleshare-shrink_800/0/1708013936402?e=2147483647&v=beta&t=crppgb7R5w6HQ0GUEpkXYLhFsVWBu-K1Y9ta7I7Idn4
                  likes_count: 38
                  text: >-
                    I recently sat down with Matt Zahab from Cryptonews to
                    discuss a range of topics, including the potential of
                    Bitcoin ETFs, the impact of the upcoming Halving, and how
                    DeFi is shaping the future of capital markets. I also shared
                    some thoughts on what 2024 might hold for the crypto space.
                    It was a thought-provoking conversation that I believe
                    offers valuable insights for anyone interested in the future
                    of finance. Dive into the full interview:
                    https://lnkd.in/gtyUtMGt #Podcast #Bitcoin Bitstamp
                  time: 2w
                  title: Bobby Zagotta
              url: https://www.linkedin.com/company/bitstamp
              website: https://www.bitstamp.net/
        description: OK
    '202':
      text/html:
        schemaArray:
          - type: string
            example: Snapshot is building. Try again in a few minutes
        examples:
          example:
            value: Snapshot is building. Try again in a few minutes
        description: Snapshot not ready
    '400':
      application/json:
        schemaArray:
          - type: object
            properties:
              error:
                allOf:
                  - type: string
            refIdentifier: '#/components/schemas/ErrorBody'
          - type: object
            properties:
              validation_errors:
                allOf:
                  - type: array
                    items:
                      type: string
            refIdentifier: '#/components/schemas/ValidationErrorBody'
        examples:
          example:
            value:
              error: Snapshot not ready
        description: Bad request
    '404':
      application/json:
        schemaArray:
          - type: object
            properties:
              error:
                allOf:
                  - type: string
                    example: Snapshot not found
        examples:
          example:
            value:
              error: Snapshot not found
        description: Snapshot not found
  deprecated: false
  type: path
components:
  schemas: {}

````

# Deliver Snapshot

> Deliver the dataset snapshot

## OpenAPI

````yaml dca-api POST /datasets/snapshots/{id}/deliver
paths:
  path: /datasets/snapshots/{id}/deliver
  method: post
  servers:
    - url: https://api.brightdata.com
  request:
    security:
      - title: bearerAuth
        parameters:
          query: {}
          header:
            Authorization:
              type: http
              scheme: bearer
              description: >-
                Use your Bright Data API Key as a Bearer token in the
                Authorization header. 

                 Get API Key from: https://brightdata.com/cp/setting/users. 

                 **Example**:
                ```Authorization: Bearer
                b5648e1096c6442f60a6c4bbbe73f8d2234d3d8324554bd6a7ec8f3f251f07df```
          cookie: {}
    parameters:
      path:
        id:
          schema:
            - type: string
              required: true
              description: >-
                A Snapshot ID is a unique identifier for a specific data
                snapshot, used to retrieve results from a data collection job
                triggered via the API. Read more about [Snapshot
                ID](/api-reference/terminology#snapshot-id).
              example: snap_m2bxug4e2o352v1jv1
      query: {}
      header: {}
      cookie: {}
    body:
      application/json:
        schemaArray:
          - type: object
            properties:
              deliver:
                allOf:
                  - $ref: '#/components/schemas/DeliverConfig'
              compress:
                allOf:
                  - type: boolean
                    description: Deliver file compressed in gzip format
                    default: false
            required: true
            refIdentifier: '#/components/schemas/DeliverSnapshotBody'
        examples:
          example:
            value:
              deliver:
                type: webhook
                filename:
                  template: <string>
                  extension: json
                endpoint: <string>
              compress: false
  response:
    '200':
      application/json:
        schemaArray:
          - type: object
            properties:
              id:
                allOf:
                  - type: string
                    description: ID of the delivery job
        examples:
          example:
            value:
              id: <string>
        description: OK
    '404':
      application/json:
        schemaArray:
          - type: object
            properties:
              error:
                allOf:
                  - type: string
                    example: Snapshot not found
        examples:
          example:
            value:
              error: Snapshot not found
        description: Snapshot not found
  deprecated: false
  type: path
components:
  schemas:
    DatasetDeliveryType:
      type: string
      description: Type of the delivery target
      enum:
        - azure
        - build
        - email
        - gcs
        - gcs_pubsub
        - s3
        - sftp
        - snowflake
        - webhook
        - ali_oss
    DeliveredFileExt:
      type: string
      enum:
        - json
        - jsonl
        - csv
    DeliverConfigBase:
      type: object
      additionalProperties: false
      properties:
        type:
          $ref: '#/components/schemas/DatasetDeliveryType'
        filename:
          type: object
          additionalProperties: false
          properties:
            template:
              type: string
              description: Template for the filename, including placeholders.
            extension:
              $ref: '#/components/schemas/DeliveredFileExt'
          required:
            - template
            - extension
      required:
        - type
        - filename
    DeliverConfigWebhook:
      allOf:
        - $ref: '#/components/schemas/DeliverConfigBase'
        - type: object
          properties:
            type:
              enum:
                - webhook
            endpoint:
              type: string
              format: uri
              description: The endpoint URL for the webhook.
    DeliverConfigGCS:
      allOf:
        - $ref: '#/components/schemas/DeliverConfigBase'
        - type: object
          properties:
            type:
              enum:
                - gcs
            bucket:
              type: string
              description: Name of the bucket.
            credentials:
              type: object
              additionalProperties: false
              description: Credentials for authentication
              properties:
                client_email:
                  type: string
                private_key:
                  type: string
              required:
                - client_email
                - private_key
            directory:
              type: string
              description: Target path
          required:
            - bucket
            - credentials
    DeliverConfigGCSPubSub:
      allOf:
        - $ref: '#/components/schemas/DeliverConfigBase'
        - type: object
          properties:
            type:
              enum:
                - gcs_pubsub
            topic_id:
              type: string
            attributes:
              type: array
              items:
                type: object
            credentials:
              type: object
              additionalProperties: false
              properties:
                client_email:
                  type: string
                private_key:
                  type: string
              required:
                - client_email
                - private_key
          required:
            - topic_id
            - credentials
    DeliverConfigS3:
      allOf:
        - $ref: '#/components/schemas/DeliverConfigBase'
        - type: object
          properties:
            type:
              enum:
                - s3
            bucket:
              type: string
            endpoint_url:
              type: string
              description: S3 like host url, available only with Access Key auth
            credentials:
              type: object
              additionalProperties: false
              minProperties: 2
              properties:
                aws-access-key:
                  type: string
                aws-secret-key:
                  type: string
                role_arn:
                  type: string
                external_id:
                  type: string
              oneOf:
                - title: Role ARN
                  required:
                    - role_arn
                    - external_id
                - title: Access Key
                  required:
                    - aws-access-key
                    - aws-secret-key
            region:
              type: string
            directory:
              type: string
          required:
            - bucket
            - credentials
    DeliverConfigSnowflake:
      allOf:
        - $ref: '#/components/schemas/DeliverConfigBase'
        - type: object
          properties:
            type:
              enum:
                - snowflake
            database:
              type: string
            schema:
              type: string
            stage:
              type: string
            role:
              type: string
            warehouse:
              type: string
            credentials:
              type: object
              additionalProperties: false
              properties:
                account:
                  type: string
                user:
                  type: string
                password:
                  type: string
              required:
                - account
                - user
                - password
          required:
            - database
            - schema
            - stage
            - role
            - warehouse
            - credentials
    DeliverConfigAliOSS:
      allOf:
        - $ref: '#/components/schemas/DeliverConfigBase'
        - type: object
          properties:
            type:
              enum:
                - ali_oss
            bucket:
              type: string
            credentials:
              type: object
              additionalProperties: false
              properties:
                access-key:
                  type: string
                secret-key:
                  type: string
              required:
                - access-key
                - secret-key
            region:
              type: string
            directory:
              type: string
          required:
            - bucket
            - credentials
            - region
    DeliverConfigSFTP:
      allOf:
        - $ref: '#/components/schemas/DeliverConfigBase'
        - type: object
          properties:
            type:
              enum:
                - sftp
            path:
              type: string
              format: hostname
            port:
              type: integer
              minimum: 0
              maximum: 65535
            credentials:
              type: object
              additionalProperties: false
              properties:
                username:
                  type: string
                password:
                  type: string
                ssh_key:
                  type: string
                passphrase:
                  type: string
              required:
                - username
            directory:
              type: string
          required:
            - path
            - credentials
    DeliverConfigAzure:
      allOf:
        - $ref: '#/components/schemas/DeliverConfigBase'
        - type: object
          properties:
            type:
              enum:
                - azure
            container:
              type: string
              minLength: 3
              pattern: ^[a-z0-9](-?[a-z0-9])*$
            credentials:
              type: object
              additionalProperties: false
              properties:
                account:
                  type: string
                  pattern: ^[a-zA-Z0-9]+$
                key:
                  type: string
                  format: byte
                sas_token:
                  type: string
              required:
                - account
              oneOf:
                - required:
                    - key
                  title: Acess key
                - required:
                    - sas_token
                  title: Shared access token
            directory:
              type: string
          required:
            - container
            - credentials
    DeliverConfig:
      description: Deliver configuration
      oneOf:
        - $ref: '#/components/schemas/DeliverConfigWebhook'
          title: Webhook
        - $ref: '#/components/schemas/DeliverConfigGCS'
          title: Google Cloud
        - $ref: '#/components/schemas/DeliverConfigGCSPubSub'
          title: Google Cloud PubSub
        - $ref: '#/components/schemas/DeliverConfigS3'
          title: Amazon S3
        - $ref: '#/components/schemas/DeliverConfigSnowflake'
          title: Snowflake
        - $ref: '#/components/schemas/DeliverConfigAliOSS'
          title: Aliyun Object Storage Service
        - $ref: '#/components/schemas/DeliverConfigSFTP'
          title: SFTP
        - $ref: '#/components/schemas/DeliverConfigAzure'
          title: Microsoft Azure

````



## Overview

[The LinkedIn API](https://brightdata.com/products/web-scraper/linkedin) Suite offers multiple types of APIs, each designed for specific data collection needs from LinkedIn. Below is an overview of how these APIs connect and interact, based on the available features:

<CardGroup cols="1">
  <Card title="Profiles API" icon="user" href="/api-reference/web-scraper-api/social-media-apis/linkedin#profiles-api">
    The [LinkedIn Profiles API](https://brightdata.com/products/web-scraper/linkedin/profiles) allows users to collect profile details based on a single input: profile URL.

    <br />

    *   **Discovery functionality**:

    *   Discover LinkedIn profiles by names

    <br />

    *   **Interesting Columns**:

    *   `name`, `country_code`, `current_company`, `about`.
  </Card>

  <Card title="Posts API" icon="images" href="/api-reference/web-scraper-api/social-media-apis/linkedin#posts-api">
    The [LinkedIn Posts API](https://brightdata.com/products/web-scraper/linkedin/post) allows users to collect multiple posts based on a single input URL.

    <br />

    *   **Discovery functionality**:

      *   - Direct URL of the LinkedIn profile

      *   - Direct URL user’s articles

      *   - Direct URL of the company

    <br />

    *   **Interesting Columns**:

    *   `url`, `title`, `hashtags`, `num_likes`.
  </Card>

  <Card title="Job Listings Information API" icon="briefcase" href="/api-reference/web-scraper-api/social-media-apis/linkedin#job-listings-information-api">
    The [LinkedIn Jobs API](https://brightdata.com/products/web-scraper/linkedin/jobs) allows users to collect job details based on a single input URL.

    <br />

    *   **Discovery functionality**:

      *   - Direct URL of the search

      *   - Discover by keywords

    <br />

    *   **Interesting Columns**:

    *   `job_title`, `company_name`, `job_location`, `job_seniority_level`.
  </Card>

  <Card title="Companies Information API" icon="building" href="/api-reference/web-scraper-api/social-media-apis/linkedin#companies-information-api">
    The [LinkedIn Companies API](https://brightdata.com/products/web-scraper/linkedin/company) allows users to collect company information by using its URL.

    <br />

    *   **Discovery functionality**: N/A

    <br />

    *   **Interesting Columns**:

    *   `name`, `country_code`, `followers`, `employees_in_linkedin`.
  </Card>
</CardGroup>

The suite of APIs is designed to offer flexibility for targeted data collection, where users can input specific URLs to gather detailed post, profile, job, and company data, either in bulk or with precise filtering options.

## Profiles API

### Collect by URL

This API allows users to collect detailed information about a LinkedIn profile by providing the profile URL.

**Input Parameters**:

<ParamField path="URL" type="string" required="true">
  The LinkedIn profile URL.
</ParamField>

**Output Structure**:\
Includes comprehensive data points:

* **Profile Details**:
  `linkedin_id`, `name`, `country_code`, `city`, `position`, `current_company`, `current_company_name`, `current_company_company_id`, `about`, and more.

  > For all data points, [click here](https://brightdata.com/cp/data_api/gd_l1viktl72bvl7bjuj0?tab=overview).

* **Professional Information**:
  `experience`, `education`, `educations_details`, `certifications`, `languages`, `recommendations_count`, `recommendations`, `volunteer_experience`, `courses`, `publications`, `patents`, `projects`, `organizations`, and `honors_and_awards`.

* **Social Activity**:
  `posts`, `activity`, `followers`, `connections`, `people_also_viewed`.

* **Media and Identification**:
  `avatar`, `banner_image`, `url`, `input_url`, `linkedin_num_id`, `id`, `timestamp`.

This API provides a rich set of data points for analyzing LinkedIn profiles, including professional experience, education, recommendations, and social activity, as well as media and unique identification details.

### Discover by Name

This API allows users to discover LinkedIn profiles based on a given first and last name.

**Input Parameters**:

<ParamField path="first_name" type="string" required="true">
  The first name of the individual.
</ParamField>

<ParamField path="last_name" type="string" required="true">
  The last name of the individual.
</ParamField>

**Output Structure**:\
Includes comprehensive data points:

* **Profile Details**:
  `linkedin_id`, `name`, `country_code`, `city`, `position`, `current_company`, `current_company_name`, `current_company_company_id`, `about`, and more.

  > For all data points, [click here](https://brightdata.com/cp/data_api/gd_l1viktl72bvl7bjuj0/name?tab=overview).

* **Professional Information**:
  `experience`, `education`, `educations_details`, `certifications`, `languages`, `recommendations_count`, `recommendations`, `volunteer_experience`, `courses`, `publications`, `patents`, `projects`, `organizations`, and `honors_and_awards`.

* **Social Activity**:
  `posts`, `activity`, `followers`, `connections`, `people_also_viewed`.

* **Media and Identification**:
  `avatar`, `banner_image`, `url`, `input_url`, `linkedin_num_id`, `id`, `timestamp`.

This API provides an efficient way to retrieve LinkedIn profile details based on a person's name, delivering rich professional and social insights along with associated media assets.

## Posts API

### Collect by URL

This API enables users to collect detailed data from Instagram posts by providing a post URL.

**Input Parameters**:

<ParamField path="URL" type="string" required="true">
  The LinkedIn post URL.
</ParamField>

**Output Structure**:\
Includes comprehensive data points:

* **Post Details**:
  `id`, `title`, `headline`, `post_text`, `post_text_html`, `date_posted`, `hashtags`, `embedded_links`, `images`, `videos`, `post_type`, `account_type`, and more.

  > For all data points, [click here](https://brightdata.com/cp/data_api/gd_lyy3tktm25m4avu764?tab=overview).

* **Engagement Metrics**:
  `num_likes`, `num_comments`, `top_visible_comments`.

* **User Details**:
  `user_id`, `use_url`, `user_followers`, `user_posts`, `user_articles`.

* **Related Content**:
  `more_articles_by_user`, `more_relevant_posts`.

This API provides detailed information about a LinkedIn post, including text, media attachments, engagement metrics, and additional user-related and related content for comprehensive post analysis.

### Discover by URL

This API allows users to discover articles authored by a LinkedIn user by providing their profile URL and optionally limiting the number of results.

**Input Parameters**:

<ParamField path="URL" type="string" required="true">
  The LinkedIn profile URL.
</ParamField>

<ParamField path="limit" type="number">
  The maximum number of articles to retrieve. If omitted, all available articles will be collected.
</ParamField>

**Output Structure**:\
Includes comprehensive data points:

* **Article Details**:
  `id`, `title`, `headline`, `post_text`, `post_text_html`, `date_posted`, `hashtags`, `embedded_links`, `images`, `videos`, `post_type`, `account_type`, and more.

  > For all data points, [click here](https://brightdata.com/cp/data_api/gd_lyy3tktm25m4avu764/url?tab=overview).

* **Engagement Metrics**:
  `num_likes`, `num_comments`, `top_visible_comments`.

* **User Details**:
  `user_id`, `use_url`, `user_followers`, `user_posts`, `user_articles`.

* **Related Content**:
  `more_articles_by_user`, `more_relevant_posts`.

This API delivers detailed information about articles written by a LinkedIn user, including text, media, and engagement insights, along with associated user and related content data for enhanced analysis.

### Discover by Profile URL

This API allows users to discover LinkedIn posts from a profile by providing the profile URL and applying optional date filters.

**Input Parameters**:

<ParamField path="URL" type="string" required="true">
  The LinkedIn profile URL.
</ParamField>

<ParamField path="start_date" type="date">
  Start date for filtering posts by their publish date (YYYY-MM-DD format). Posts published before this date will be excluded.
</ParamField>

<ParamField path="end_date" type="date">
  End date for filtering posts by their publish date (YYYY-MM-DD format). Posts published after this date will be excluded.
</ParamField>

**Output Structure**:\
Includes comprehensive data points:

* **Post Details**:
  `id`, `title`, `headline`, `post_text`, `post_text_html`, `date_posted`, `hashtags`, `embedded_links`, `images`, `videos`, `post_type`, `account_type`, and more.

  > For all data points, [click here](https://brightdata.com/cp/data_api/gd_lyy3tktm25m4avu764/company_url?tab=overview).

* **Engagement Metrics**:
  `num_likes`, `num_comments`, `top_visible_comments`.

* **User Details**:
  `user_id`, `use_url`, `user_followers`, `user_posts`, `user_articles`.

* **Related Content**:
  `more_articles_by_user`, `more_relevant_posts`.

This API enables precise discovery of LinkedIn posts based on specific profiles and time ranges, providing detailed post data, engagement metrics, and associated user information for in-depth analysis.

### Discover by Company URL

This API allows users to discover recent LinkedIn posts published by a company, filtered by optional date ranges, using the company URL.

**Input Parameters**:

<ParamField path="URL" type="string" required="true">
  The LinkedIn company profile URL.
</ParamField>

<ParamField path="start_date" type="date">
  Start date for filtering posts by their publish date (YYYY-MM-DD format). Only posts published on or after this date will be collected.
</ParamField>

<ParamField path="end_date" type="date">
  End date for filtering posts by their publish date (YYYY-MM-DD format). Only posts published on or before this date will be collected.
</ParamField>

**Output Structure**:\
Includes comprehensive data points:

* **Post Details**:
  `post_id`, `title`, `post_text`, `date_posted`, `hashtags`, `embedded_links`, `images`, `videos`, `post_type`, `account_type`, and more.

  > For all data points, [click here](https://brightdata.com/cp/data_api/gd_lyy3tktm25m4avu764/company_url?tab=overview).

* **Engagement Metrics**:
  `num_likes`, `num_comments`, `top_visible_comments`.

* **Company Details**:
  `company_id`, `company_name`, `company_url`, `followers`.

* **Related Content**:
  `more_relevant_posts`, `additional_media_links`.

This API provides detailed insights into company posts, allowing businesses and analysts to track updates, engagement, and content trends effectively.

## Job Listings Information API

### Collect by URL

This API allows users to collect detailed information about a LinkedIn job listing by providing the job URL.

**Input Parameters**:

<ParamField path="URL" type="string" required="true">
  The LinkedIn job listing URL.
</ParamField>

**Output Structure**:\
Includes comprehensive data points:

* **Job Details**:
  `job_posting_id`, `job_title`, `job_summary`, `job_seniority_level`, `job_function`, `job_employment_type`, `job_industries`, `job_base_pay_range`, `base_salary`, `job_description_formatted`, and more.

  > For all data points, [click here](https://brightdata.com/cp/data_api/gd_lpfll7v5hcqtkxl6l?tab=overview).

* **Company Details**:
  `company_name`, `company_id`, `company_url`, `company_logo`.

* **Job Metadata**:
  `job_location`, `job_posted_time`, `job_posted_date`, `job_num_applicants`, `discovery_input`, `apply_link`, `country_code`, `title_id`.

* **Job Poster Information**:
  `job_poster`.

This API provides a comprehensive overview of LinkedIn job listings, including job details, company information, applicant statistics, and metadata for enhanced job analysis and application tracking.

### Discover by Keyword

This API allows users to discover LinkedIn job postings based on keyword search, location, and other filters like job type, experience level, and more.

**Input Parameters**:

<ParamField path="location" type="string" required="true">
  The specific location where the jobs are located.
</ParamField>

<ParamField path="keyword" type="string" required="true">
  A keyword or job title for searching jobs (e.g., "Product Manager"). Use quotation marks for exact matches.
</ParamField>

<ParamField path="country" type="string">
  The country code in 2-letter format (e.g., `US`, `FR`).
</ParamField>

<ParamField path="time_range" type="string">
  The time range of the job postings (e.g., `past_week`, `past_month`).
</ParamField>

<ParamField path="job_type" type="string">
  The type of job (e.g., "full-time", "part-time").
</ParamField>

<ParamField path="experience_level" type="string">
  The required experience level for the job (e.g., "entry-level", "mid-senior").
</ParamField>

<ParamField path="remote" type="string">
  Whether the job is remote (e.g., "yes" or "no").
</ParamField>

<ParamField path="company" type="string">
  The company name to filter jobs by.
</ParamField>

<ParamField path="selective_search" type="boolean">
  When set to true, excludes job titles that do not contain the specified keywords.
</ParamField>

**Output Structure**:\
Includes comprehensive data points:

* **Job Details**:
  `job_posting_id`, `job_title`, `job_summary`, `job_seniority_level`, `job_function`, `job_employment_type`, `job_industries`, `job_base_pay_range`, `job_description_formatted`, `base_salary`, and more.

  > For all data points, [click here](https://brightdata.com/cp/data_api/gd_lpfll7v5hcqtkxl6l/keyword?tab=overview).

* **Company Details**:
  `company_name`, `company_id`, `company_url`, `company_logo`.

* **Job Metadata**:
  `job_location`, `job_posted_time`, `job_posted_date`, `job_num_applicants`, `job_poster`, `apply_link`, `country_code`, `title_id`.

* **Application Details**:
  `job_poster`, `application_availability`, `discovery_input`.

This API allows users to discover and filter jobs on LinkedIn based on specific keywords, location, job type, and other criteria, offering detailed job listings and company information for further analysis.

### Discover by URL

This API allows users to discover job listings from a direct LinkedIn job search URL, providing job details, company information, and job metadata based on the specific URL query.

**Input Parameters**:

<ParamField path="URL" type="string" required="true">
  A direct LinkedIn search URL for jobs (e.g., by company or job title).
</ParamField>

<ParamField path="selective_search" type="boolean">
  When set to `true`, the search will exclude job titles that do not match the specified keywords or criteria.
</ParamField>

**Output Structure**:\
Includes comprehensive data points:

* **Job Details**:
  `job_posting_id`, `job_title`, `job_summary`, `job_seniority_level`, `job_function`, `job_employment_type`, `job_industries`, `job_base_pay_range`, `job_description_formatted`, `base_salary`, and more.

  > For all data points, [click here](https://brightdata.com/cp/data_api/gd_lpfll7v5hcqtkxl6l/url?tab=overview).

* **Company Details**:
  `company_name`, `company_id`, `company_url`, `company_logo`.

* **Job Metadata**:
  `job_location`, `job_posted_time`, `job_posted_date`, `job_num_applicants`, `job_poster`, `apply_link`, `country_code`, `title_id`.

* **Application Details**:
  `job_poster`, `application_availability`, `discovery_input`.

This API allows users to retrieve detailed job listings from a LinkedIn search URL, offering insights into job opportunities, company details, and more, enabling efficient job discovery and application tracking.

## Companies Information API

### Collect by URL

This API allows users to collect detailed information about a LinkedIn company profile by providing the company URL.

**Input Parameters**:

<ParamField path="URL" type="string" required="true">
  The LinkedIn company profile URL.
</ParamField>

**Output Structure**:\
Includes comprehensive data points:

* **Company Details**:
  `id`, `name`, `about`, `slogan`, `description`, `specialties`, `organization_type`, `company_size`, `industries`, `founded`, and more.

  > For all data points, [click here](https://brightdata.com/cp/data_api/gd_l1vikfnt1wgvvqz95w?tab=overview).

* **Business Information**:
  `country_code`, `country_codes_array`, `locations`, `formatted_locations`, `headquarters`, `stock_info`, `funding`, `investors`, `crunchbase_url`, `get_directions_url`.

* **Engagement and Network**:
  `followers`, `employees`, `employees_in_linkedin`, `alumni`, `alumni_information`, `affiliated`, `similar`.

* **Media and Metadata**:
  `logo`, `image`, `url`, `updates`, `timestamp`.

This API provides a comprehensive overview of LinkedIn company profiles, including business details, locations, alumni network, funding information, and media assets.




# Filter Dataset (JSON or File Uploads)

> Create a dataset snapshot based on a provided filter

## OpenAPI

````yaml filter-csv-json POST /datasets/filter
paths:
  path: /datasets/filter
  method: post
  servers:
    - url: https://api.brightdata.com
  request:
    security:
      - title: bearerAuth
        parameters:
          query: {}
          header:
            Authorization:
              type: http
              scheme: bearer
              description: >-
                Use your Bright Data API Key as a Bearer token in the
                Authorization header. 

                 Get API Key from: https://brightdata.com/cp/setting/users. 

                 **Example**:
                ```Authorization: Bearer
                b5648e1096c6442f60a6c4bbbe73f8d2234d3d8324554bd6a7ec8f3f251f07df```
          cookie: {}
    parameters:
      path: {}
      query:
        dataset_id:
          schema:
            - type: string
              required: true
              description: >-
                ID of the dataset to filter (required in multipart/form-data
                mode)
              example: gd_l1viktl72bvl7bjuj0
        records_limit:
          schema:
            - type: integer
              required: false
              description: Limit the number of records to be included in the snapshot
              example: 1000
      header: {}
      cookie: {}
    body:
      multipart/form-data:
        schemaArray:
          - type: object
            properties:
              filter:
                allOf:
                  - $ref: '#/components/schemas/DatasetFilter'
            required: true
            refIdentifier: '#/components/schemas/FilterDatasetBody'
            requiredProperties:
              - filter
        examples:
          example:
            value:
              filter:
                name: name
                operator: '='
                value: John
  response:
    '200':
      application/json:
        schemaArray:
          - type: object
            properties:
              snapshot_id:
                allOf:
                  - type: string
                    description: ID of the snapshot
        examples:
          example:
            value:
              snapshot_id: <string>
        description: Job of creating the snapshot successfully started
    '400':
      application/json:
        schemaArray:
          - type: object
            properties:
              validation_errors:
                allOf:
                  - type: array
                    items:
                      type: string
            refIdentifier: '#/components/schemas/ValidationErrorBody'
        examples:
          example:
            value:
              validation_errors:
                - '"filter.filters[0].invalid_prop" is not allowed'
                - '"records_limit" must be a positive number'
        description: Bad request
    '402':
      application/json:
        schemaArray:
          - type: object
            properties:
              error:
                allOf:
                  - &ref_0
                    type: string
            refIdentifier: '#/components/schemas/ErrorBody'
        examples:
          example:
            value:
              error: >-
                Your current balance is insufficient to process this data
                collection request. Please add funds to your account or adjust
                your request to continue. ($1 is missing)
        description: Not enough funds to create the snapshot
    '422':
      application/json:
        schemaArray:
          - type: object
            properties:
              error:
                allOf:
                  - *ref_0
            refIdentifier: '#/components/schemas/ErrorBody'
        examples:
          example:
            value:
              error: Provided filter did not match any records
        description: Provided filter did not match any records
    '429':
      application/json:
        schemaArray:
          - type: object
            properties:
              error:
                allOf:
                  - *ref_0
            refIdentifier: '#/components/schemas/ErrorBody'
        examples:
          example:
            value:
              error: Maximum limit of 100 jobs per dataset has been exceeded
        description: Too many parallel jobs
  deprecated: false
  type: path
components:
  schemas:
    DatasetFilter:
      anyOf:
        - $ref: '#/components/schemas/DatasetFilterItem'
          title: Single field filter
        - $ref: '#/components/schemas/DatasetFilterGroup'
          title: Filters group
        - $ref: '#/components/schemas/DatasetFilterItemNoVal'
          title: Single field filter w/out value
    DatasetFilterGroup:
      type: object
      required:
        - operator
        - filters
      additionalProperties: false
      properties:
        operator:
          type: string
          enum:
            - and
            - or
        combine_nested_fields:
          type: boolean
          description: >-
            For arrays of objects: if true, all filters must match within a
            single object
        filters:
          type: array
          items:
            $ref: '#/components/schemas/DatasetFilter'
      example:
        operator: and
        filters:
          - name: name
            operator: '='
            value: John
          - name: age
            operator: '>'
            value: '30'
    DatasetFilterItem:
      type: object
      required:
        - name
        - operator
        - value
      additionalProperties: false
      properties:
        name:
          type: string
          description: Field name to filter by
        operator:
          type: string
          enum:
            - '='
            - '!='
            - '>'
            - <
            - '>='
            - <=
            - in
            - not_in
            - includes
            - not_includes
            - array_includes
            - not_array_includes
        value:
          description: Value to filter by
          oneOf:
            - type: string
            - type: number
            - type: boolean
            - type: object
            - type: array
              items:
                oneOf:
                  - type: string
                  - type: number
                  - type: boolean
      example:
        name: name
        operator: '='
        value: John
    DatasetFilterItemNoVal:
      type: object
      required:
        - name
        - operator
      additionalProperties: false
      properties:
        name:
          type: string
          description: Field name to filter by
        operator:
          type: string
          enum:
            - is_null
            - is_not_null
      example:
        name: reviews_count
        operator: is_not_null

````


print('If you get "ImportError: No module named \'requests\'", install requests: sudo pip install requests');
import requests
def filter_dataset():
    url = "https://api.brightdata.com/datasets/filter"
    headers = {
        "Authorization": "Bearer API_TOKEN",
        "Content-Type": "application/json"
    }
    payload = {
        "dataset_id": "gd_l1viktl72bvl7bjuj0",
        "filter": {}
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.ok:
        print("Request succeeded:", response.json())
    else:
        print("Request failed:", response.text)
filter_dataset()