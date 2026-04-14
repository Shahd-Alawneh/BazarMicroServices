# Bazar Microservices

A simple multi-tier online bookstore built using a microservices architecture.

## Project Overview

This project implements **Bazar.com**, a small online bookstore system using three independent microservices:

* **Frontend Service**: handles client requests
* **Catalog Service**: manages the book catalog
* **Order Service**: processes purchase requests

The services communicate using **HTTP REST APIs** and are deployed using **Docker Compose**.

---

## System Architecture

The system consists of three services:

1. **Frontend**

   * Accepts user requests
   * Forwards search and info requests to the catalog service
   * Forwards purchase requests to the order service

2. **Catalog**

   * Stores books data
   * Supports searching by topic
   * Supports retrieving book details by ID
   * Supports updating price and quantity

3. **Order**

   * Handles purchase requests
   * Checks availability through the catalog service
   * Updates stock after successful purchase
   * Logs orders in a CSV file

---

## Technologies Used

* Python 3
* Flask
* Docker
* Docker Compose
* CSV files for persistent storage

---

## Project Structure

```text
Bazar/
├── Catalog/
│   ├── catalog_service.py
│   ├── catalog.csv
│   └── Dockerfile
├── Order/
│   ├── order_service.py
│   ├── orders.csv
│   └── Dockerfile
├── Frontend/
│   ├── frontend_service.py
│   └── Dockerfile
├── docs/
│   ├── design.md
│   └── output.md
├── docker-compose.yml
└── README.md
```

---

## REST API Endpoints

### Frontend Service

#### Search by topic

```http
GET /search/<topic>
```

Example:

```http
GET /search/distributed systems
```

#### Get book information

```http
GET /info/<item_id>
```

Example:

```http
GET /info/2
```

#### Purchase a book

```http
POST /purchase/<item_id>
```

Example:

```http
POST /purchase/2
```

---

### Catalog Service

#### Search books by topic

```http
GET /search/<topic>
```

#### Get book details by ID

```http
GET /info/<item_id>
```

#### Update a book

```http
POST /update/<item_id>
```

Example request body:

```json
{
  "action": "increment",
  "value": 3
}
```

Supported actions:

* `set_price`
* `decrement`
* `increment`
* `set_quantity`

---

### Order Service

#### Purchase endpoint

```http
POST /purchase/<item_id>
```

The order service:

1. checks if the item exists
2. verifies stock quantity
3. decrements quantity in catalog
4. records the purchase in `orders.csv`

---

## Data Storage

This project uses CSV files for persistent storage:

* `catalog.csv` stores:

  * book ID
  * title
  * topic
  * price
  * quantity

* `orders.csv` stores:

  * purchased book records

This keeps the system simple and lightweight.

---

## How to Run the Project

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd Bazar
```

### 2. Build and start the services

```bash
docker-compose up --build
```

### 3. Access the services

Example local ports:

* Frontend: `http://localhost:5000`
* Catalog: `http://localhost:5001`
* Order: `http://localhost:5002`

---

## Example Requests

### Search for books by topic

```bash
curl http://localhost:5000/search/distributed%20systems
```

### Get information about a book

```bash
curl http://localhost:5000/info/2
```

### Purchase a book

```bash
curl -X POST http://localhost:5000/purchase/2
```

### Update a book in catalog

```bash
curl -X POST http://localhost:5001/update/2 -H "Content-Type: application/json" -d "{\"action\":\"increment\",\"value\":2}"
```

---

## Sample Output

### Search

```json
[
  {
    "id": 1,
    "title": "How to get a good grade in DOS in 40 minutes a day"
  },
  {
    "id": 2,
    "title": "RPCs for Noobs"
  }
]
```

### Info

```json
{
  "title": "RPCs for Noobs",
  "quantity": 5,
  "price": 40
}
```

### Purchase

```json
{
  "message": "purchase successful"
}
```

---

## Notes

* Each service runs independently in its own container
* Services communicate using REST APIs
* Data is stored persistently using CSV files
* Docker Compose is used to run the whole system easily

---

## Future Improvements

* Add better logging
* Add authentication
* Improve validation and error handling
* Replace CSV with SQLite
* Add API gateway

---

## Author

Developed as part of the **Distributed and Operating Systems** .
 
## Contributers
Shahd Alawneh 12116072
Sewar Diab 12116104