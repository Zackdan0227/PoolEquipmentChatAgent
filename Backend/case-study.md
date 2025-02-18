#  Pool Equipment API Documentation

## Overview
This document provides documentation for the Pool Equipment API wrapper. All endpoints return data in JSON format and include the fixed store configuration in their responses:
- Customer ID: HPTA
- Branch Code: BELHARR
- Ship To Sequence: 1

## Base URL
```
https://candidate-onsite-study-srs-712206638513.us-central1.run.app
```

## Product Operations

### 1. Search Products (Klevu)
Search for products using the Klevu search engine.

**Endpoint:** `GET /api/search`

**Parameters:**
- `term` (required): Search term
- `page_size` (optional): Results per page (default: 5)
- `page` (optional): Page number (default: '1')

**Example Request:**
```bash
curl "https://candidate-onsite-study-srs-712206638513.us-central1.run.app/api/search?term=pool%20pump&page_size=5&page=1"
```

**Success Response:**
```json
{
    "store": {
        "customerId": "HPTA",
        "branchCode": "BELHARR",
        "shipToSequenceNumber": "1"
    },
    "total_results": 25,
    "items": [
        {
            "id": "12345",
            "part_number": "LZA406103A"
        }
    ]
}
```

### 2. Search Products (Azure)
Search for products using Azure Cognitive Search with vector enhancement.

**Endpoint:** `GET /api/products/search`

**Parameters:**
- `query` (required): Search query
- `limit` (optional): Maximum number of results (default: 3)

**Example Request:**
```bash
curl "https://candidate-onsite-study-srs-712206638513.us-central1.run.app/api/products/search?query=pool%20pump&limit=3"
```

**Success Response:**
```json
{
    "store": {
        "customerId": "HPTA",
        "branchCode": "BELHARR",
        "shipToSequenceNumber": "1"
    },
    "total_results": 3,
    "items": [
        {
            "product_name": "Super Pool Pump",
            "description": "High-performance pool pump",
            "brand": "SuperPump",
            "part_number": "LZA406103A",
            "manufacturer_id": "SP123",
            "heritage_link": "https://heritagepoolplus.com/product/LZA406103A",
            "image_url": "https://heritagepoolplus.com/images/LZA406103A.jpg",
            "relevance_score": 0.95
        }
    ]
}
```

### 3. Get Product Details
Get detailed information about a specific product.

**Endpoint:** `GET /api/products/{part_number}`

**Example Request:**
```bash
curl "https://candidate-onsite-study-srs-712206638513.us-central1.run.app/api/products/LZA406103A"
```

**Success Response:**
```json
{
    "store": {
        "customerId": "HPTA",
        "branchCode": "BELHARR",
        "shipToSequenceNumber": "1"
    },
    "product_name": "Super Pool Pump",
    "description": "High-performance pool pump",
    "brand": "SuperPump",
    "part_number": "LZA406103A",
    "manufacturer_id": "SP123",
    "heritage_link": "https://heritagepoolplus.com/product/LZA406103A",
    "image_url": "https://heritagepoolplus.com/images/LZA406103A.jpg"
}
```

### 4. Get Pricing
Get pricing information for multiple items.

**Endpoint:** `POST /api/pricing`

**Request Body:**
```json
{
    "items": [
        {
            "item_code": "LZA406103A",
            "unit": "EA"
        }
    ]
}
```

**Example Request:**
```bash
curl -X POST "https://candidate-onsite-study-srs-712206638513.us-central1.run.app/api/pricing" \
-H "Content-Type: application/json" \
-d '{
    "items": [
        {
            "item_code": "LZA406103A",
            "unit": "EA"
        }
    ]
}'
```

**Success Response:**
```json
{
    "store": {
        "customerId": "HPTA",
        "branchCode": "BELHARR",
        "shipToSequenceNumber": "1"
    },
    "items": [
        {
            "item_code": "LZA406103A",
            "description": "Super Pool Pump",
            "price": 599.99,
            "available_quantity": 10,
            "in_stock": true,
            "unit": "EA"
        }
    ]
}
```

## Store Locations

### 1. Search Stores
Search for stores near a location using coordinates.

**Endpoint:** `GET /api/stores/search`

**Parameters:**
- `latitude` (required): Latitude coordinate
- `longitude` (required): Longitude coordinate
- `radius` (optional): Search radius in miles (default: 50)
- `page_size` (optional): Results per page (default: 10)
- `page` (optional): Page number (default: 1)

**Example Request:**
```bash
curl "https://candidate-onsite-study-srs-712206638513.us-central1.run.app/api/stores/search?latitude=33.7490&longitude=-84.3880&radius=50"
```

**Success Response:**
```json
{
    "store": {
        "customerId": "HPTA",
        "branchCode": "BELHARR",
        "shipToSequenceNumber": "1"
    },
    "total_results": 1,
    "page_info": {
        "current_page": 1,
        "page_size": 10,
        "total_pages": 1
    },
    "stores": [
        {
            "id": 726,
            "name": "POOL BUILDERS SUPPLY NORCROSS",
            "location": {
                "latitude": 33.92,
                "longitude": -84.22,
                "distance": 15.27
            },
            "address": {
                "street": "6480 BEST FRIEND ROAD",
                "city": "NORCROSS",
                "state": "GA",
                "zip": "30071"
            },
            "contact": {
                "phone": "770-441-3600",
                "email": "ORDERSNORCROSS@POOLBUILDERSSUPPLY.COM",
                "website": null
            },
            "hours": {
                "monday": {"open": "7:30 AM", "close": "4:30 PM"},
                "tuesday": {"open": "7:30 AM", "close": "4:30 PM"},
                "wednesday": {"open": "7:30 AM", "close": "4:30 PM"},
                "thursday": {"open": "7:30 AM", "close": "4:30 PM"},
                "friday": {"open": "7:30 AM", "close": "4:30 PM"},
                "saturday": {"open": "7:30 AM", "close": "11:00 AM"},
                "sunday": {"open": null, "close": null}
            }
        }
    ]
}
```

### 2. Get Store Details
Get detailed information about a specific store.

**Endpoint:** `GET /api/stores/{store_id}`

**Example Request:**
```bash
curl "https://candidate-onsite-study-srs-712206638513.us-central1.run.app/api/stores/726"
```

**Success Response:**
```json
{
    "store": {
        "customerId": "HPTA",
        "branchCode": "BELHARR",
        "shipToSequenceNumber": "1"
    },
    "id": 726,
    "name": "POOL BUILDERS SUPPLY NORCROSS",
    "location": {
        "latitude": 33.92,
        "longitude": -84.22
    },
    "address": {
        "street": "6480 BEST FRIEND ROAD",
        "city": "NORCROSS",
        "state": "GA",
        "zip": "30071"
    },
    "contact": {
        "phone": "770-441-3600",
        "email": "ORDERSNORCROSS@POOLBUILDERSSUPPLY.COM"
    }
}
```

### 3. Health Check

Check if the API is running.

**Endpoint:** `GET /health`

**Example Request:**
```bash
curl "https://candidate-onsite-study-srs-712206638513.us-central1.run.app/health"
```

**Success Response:**
```json
{
    "status": "healthy"
}
```

## Error Responses

All endpoints return appropriate HTTP status codes:

- `200`: Success
- `400`: Bad Request (invalid parameters or missing required fields)
- `404`: Not Found (resource not found)
- `500`: Internal Server Error

**Error Response Format:**
```json
{
    "detail": "Error message describing what went wrong"
}
```
