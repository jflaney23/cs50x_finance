# cs50x_finance
CS50x's finance project. 

This is a web app via which you can manage portfolios of stocks. Not only will this tool allow you to check real stocks’ actual prices and portfolios’ values, it will also let you buy (okay, “buy”) and sell (okay, “sell”) stocks by querying IEX for stocks’ prices.

It uses SQLite3 database to store all changes in stocks and user's. The layout of the database looks like this:

+-----------+
|   users   |
+-----------+
| id        |----+
| username  |    |
| hash      |    |
| cash      |    |
+-----------+    |
                 |
+-----------+    |    +--------------+
| portfolio |    |    | transactions |
+-----------+    |    +--------------+
| user_id   |----+----| user_id      |
| symbol    |         | id           |
| shares    |         | transaction_type |
+-----------+         | symbol       |
                      | shares       |
                      | price        |
                      | timestamp    |
                      +--------------+



