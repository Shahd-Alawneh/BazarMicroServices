# Bazar Microservices - Design Document

## 1. Overview

This project implements a simple multi-tier online bookstore called **Bazar.com** using a microservices architecture. The system is divided into three main services:

* Frontend Service
* Catalog Service
* Order Service

Each service runs independently and communicates using HTTP REST APIs.

---

## 2. System Architecture

The system follows a **multi-tier architecture**:

* **Frontend Service**: Handles user requests
* **Catalog Service**: Stores book data (title, price, quantity, topic)
* **Order Service**: Handles purchase requests and logs orders

Communication between services is done via HTTP requests.

---

## 3. Services Description

### 3.1 Frontend Service

Responsible for handling client requests and forwarding them to the appropriate backend service.

Supported operations:

* Search books by topic
* Get book information by ID
* Purchase a book

---

### 3.2 Catalog Service

Responsible for managing the book catalog.

Supported operations:

* Query books by topic
* Query book by ID
* Update book price or quantity

Data is stored in a CSV file (`catalog.csv`) to ensure persistence.

---

### 3.3 Order Service

Responsible for handling purchase operations.

Workflow:

1. Receives purchase request
2. Queries catalog service to check availability
3. If available:

   * Decrements quantity
   * Records order in `orders.csv`
4. If not available:

   * Returns failure message

---

## 4. REST API Design

All services expose REST endpoints and return JSON responses.

Examples:

* GET /search/<topic>
* GET /info/<item_id>
* POST /purchase/<item_id>

---

## 5. Data Storage

* Catalog data stored in: `catalog.csv`
* Orders stored in: `orders.csv`

This ensures persistence without using heavy databases.

---

## 6. Concurrency

The system supports concurrent requests using the Flask web framework, which handles multiple requests efficiently.

---

## 7. Deployment

The system is deployed using **Docker Compose** with three containers:

* frontend container
* catalog container
* order container

Each service runs independently.

---

## 8. Design Decisions

* Used microservices to separate concerns
* Used REST APIs for communication
* Used CSV files for simplicity and lightweight storage
* Used Docker for easy deployment

---

## 9. Limitations

* No authentication system
* No advanced error handling
* No load balancing
* No database scaling

---

## 10. Future Improvements

* Add database (e.g., SQLite)
* Add API Gateway
* Improve logging and monitoring
* Add authentication system
