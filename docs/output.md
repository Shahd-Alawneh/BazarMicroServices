# Program Output Examples

## 1. Search Operation

Request:
GET /search/distributed systems

Output:
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

---

## 2. Info Operation

Request:
GET /info/2

Output:
{
"title": "RPCs for Noobs",
"quantity": 5,
"price": 40
}

---

## 3. Purchase Operation (Success)

Request:
POST /purchase/2

Output:
{
"message": "purchase successful"
}

Console Log:
bought book RPCs for Noobs

---

## 4. Purchase Operation (Failure)

Request:
POST /purchase/2

Output:
{
"message": "out of stock"
}

---

## 5. Notes

* All responses are returned in JSON format
* System logs important operations in the console
* Data is updated in CSV files after each purchase
